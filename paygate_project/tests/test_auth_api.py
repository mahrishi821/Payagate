"""
Tests for authentication API endpoints.
"""
import pytest
import json
from decimal import Decimal
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from paygate.models import Merchant
from .factories import UserFactory, AdminUserFactory, MerchantFactory

User = get_user_model()


def parse_response(response):
    """Helper function to parse Django JsonResponse."""
    return json.loads(response.content)


@pytest.mark.django_db
class TestMerchantRegistrationAPI:
    """Test merchant registration endpoint."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = APIClient()
        self.url = '/paygate/api/v1/auth/register/'

    def test_register_merchant_success(self):
        """Test successful merchant registration."""
        data = {
            'user': {
                'email': 'merchant@example.com',
                'name': 'Test Merchant',
                'password': 'testpass123'
            },
            'webhook_url': 'https://example.com/webhook'
        }

        response = self.client.post(self.url, data, format='json')

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is True
        assert response_data['message'] == 'Merchant registered successfully'
        assert 'access' in response_data['data']
        assert 'api_key' in response_data['data']
        assert response_data['data']['email'] == 'merchant@example.com'
        assert response_data['data']['role'] == 'merchant'

        # Verify user and merchant were created
        assert User.objects.filter(email='merchant@example.com').exists()
        merchant = Merchant.objects.get(user__email='merchant@example.com')
        assert merchant.webhook_url == 'https://example.com/webhook'

    def test_register_merchant_missing_user_data(self):
        """Test registration with missing user data."""
        data = {
            'webhook_url': 'https://example.com/webhook'
        }

        response = self.client.post(self.url, data, format='json')

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is False

    def test_register_merchant_invalid_email(self):
        """Test registration with invalid email."""
        data = {
            'user': {
                'email': 'invalid-email',
                'name': 'Test Merchant',
                'password': 'testpass123'
            }
        }

        response = self.client.post(self.url, data, format='json')

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is False

    def test_register_merchant_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create existing user
        UserFactory(email='existing@example.com')

        data = {
            'user': {
                'email': 'existing@example.com',
                'name': 'Test Merchant',
                'password': 'testpass123'
            }
        }

        response = self.client.post(self.url, data, format='json')

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is False

    def test_register_merchant_sets_refresh_token_cookie(self):
        """Test that registration sets refresh token cookie."""
        data = {
            'user': {
                'email': 'merchant@example.com',
                'name': 'Test Merchant',
                'password': 'testpass123'
            }
        }

        response = self.client.post(self.url, data, format='json')

        assert response.status_code == 200
        assert 'refresh_token' in response.cookies

        cookie = response.cookies['refresh_token']
        assert cookie['httponly'] is True
        assert cookie['samesite'] == 'Strict'

@pytest.mark.django_db
class TestAdminRegistrationAPI:
    def setup_method(self):
        self.client = APIClient()
        self.url = '/paygate/api/v1/auth/register-admin/'
        self.admin_user = AdminUserFactory()
        self.client.force_authenticate(user=self.admin_user)

    def test_register_admin_success(self):
        data = {
            'user': {
                'email': 'newadmin@example.com',
                'name': 'New Admin',
                'password': 'adminpass123'
            }
        }
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is True
        assert 'access' in response_data['data']
        assert response_data['data']['role'] == 'admin'
        assert User.objects.filter(email='newadmin@example.com', is_staff=True).exists()
        assert 'refresh_token' in response.cookies

@pytest.mark.django_db
class TestLoginAPI:
    """Test login endpoint."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = APIClient()
        self.url = '/paygate/api/v1/auth/token/'

        # Create test users
        self.merchant_user = UserFactory(email='merchant@example.com')
        self.merchant_user.set_password('testpass123')
        self.merchant_user.save()
        self.merchant = MerchantFactory(user=self.merchant_user)

        self.admin_user = AdminUserFactory(email='admin@example.com')
        self.admin_user.set_password('adminpass123')
        self.admin_user.save()

    def test_login_merchant_success(self):
        """Test successful merchant login."""
        data = {
            'email': 'merchant@example.com',
            'password': 'testpass123'
        }

        response = self.client.post(self.url, data, format='json')

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is True
        assert response_data['message'] == 'Login successful'
        assert 'access' in response_data['data']
        assert response_data['data']['email'] == 'merchant@example.com'
        assert response_data['data']['role'] == 'merchant'
        assert 'api_key' in response_data['data']

    def test_login_admin_success(self):
        """Test successful admin login."""
        data = {
            'email': 'admin@example.com',
            'password': 'adminpass123'
        }

        response = self.client.post(self.url, data, format='json')

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is True
        assert response_data['data']['role'] == 'admin'
        assert response_data['data']['api_key'] is None

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        data = {
            'email': 'merchant@example.com',
            'password': 'wrongpassword'
        }

        response = self.client.post(self.url, data, format='json')

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is False
        assert response_data['exception']['code'] == 1001

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }

        response = self.client.post(self.url, data, format='json')

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is False

    def test_login_sets_refresh_token_cookie(self):
        """Test that login sets refresh token cookie."""
        data = {
            'email': 'merchant@example.com',
            'password': 'testpass123'
        }

        response = self.client.post(self.url, data, format='json')

        assert response.status_code == 200
        assert 'refresh_token' in response.cookies

        cookie = response.cookies['refresh_token']
        assert cookie['httponly'] is True
        assert cookie['samesite'] == 'None'


@pytest.mark.django_db
class TestTokenRefreshAPI:
    """Test token refresh endpoint."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = APIClient()
        self.url = '/paygate/api/v1/auth/refresh/'
        self.user = UserFactory()
        self.refresh_token = RefreshToken.for_user(self.user)

    def test_refresh_token_success(self):
        """Test successful token refresh."""
        # Set refresh token cookie
        self.client.cookies['refresh_token'] = str(self.refresh_token)

        response = self.client.post(self.url)

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is True
        assert 'access' in response_data['data']

    def test_refresh_token_missing_cookie(self):
        """Test token refresh without refresh token cookie."""
        response = self.client.post(self.url)

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is False
        assert 'No refresh token provided' in response_data['exception']['message']

    def test_refresh_token_invalid_token(self):
        """Test token refresh with invalid token."""
        self.client.cookies['refresh_token'] = 'invalid-token'

        response = self.client.post(self.url)

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is False


@pytest.mark.django_db
class TestLogoutAPI:
    """Test logout endpoint."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = APIClient()
        self.url = '/paygate/api/v1/auth/logout/'
        self.user = UserFactory()
        self.refresh_token = RefreshToken.for_user(self.user)

    def test_logout_success(self):
        """Test successful logout."""
        self.client.force_authenticate(user=self.user)
        self.client.cookies['refresh_token'] = str(self.refresh_token)

        response = self.client.post(self.url)

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is True
        assert response_data['message'] == 'Logout successful'

        # Check that refresh_token cookie is deleted
        assert 'refresh_token' in response.cookies
        assert response.cookies['refresh_token'].value == ''

    def test_logout_requires_authentication(self):
        """Test that logout requires authentication."""
        self.client.cookies['refresh_token'] = str(self.refresh_token)

        response = self.client.post(self.url)

        assert response.status_code == 401

    def test_logout_missing_refresh_token(self):
        """Test logout without refresh token cookie."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.url)

        assert response.status_code == 200
        response_data = parse_response(response)
        assert response_data['success'] is False
        assert response_data['exception']['code'] == 1040


@pytest.mark.django_db
class TestAuthenticationFlow:
    """Test complete authentication flow scenarios."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = APIClient()

    def test_complete_merchant_auth_flow(self):
        """Test complete merchant registration -> login -> refresh -> logout flow."""
        # 1. Register merchant
        register_data = {
            'user': {
                'email': 'flowtest@example.com',
                'name': 'Flow Test Merchant',
                'password': 'flowpass123'
            },
            'webhook_url': 'https://example.com/webhook'
        }

        register_response = self.client.post(
            '/paygate/api/v1/auth/register/',
            register_data,
            format='json'
        )
        assert register_response.status_code == 200

        # 2. Login with registered credentials
        login_data = {
            'email': 'flowtest@example.com',
            'password': 'flowpass123'
        }

        login_response = self.client.post(
            '/paygate/api/v1/auth/token/',
            login_data,
            format='json'
        )
        assert login_response.status_code == 200

        # Extract access token
        login_data = parse_response(login_response)
        access_token = login_data['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # 3. Use refresh token
        refresh_response = self.client.post('/paygate/api/v1/auth/refresh/')
        assert refresh_response.status_code == 200

        # 4. Logout
        logout_response = self.client.post('/paygate/api/v1/auth/logout/')
        assert logout_response.status_code == 200

    def test_authentication_required_endpoints(self):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            '/paygate/api/v1/auth/logout/',
            '/paygate/api/v1/orders/',
            '/paygate/api/v1/payments/',
            '/paygate/api/v1/refunds/',
        ]

        for endpoint in protected_endpoints:
            response = self.client.post(endpoint)
            assert response.status_code == 401