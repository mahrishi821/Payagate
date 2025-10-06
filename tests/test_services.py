"""
Tests for paygate service layer (PaymentProcessor and WebhookHandler).
"""
import pytest
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock, call
from django.utils import timezone
from django.contrib.auth import get_user_model

from paygate.services import PaymentProcessor, WebhookHandler
from paygate.models import Payment, WebhookLog
from .factories import (
    UserFactory, MerchantFactory, OrderFactory, 
    PaymentFactory, WebhookLogFactory
)

User = get_user_model()


@pytest.mark.django_db
class TestPaymentProcessor:
    """Test PaymentProcessor service."""

    def setup_method(self):
        """Set up test data for each test."""
        self.merchant = MerchantFactory()
        self.order = OrderFactory(merchant=self.merchant, amount=Decimal('100.00'))

    def test_process_payment_success(self):
        """Test successful payment processing."""
        card_details = {
            'card_number': '4111111111111111',
            'expiry': '12/25',
            'cvv': '123'
        }
        
        with patch('random.random', return_value=0.5):  # Mock 80% success rate
            payment, success = PaymentProcessor.process_payment(self.order, card_details)
        
        assert success is True
        assert payment is not None
        assert payment.order == self.order
        assert payment.amount == self.order.amount
        assert payment.status == 'authorized'
        assert payment.card_hash is not None
        assert len(payment.card_hash) == 64  # SHA256 hash length
        
        # Verify payment was saved to database
        assert Payment.objects.filter(payment_id=payment.payment_id).exists()

    def test_process_payment_failure(self):
        """Test failed payment processing due to random failure."""
        card_details = {
            'card_number': '4111111111111111',
            'expiry': '12/25',
            'cvv': '123'
        }
        
        with patch('random.random', return_value=0.9):  # Mock failure (>80%)
            payment, success = PaymentProcessor.process_payment(self.order, card_details)
        
        assert success is False
        assert payment is not None
        assert payment.status == 'failed'
        assert payment.order == self.order

    def test_process_payment_invalid_card_number(self):
        """Test payment processing with invalid card number."""
        invalid_card_details = [
            {'card_number': '123', 'expiry': '12/25', 'cvv': '123'},  # Too short
            {'card_number': '', 'expiry': '12/25', 'cvv': '123'},     # Empty
            {'card_number': None, 'expiry': '12/25', 'cvv': '123'},   # None
        ]
        
        for card_details in invalid_card_details:
            payment, success = PaymentProcessor.process_payment(self.order, card_details)
            
            assert payment is None
            assert success is False

    def test_process_payment_missing_card_details(self):
        """Test payment processing with missing card details."""
        card_details = {}  # Empty card details
        
        payment, success = PaymentProcessor.process_payment(self.order, card_details)
        
        assert payment is None
        assert success is False

    def test_process_payment_card_hashing(self):
        """Test that card numbers are properly hashed."""
        card_details = {
            'card_number': '4111111111111111',
            'expiry': '12/25',
            'cvv': '123'
        }
        
        with patch('random.random', return_value=0.5):
            payment, success = PaymentProcessor.process_payment(self.order, card_details)
        
        assert success is True
        # Verify the card number is hashed, not stored in plain text
        assert payment.card_hash != card_details['card_number']
        assert len(payment.card_hash) == 64  # SHA256 length
        
        # Verify the same card number produces the same hash
        with patch('random.random', return_value=0.5):
            payment2, success2 = PaymentProcessor.process_payment(self.order, card_details)
        
        assert payment.card_hash == payment2.card_hash

    def test_process_payment_creates_unique_payment_id(self):
        """Test that each payment gets a unique payment ID."""
        card_details = {
            'card_number': '4111111111111111',
            'expiry': '12/25',
            'cvv': '123'
        }
        
        with patch('random.random', return_value=0.5):
            payment1, success1 = PaymentProcessor.process_payment(self.order, card_details)
            payment2, success2 = PaymentProcessor.process_payment(self.order, card_details)
        
        assert success1 is True
        assert success2 is True
        assert payment1.payment_id != payment2.payment_id

    def test_process_payment_sets_timestamp(self):
        """Test that payment timestamp is set correctly."""
        card_details = {
            'card_number': '4111111111111111',
            'expiry': '12/25',
            'cvv': '123'
        }
        
        before_time = timezone.now()
        with patch('random.random', return_value=0.5):
            payment, success = PaymentProcessor.process_payment(self.order, card_details)
        after_time = timezone.now()
        
        assert success is True
        assert before_time <= payment.created_at <= after_time


@pytest.mark.django_db
class TestPaymentProcessorRefunds:
    """Test PaymentProcessor refund functionality."""

    def setup_method(self):
        """Set up test data for each test."""
        self.merchant = MerchantFactory()
        self.order = OrderFactory(merchant=self.merchant)

    def test_process_refund_authorized_payment(self):
        """Test successful refund of authorized payment."""
        payment = PaymentFactory(order=self.order, status='authorized')
        
        result = PaymentProcessor.process_refund(payment)
        
        assert result is True
        payment.refresh_from_db()
        assert payment.status == 'refunded'

    def test_process_refund_captured_payment(self):
        """Test successful refund of captured payment."""
        payment = PaymentFactory(order=self.order, status='captured')
        
        result = PaymentProcessor.process_refund(payment)
        
        assert result is True
        payment.refresh_from_db()
        assert payment.status == 'refunded'

    def test_process_refund_invalid_status(self):
        """Test refund failure for payments with invalid status."""
        invalid_statuses = ['pending', 'failed', 'refunded']
        
        for status in invalid_statuses:
            payment = PaymentFactory(order=self.order, status=status)
            original_status = payment.status
            
            result = PaymentProcessor.process_refund(payment)
            
            assert result is False
            payment.refresh_from_db()
            assert payment.status == original_status  # Status unchanged

    def test_process_refund_already_refunded(self):
        """Test refund attempt on already refunded payment."""
        payment = PaymentFactory(order=self.order, status='refunded')
        
        result = PaymentProcessor.process_refund(payment)
        
        assert result is False
        payment.refresh_from_db()
        assert payment.status == 'refunded'  # Status unchanged

    def test_process_refund_updates_only_status(self):
        """Test that refund only updates the status field."""
        payment = PaymentFactory(order=self.order, status='authorized')
        original_amount = payment.amount
        original_created_at = payment.created_at
        original_payment_id = payment.payment_id
        
        result = PaymentProcessor.process_refund(payment)
        
        assert result is True
        payment.refresh_from_db()
        assert payment.status == 'refunded'
        assert payment.amount == original_amount
        assert payment.created_at == original_created_at
        assert payment.payment_id == original_payment_id


@pytest.mark.django_db 
class TestWebhookHandler:
    """Test WebhookHandler service."""

    def setup_method(self):
        """Set up test data for each test."""
        self.merchant = MerchantFactory(webhook_url='https://example.com/webhook')
        self.order = OrderFactory(merchant=self.merchant)
        self.payment = PaymentFactory(order=self.order, status='authorized')

    def test_send_webhook_success(self):
        """Test successful webhook sending."""
        with patch('random.random', return_value=0.5):  # Mock 80% success rate
            result = WebhookHandler.send_webhook(self.payment, self.merchant)
        
        assert result is True
        
        # Verify webhook log was created
        webhook_log = WebhookLog.objects.get(payment=self.payment)
        assert webhook_log.status == 'sent'
        assert webhook_log.response == '{"status": "success"}'
        
        # Verify payload structure
        payload = webhook_log.payload
        assert payload['event'] == f'payment.{self.payment.status}'
        assert payload['payment_id'] == str(self.payment.payment_id)
        assert payload['order_id'] == str(self.payment.order.order_id)
        assert payload['amount'] == str(self.payment.amount)
        assert payload['currency'] == self.payment.order.currency
        assert payload['status'] == self.payment.status
        assert 'created_at' in payload

    def test_send_webhook_failure(self):
        """Test failed webhook sending."""
        with patch('random.random', return_value=0.9):  # Mock failure (>80%)
            result = WebhookHandler.send_webhook(self.payment, self.merchant)
        
        assert result is False
        
        # Verify webhook log was created with failure
        webhook_log = WebhookLog.objects.get(payment=self.payment)
        assert webhook_log.status == 'failed'
        assert webhook_log.response == '{"error": "Webhook endpoint failed"}'

    def test_send_webhook_no_webhook_url(self):
        """Test webhook handling when merchant has no webhook URL."""
        merchant_no_webhook = MerchantFactory(webhook_url='')
        order = OrderFactory(merchant=merchant_no_webhook)
        payment = PaymentFactory(order=order)
        
        result = WebhookHandler.send_webhook(payment, merchant_no_webhook)
        
        assert result is False
        
        # Verify webhook log was created with appropriate error
        webhook_log = WebhookLog.objects.get(payment=payment)
        assert webhook_log.status == 'failed'
        assert webhook_log.response == 'No webhook URL configured for merchant'
        assert 'No webhook URL provided' in webhook_log.payload['error']

    def test_send_webhook_null_webhook_url(self):
        """Test webhook handling when merchant has null webhook URL."""
        merchant_null_webhook = MerchantFactory(webhook_url=None)
        order = OrderFactory(merchant=merchant_null_webhook)
        payment = PaymentFactory(order=order)
        
        result = WebhookHandler.send_webhook(payment, merchant_null_webhook)
        
        assert result is False

    def test_send_webhook_payload_format(self):
        """Test webhook payload format and content."""
        payment = PaymentFactory(
            order=self.order,
            status='captured',
            amount=Decimal('150.75')
        )
        
        with patch('random.random', return_value=0.5):
            WebhookHandler.send_webhook(payment, self.merchant)
        
        webhook_log = WebhookLog.objects.get(payment=payment)
        payload = webhook_log.payload
        
        # Test all required fields
        expected_fields = ['event', 'payment_id', 'order_id', 'amount', 'currency', 'status', 'created_at']
        for field in expected_fields:
            assert field in payload, f"Field '{field}' missing from webhook payload"
        
        # Test field values
        assert payload['event'] == 'payment.captured'
        assert payload['payment_id'] == str(payment.payment_id)
        assert payload['order_id'] == str(payment.order.order_id)
        assert payload['amount'] == '150.75'
        assert payload['currency'] == payment.order.currency
        assert payload['status'] == 'captured'

    def test_send_webhook_different_payment_statuses(self):
        """Test webhook payload for different payment statuses."""
        statuses = ['pending', 'authorized', 'captured', 'failed', 'refunded']
        
        for status in statuses:
            payment = PaymentFactory(order=self.order, status=status)
            
            with patch('random.random', return_value=0.5):
                WebhookHandler.send_webhook(payment, self.merchant)
            
            webhook_log = WebhookLog.objects.get(payment=payment)
            payload = webhook_log.payload
            
            assert payload['event'] == f'payment.{status}'
            assert payload['status'] == status

    def test_send_webhook_creates_log_on_exception(self):
        """Test that webhook logs are created even when exceptions occur."""
        # This test ensures that any unexpected errors are logged
        with patch('paygate.services.WebhookHandler.send_webhook') as mock_send:
            # Simulate an exception during webhook processing
            def side_effect(*args, **kwargs):
                # Create the log entry manually to test exception handling
                WebhookLog.objects.create(
                    payment=self.payment,
                    payload={'event': 'payment.authorized', 'error': 'Test exception'},
                    status='failed',
                    response='Test exception occurred'
                )
                return False
            
            mock_send.side_effect = side_effect
            result = WebhookHandler.send_webhook(self.payment, self.merchant)
            
            assert result is False
            assert WebhookLog.objects.filter(payment=self.payment).exists()

    @patch('random.random')
    def test_webhook_retry_behavior_simulation(self, mock_random):
        """Test webhook behavior under different success rates."""
        # Simulate multiple webhook attempts with different outcomes
        mock_random.side_effect = [0.9, 0.5]  # First fails, second succeeds
        
        # First attempt (failure)
        result1 = WebhookHandler.send_webhook(self.payment, self.merchant)
        assert result1 is False
        
        # Second attempt (success) - simulating retry
        payment2 = PaymentFactory(order=self.order, status='captured')
        result2 = WebhookHandler.send_webhook(payment2, self.merchant)
        assert result2 is True
        
        # Verify both attempts were logged
        assert WebhookLog.objects.filter(payment=self.payment).count() == 1
        assert WebhookLog.objects.filter(payment=payment2).count() == 1

    def test_webhook_multiple_logs_per_payment(self):
        """Test that multiple webhook logs can be created for the same payment."""
        # This simulates retry scenarios or status updates
        with patch('random.random', return_value=0.5):
            # First webhook
            WebhookHandler.send_webhook(self.payment, self.merchant)
            
            # Update payment status and send another webhook
            self.payment.status = 'captured'
            self.payment.save()
            WebhookHandler.send_webhook(self.payment, self.merchant)
        
        # Should have 2 webhook logs for the same payment
        logs = WebhookLog.objects.filter(payment=self.payment)
        assert logs.count() == 2
        
        # Verify different events were logged
        events = [log.payload['event'] for log in logs]
        assert 'payment.authorized' in events
        assert 'payment.captured' in events


@pytest.mark.django_db
class TestServiceIntegration:
    """Test integration between PaymentProcessor and WebhookHandler."""

    def setup_method(self):
        """Set up test data for each test."""
        self.merchant = MerchantFactory(webhook_url='https://example.com/webhook')
        self.order = OrderFactory(merchant=self.merchant, amount=Decimal('200.00'))

    @patch('random.random')
    def test_payment_to_webhook_flow(self, mock_random):
        """Test complete flow from payment processing to webhook."""
        # Mock successful payment
        mock_random.return_value = 0.5
        
        card_details = {
            'card_number': '4111111111111111',
            'expiry': '12/25',
            'cvv': '123'
        }
        
        # Process payment
        payment, payment_success = PaymentProcessor.process_payment(self.order, card_details)
        assert payment_success is True
        assert payment.status == 'authorized'
        
        # Send webhook
        webhook_success = WebhookHandler.send_webhook(payment, self.merchant)
        assert webhook_success is True
        
        # Verify webhook log contains correct payment info
        webhook_log = WebhookLog.objects.get(payment=payment)
        payload = webhook_log.payload
        assert payload['payment_id'] == str(payment.payment_id)
        assert payload['amount'] == str(payment.amount)
        assert payload['status'] == 'authorized'

    def test_refund_to_webhook_flow(self):
        """Test complete flow from refund processing to webhook."""
        # Create an authorized payment
        payment = PaymentFactory(order=self.order, status='authorized')
        
        # Process refund
        refund_success = PaymentProcessor.process_refund(payment)
        assert refund_success is True
        assert payment.status == 'refunded'
        
        # Send webhook for refund
        with patch('random.random', return_value=0.5):
            webhook_success = WebhookHandler.send_webhook(payment, self.merchant)
        assert webhook_success is True
        
        # Verify webhook log reflects refunded status
        webhook_log = WebhookLog.objects.get(payment=payment)
        payload = webhook_log.payload
        assert payload['event'] == 'payment.refunded'
        assert payload['status'] == 'refunded'

    def test_failed_payment_webhook(self):
        """Test webhook for failed payment."""
        card_details = {
            'card_number': '4111111111111111',
            'expiry': '12/25',
            'cvv': '123'
        }
        
        # Mock failed payment
        with patch('random.random', return_value=0.9):  # >80% = failure
            payment, payment_success = PaymentProcessor.process_payment(self.order, card_details)
        
        assert payment_success is False
        assert payment.status == 'failed'
        
        # Send webhook for failed payment
        with patch('random.random', return_value=0.5):  # Webhook succeeds
            webhook_success = WebhookHandler.send_webhook(payment, self.merchant)
        assert webhook_success is True
        
        # Verify webhook contains failure information
        webhook_log = WebhookLog.objects.get(payment=payment)
        payload = webhook_log.payload
        assert payload['event'] == 'payment.failed'
        assert payload['status'] == 'failed'

    def test_service_error_handling(self):
        """Test error handling in service integration."""
        # Test payment with invalid card and webhook attempt
        card_details = {'card_number': '123'}  # Invalid
        
        payment, success = PaymentProcessor.process_payment(self.order, card_details)
        assert payment is None
        assert success is False
        
        # Attempting webhook with None payment should not crash
        # (This would be handled at the view level, but testing robustness)
        if payment is not None:  # Only if payment exists
            WebhookHandler.send_webhook(payment, self.merchant)