"""
Tests for payment API endpoints.
"""
import pytest
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from paygate.models import Merchant, Order, Payment, WebhookLog
from .factories import UserFactory, AdminUserFactory, MerchantFactory, OrderFactory, PaymentFactory

User = get_user_model()


def parse_response(response):
    """Helper function to parse Django JsonResponse."""
    return json.loads(response.content)


@pytest.mark.django_db
class TestOrderCreateAPI:
    """Test order creation endpoint."""

    def setup_method(self):
        """Set up test client and authenticated merchant for each test."""
        self.client = APIClient()
        self.url = '/paygate/api/v1/orders/'
        
        # Create authenticated merchant
        self.merchant_user = UserFactory()
        self.merchant = MerchantFactory(user=self.merchant_user)
        self.client.force_authenticate(user=self.merchant_user)

    def test_create_order_success(self):
        """Test successful order creation."""
        data = {
            'amount': '100.50',
            'currency': 'INR'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        response_data = parse_response(response)
        assert response_data['success'] is True
        assert response_data['message'] == 'Order created successfully'
        
        order_data = response_data['data']
        assert 'order_id' in order_data
        assert order_data['amount'] == '100.50'
        assert order_data['currency'] == 'INR'
        assert order_data['status'] == 'created'
        
        # Verify order was created in database
        order = Order.objects.get(order_id=order_data['order_id'])
        assert order.merchant == self.merchant
        assert order.amount == Decimal('100.50')

    def test_create_order_default_currency(self):
        """Test order creation with default currency."""
        data = {
            'amount': '50.00'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert parse_response(response)['data']['currency'] == 'INR'

    def test_create_order_invalid_amount(self):
        """Test order creation with invalid amount."""
        invalid_amounts = ['-10.00', '0', 'invalid', '']
        
        for amount in invalid_amounts:
            data = {'amount': amount}
            response = self.client.post(self.url, data, format='json')
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert parse_response(response)['success'] is False
            assert parse_response(response)['exception']['code'] == 1009

    def test_create_order_missing_amount(self):
        """Test order creation without amount."""
        data = {'currency': 'INR'}
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert parse_response(response)['success'] is False

    def test_create_order_requires_authentication(self):
        """Test that order creation requires authentication."""
        self.client.force_authenticate(user=None)
        
        data = {'amount': '100.00'}
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_order_requires_merchant(self):
        """Test that only merchants can create orders."""
        # Create regular user (not a merchant)
        regular_user = UserFactory()
        self.client.force_authenticate(user=regular_user)
        
        data = {'amount': '100.00'}
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert parse_response(response)['exception']['code'] == 1008


@pytest.mark.django_db
class TestPaymentProcessAPI:
    """Test payment processing endpoint."""

    def setup_method(self):
        """Set up test client and test data for each test."""
        self.client = APIClient()
        self.url = '/paygate/api/v1/payments/'
        
        # Create authenticated merchant with order
        self.merchant_user = UserFactory()
        self.merchant = MerchantFactory(user=self.merchant_user)
        self.order = OrderFactory(merchant=self.merchant, amount=Decimal('100.00'))
        self.client.force_authenticate(user=self.merchant_user)

    @patch('paygate.services.PaymentProcessor.process_payment')
    @patch('paygate.services.WebhookHandler.send_webhook')
    def test_process_payment_success(self, mock_webhook, mock_process):
        """Test successful payment processing."""
        # Mock successful payment
        mock_payment = PaymentFactory(order=self.order, status='authorized')
        mock_process.return_value = (mock_payment, True)
        mock_webhook.return_value = True
        
        data = {
            'order_id': str(self.order.order_id),
            'card_details': {
                'card_number': '4111111111111111',
                'expiry': '12/25',
                'cvv': '123'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert parse_response(response)['success'] is True
        assert parse_response(response)['message'] == 'Payment processed successfully'
        
        # Verify mocks were called
        mock_process.assert_called_once_with(self.order, data['card_details'])
        mock_webhook.assert_called_once_with(mock_payment, self.merchant)

    @patch('paygate.services.PaymentProcessor.process_payment')
    def test_process_payment_failure(self, mock_process):
        """Test failed payment processing."""
        # Mock failed payment
        mock_payment = PaymentFactory(order=self.order, status='failed')
        mock_process.return_value = (mock_payment, False)
        
        data = {
            'order_id': str(self.order.order_id),
            'card_details': {
                'card_number': '4111111111111111',
                'expiry': '12/25',
                'cvv': '123'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert parse_response(response)['data']['status'] == 'failed'

    @patch('paygate.services.PaymentProcessor.process_payment')
    def test_process_payment_invalid_card(self, mock_process):
        """Test payment processing with invalid card details."""
        # Mock invalid card response
        mock_process.return_value = (None, False)
        
        data = {
            'order_id': str(self.order.order_id),
            'card_details': {
                'card_number': '123',  # Invalid card number
                'expiry': '12/25',
                'cvv': '123'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert parse_response(response)['exception']['code'] == 1011

    def test_process_payment_nonexistent_order(self):
        """Test payment processing with nonexistent order."""
        data = {
            'order_id': 'nonexistent-order-id',
            'card_details': {
                'card_number': '4111111111111111',
                'expiry': '12/25',
                'cvv': '123'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert parse_response(response)['exception']['code'] == 1012

    def test_process_payment_unauthorized_order(self):
        """Test payment processing for order belonging to different merchant."""
        # Create order for different merchant
        other_merchant = MerchantFactory()
        other_order = OrderFactory(merchant=other_merchant)
        
        data = {
            'order_id': str(other_order.order_id),
            'card_details': {
                'card_number': '4111111111111111',
                'expiry': '12/25',
                'cvv': '123'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert parse_response(response)['exception']['code'] == 1012

    def test_process_payment_missing_order_id(self):
        """Test payment processing without order ID."""
        data = {
            'card_details': {
                'card_number': '4111111111111111',
                'expiry': '12/25',
                'cvv': '123'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_process_payment_requires_merchant(self):
        """Test that only merchants can process payments."""
        regular_user = UserFactory()
        self.client.force_authenticate(user=regular_user)
        
        data = {
            'order_id': str(self.order.order_id),
            'card_details': {
                'card_number': '4111111111111111',
                'expiry': '12/25',
                'cvv': '123'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert parse_response(response)['exception']['code'] == 1010


@pytest.mark.django_db
class TestRefundProcessAPI:
    """Test refund processing endpoint."""

    def setup_method(self):
        """Set up test client and test data for each test."""
        self.client = APIClient()
        self.url = '/paygate/api/v1/refunds/'
        
        # Create authenticated merchant with payment
        self.merchant_user = UserFactory()
        self.merchant = MerchantFactory(user=self.merchant_user)
        self.order = OrderFactory(merchant=self.merchant)
        self.payment = PaymentFactory(order=self.order, status='authorized')
        self.client.force_authenticate(user=self.merchant_user)

    @patch('paygate.services.PaymentProcessor.process_refund')
    @patch('paygate.services.WebhookHandler.send_webhook')
    def test_process_refund_success(self, mock_webhook, mock_refund):
        """Test successful refund processing."""
        mock_refund.return_value = True
        mock_webhook.return_value = True
        
        data = {
            'payment_id': str(self.payment.payment_id)
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert parse_response(response)['success'] is True
        assert parse_response(response)['message'] == 'Refund processed successfully'
        assert parse_response(response)['data']['status'] == 'refunded'
        
        mock_refund.assert_called_once_with(self.payment)
        mock_webhook.assert_called_once_with(self.payment, self.merchant)

    @patch('paygate.services.PaymentProcessor.process_refund')
    def test_process_refund_failure(self, mock_refund):
        """Test failed refund processing."""
        mock_refund.return_value = False
        
        data = {
            'payment_id': str(self.payment.payment_id)
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert parse_response(response)['exception']['code'] == 1014

    def test_process_refund_nonexistent_payment(self):
        """Test refund processing with nonexistent payment."""
        data = {
            'payment_id': 'nonexistent-payment-id'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert parse_response(response)['exception']['code'] == 1015

    def test_process_refund_unauthorized_payment(self):
        """Test refund processing for payment belonging to different merchant."""
        other_merchant = MerchantFactory()
        other_order = OrderFactory(merchant=other_merchant)
        other_payment = PaymentFactory(order=other_order)
        
        data = {
            'payment_id': str(other_payment.payment_id)
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert parse_response(response)['exception']['code'] == 1015

    def test_process_refund_requires_merchant(self):
        """Test that only merchants can process refunds."""
        regular_user = UserFactory()
        self.client.force_authenticate(user=regular_user)
        
        data = {
            'payment_id': str(self.payment.payment_id)
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert parse_response(response)['exception']['code'] == 1013


@pytest.mark.django_db
class TestAdminStatsAPI:
    """Test admin statistics endpoint."""

    def setup_method(self):
        """Set up test client and test data for each test."""
        self.client = APIClient()
        self.url = '/paygate/api/v1/admin/stats/'
        
        # Create admin user
        self.admin_user = AdminUserFactory()
        self.client.force_authenticate(user=self.admin_user)
        
        # Create test data
        self.merchant = MerchantFactory()
        self.order1 = OrderFactory(merchant=self.merchant)
        self.order2 = OrderFactory(merchant=self.merchant)
        
        self.payment1 = PaymentFactory(order=self.order1, status='authorized')
        self.payment2 = PaymentFactory(order=self.order2, status='failed')
        self.payment3 = PaymentFactory(order=self.order1, status='refunded')

    def test_get_overall_stats(self):
        """Test getting overall admin statistics."""
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert parse_response(response)['success'] is True
        
        stats = parse_response(response)['data']
        assert 'total_merchants' in stats
        assert 'total_orders' in stats
        assert 'total_successful_payments' in stats
        assert 'total_successful_refunds' in stats
        assert 'total_canceled_payments' in stats
        
        # Verify counts match test data
        assert stats['total_merchants'] >= 1
        assert stats['total_orders'] >= 2
        assert stats['total_successful_payments'] >= 1
        assert stats['total_successful_refunds'] >= 1
        assert stats['total_canceled_payments'] >= 1

    def test_get_merchant_specific_stats(self):
        """Test getting statistics for specific merchant."""
        response = self.client.get(self.url, {'merchant_id': self.merchant.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert parse_response(response)['success'] is True
        
        stats = parse_response(response)['data']
        assert 'user__email' in stats
        assert stats['user__email'] == self.merchant.user.email
        assert stats['order_count'] == 2
        assert stats['successful_payments'] == 1
        assert stats['successful_refunds'] == 1
        assert stats['canceled_payments'] == 1

    def test_get_stats_invalid_merchant_id(self):
        """Test getting statistics with invalid merchant ID."""
        response = self.client.get(self.url, {'merchant_id': 999999})
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert parse_response(response)['exception']['code'] == 1019

    def test_get_stats_requires_admin(self):
        """Test that only admins can access statistics."""
        regular_user = UserFactory()
        self.client.force_authenticate(user=regular_user)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_stats_requires_authentication(self):
        """Test that statistics endpoint requires authentication."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPaymentFlowIntegration:
    """Test complete payment flow integration."""

    def setup_method(self):
        """Set up test client and authenticated merchant."""
        self.client = APIClient()
        
        self.merchant_user = UserFactory()
        self.merchant = MerchantFactory(
            user=self.merchant_user,
            webhook_url='https://example.com/webhook'
        )
        self.client.force_authenticate(user=self.merchant_user)

    @patch('paygate.services.PaymentProcessor.process_payment')
    @patch('paygate.services.PaymentProcessor.process_refund')
    @patch('paygate.services.WebhookHandler.send_webhook')
    def test_complete_payment_flow(self, mock_webhook, mock_refund, mock_process):
        """Test complete payment flow: create order -> process payment -> refund."""
        # 1. Create order
        order_data = {
            'amount': '150.75',
            'currency': 'INR'
        }
        
        order_response = self.client.post('/paygate/api/v1/orders/', order_data, format='json')
        assert order_response.status_code == status.HTTP_201_CREATED
        
        order_id = parse_response(order_response)['data']['order_id']
        
        # 2. Process payment - Create real payment for the real order
        real_order = Order.objects.get(order_id=order_id)
        mock_payment = PaymentFactory(order=real_order)
        mock_process.return_value = (mock_payment, True)
        mock_webhook.return_value = True
        
        payment_data = {
            'order_id': order_id,
            'card_details': {
                'card_number': '4111111111111111',
                'expiry': '12/25',
                'cvv': '123'
            }
        }
        
        payment_response = self.client.post('/paygate/api/v1/payments/', payment_data, format='json')
        assert payment_response.status_code == status.HTTP_201_CREATED
        
        payment_id = parse_response(payment_response)['data']['payment_id']
        
        # 3. Process refund
        mock_refund.return_value = True
        
        refund_data = {
            'payment_id': payment_id
        }
        
        refund_response = self.client.post('/paygate/api/v1/refunds/', refund_data, format='json')
        assert refund_response.status_code == status.HTTP_200_OK
        
        # Verify all services were called appropriately
        assert mock_process.called
        assert mock_refund.called
        assert mock_webhook.call_count == 2  # Once for payment, once for refund