"""
Tests for paygate models.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone

from paygate.models import Merchant, Order, Payment, WebhookLog
from .factories import UserFactory, AdminUserFactory, MerchantFactory, OrderFactory, PaymentFactory, WebhookLogFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test cases for User model."""

    def test_create_user(self):
        """Test creating a user."""
        user = UserFactory()
        assert user.email
        assert user.name
        assert user.is_active is True
        assert user.is_staff is False
        assert user.deleted is False

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = AdminUserFactory()
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_user_email_unique(self):
        """Test that user emails must be unique."""
        user1 = UserFactory(email="test@example.com")
        
        with pytest.raises(IntegrityError):
            UserFactory(email="test@example.com")

    def test_user_str_method(self):
        """Test user string representation."""
        user = UserFactory(email="test@example.com")
        assert str(user) == "test@example.com"

    def test_soft_delete(self):
        """Test user soft delete functionality."""
        user = UserFactory()
        user_id = user.id
        
        # Soft delete
        user.delete()
        
        assert user.deleted is True
        assert user.deleted_at is not None
        
        # User should not appear in default queryset
        assert not User.objects.filter(id=user_id).exists()
        
        # But should appear in all_with_deleted queryset
        assert User.objects.all_with_deleted().filter(id=user_id).exists()

    def test_hard_delete(self):
        """Test user hard delete functionality."""
        user = UserFactory()
        user_id = user.id
        
        # Hard delete
        user.hard_delete()
        
        # User should not exist in any queryset
        assert not User.objects.all_with_deleted().filter(id=user_id).exists()


@pytest.mark.django_db
class TestMerchantModel:
    """Test cases for Merchant model."""

    def test_create_merchant(self):
        """Test creating a merchant."""
        merchant = MerchantFactory()
        assert merchant.user
        assert merchant.api_key
        assert merchant.webhook_url

    def test_merchant_str_method(self):
        """Test merchant string representation."""
        user = UserFactory(email="merchant@example.com")
        merchant = MerchantFactory(user=user)
        assert str(merchant) == "merchant@example.com"

    def test_merchant_api_key_unique(self):
        """Test that merchant API keys are unique."""
        api_key = "unique-test-api-key"
        MerchantFactory(api_key=api_key)
        
        with pytest.raises(IntegrityError):
            MerchantFactory(api_key=api_key)

    def test_merchant_cascade_delete(self):
        """Test that deleting user deletes merchant."""
        merchant = MerchantFactory()
        user = merchant.user
        merchant_id = merchant.id
        
        # Delete user (hard delete)
        user.hard_delete()
        
        # Merchant should also be deleted
        assert not Merchant.objects.filter(id=merchant_id).exists()


@pytest.mark.django_db
class TestOrderModel:
    """Test cases for Order model."""

    def test_create_order(self):
        """Test creating an order."""
        order = OrderFactory()
        assert order.order_id
        assert order.merchant
        assert order.amount > 0
        assert order.currency == 'INR'
        assert order.status == 'created'

    def test_order_str_method(self):
        """Test order string representation."""
        order = OrderFactory(order_id="test-order-123")
        assert str(order) == "test-order-123"

    def test_order_id_unique(self):
        """Test that order IDs are unique."""
        order_id = "unique-order-123"
        OrderFactory(order_id=order_id)
        
        with pytest.raises(IntegrityError):
            OrderFactory(order_id=order_id)

    def test_order_amount_precision(self):
        """Test order amount decimal precision."""
        order = OrderFactory(amount=Decimal('999.99'))
        assert order.amount == Decimal('999.99')

    def test_order_default_currency(self):
        """Test order default currency."""
        order = OrderFactory()
        assert order.currency == 'INR'

    def test_order_merchant_relationship(self):
        """Test order-merchant relationship."""
        merchant = MerchantFactory()
        order = OrderFactory(merchant=merchant)
        assert order.merchant == merchant


@pytest.mark.django_db
class TestPaymentModel:
    """Test cases for Payment model."""

    def test_create_payment(self):
        """Test creating a payment."""
        payment = PaymentFactory()
        assert payment.payment_id
        assert payment.order
        assert payment.amount > 0
        assert payment.status == 'pending'
        assert payment.card_hash

    def test_payment_str_method(self):
        """Test payment string representation."""
        payment = PaymentFactory(payment_id="test-payment-123")
        assert str(payment) == "test-payment-123"

    def test_payment_id_unique(self):
        """Test that payment IDs are unique."""
        payment_id = "unique-payment-123"
        PaymentFactory(payment_id=payment_id)
        
        with pytest.raises(IntegrityError):
            PaymentFactory(payment_id=payment_id)

    def test_payment_order_relationship(self):
        """Test payment-order relationship."""
        order = OrderFactory()
        payment = PaymentFactory(order=order)
        assert payment.order == order

    def test_payment_amount_matches_order(self):
        """Test payment amount can match order amount."""
        order = OrderFactory(amount=Decimal('100.50'))
        payment = PaymentFactory(order=order, amount=order.amount)
        assert payment.amount == order.amount

    def test_payment_status_choices(self):
        """Test payment status values."""
        # Test various status values that should be valid
        valid_statuses = ['pending', 'authorized', 'captured', 'failed', 'refunded', 'voided']
        for status in valid_statuses:
            payment = PaymentFactory(status=status)
            payment.save()  # Should not raise any error


@pytest.mark.django_db
class TestWebhookLogModel:
    """Test cases for WebhookLog model."""

    def test_create_webhook_log(self):
        """Test creating a webhook log."""
        webhook_log = WebhookLogFactory()
        assert webhook_log.payment
        assert webhook_log.payload
        assert webhook_log.status == 'sent'
        assert webhook_log.response

    def test_webhook_log_str_method(self):
        """Test webhook log string representation."""
        payment = PaymentFactory(payment_id="test-payment-123")
        webhook_log = WebhookLogFactory(payment=payment)
        assert str(webhook_log) == "Webhook for test-payment-123"

    def test_webhook_log_payload_structure(self):
        """Test webhook log payload structure."""
        webhook_log = WebhookLogFactory()
        payload = webhook_log.payload
        
        assert 'event' in payload
        assert 'payment_id' in payload
        assert 'order_id' in payload
        assert 'amount' in payload
        assert 'status' in payload

    def test_webhook_log_payment_relationship(self):
        """Test webhook log-payment relationship."""
        payment = PaymentFactory()
        webhook_log = WebhookLogFactory(payment=payment)
        assert webhook_log.payment == payment

    def test_webhook_log_cascade_delete(self):
        """Test that deleting payment deletes webhook logs."""
        webhook_log = WebhookLogFactory()
        payment = webhook_log.payment
        webhook_log_id = webhook_log.id
        
        # Delete payment
        payment.delete()
        
        # Webhook log should also be deleted
        assert not WebhookLog.objects.filter(id=webhook_log_id).exists()


@pytest.mark.django_db 
class TestModelRelationships:
    """Test model relationships and constraints."""

    def test_complete_payment_flow_models(self):
        """Test creating a complete payment flow."""
        # Create merchant with user
        merchant = MerchantFactory()
        
        # Create order for merchant
        order = OrderFactory(merchant=merchant, amount=Decimal('100.00'))
        
        # Create payment for order
        payment = PaymentFactory(order=order, amount=order.amount)
        
        # Create webhook log for payment
        webhook_log = WebhookLogFactory(payment=payment)
        
        # Test relationships
        assert order.merchant == merchant
        assert payment.order == order
        assert webhook_log.payment == payment
        
        # Test cascade relationships through merchant user
        assert payment.order.merchant.user == merchant.user

    def test_merchant_multiple_orders(self):
        """Test that merchant can have multiple orders."""
        merchant = MerchantFactory()
        order1 = OrderFactory(merchant=merchant)
        order2 = OrderFactory(merchant=merchant)
        
        # Both orders should belong to the same merchant
        assert order1.merchant == merchant
        assert order2.merchant == merchant

    def test_order_multiple_payments(self):
        """Test that order can have multiple payments."""
        order = OrderFactory()
        payment1 = PaymentFactory(order=order)
        payment2 = PaymentFactory(order=order)
        
        # Both payments should belong to the same order
        assert payment1.order == order
        assert payment2.order == order

    def test_payment_multiple_webhook_logs(self):
        """Test that payment can have multiple webhook logs."""
        payment = PaymentFactory()
        webhook1 = WebhookLogFactory(payment=payment)
        webhook2 = WebhookLogFactory(payment=payment)
        
        # Both webhooks should belong to the same payment
        assert webhook1.payment == payment
        assert webhook2.payment == payment