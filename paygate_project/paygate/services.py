import random
import hashlib
import requests
from django.utils import timezone
from .models import Payment, WebhookLog


class PaymentProcessor:
    @staticmethod
    def process_payment(order, card_details):
        """
        Mock payment processing with proper authorization and capture flow.
        Args:
            order: Order instance from models.Order
            card_details: Dict with card_number, expiry, cvv (mocked)
        Returns:
            tuple: (Payment instance, success boolean)
        """
        # Simulate card validation

        card_number = card_details.get('card_number', '')
        if not card_number or len(card_number) < 12:
            return None, False

        # Mock authorization success rate: 85% chance of success
        # auth_success = random.random() < 0.85
        auth_success = True
        if not auth_success:
            # Create failed payment
            card_hash = hashlib.sha256(card_number.encode()).hexdigest()
            payment = Payment.objects.create(
                order=order,
                amount=order.amount,
                status='failed',
                card_hash=card_hash,
                created_at=timezone.now()
            )

            return payment, False

        # Authorization successful - now determine capture
        # 70% chance of immediate capture, 30% chance of staying authorized
        immediate_capture = random.random() < 0.7
        status = 'captured' if immediate_capture else 'authorized'

        # Create card hash for storage (simulating secure tokenization)
        card_hash = hashlib.sha256(card_number.encode()).hexdigest()

        # Create Payment instance
        payment = Payment.objects.create(
            order=order,
            amount=order.amount,
            status=status,
            card_hash=card_hash,
            created_at=timezone.now()
        )

        return payment, True

    @staticmethod
    def capture_authorized_payment(payment):
        """
        Capture an authorized payment.
        Args:
            payment: Payment instance with 'authorized' status
        Returns:
            bool: True if capture succeeds, False otherwise
        """
        if payment.status != 'authorized':
            return False
        
        # Simulate capture processing (95% success rate)
        capture_success = random.random() < 0.95
        
        if capture_success:
            payment.status = 'captured'
            payment.save()
            return True
        
        # Capture failed - could set status to 'capture_failed' or keep 'authorized'
        return False

    @staticmethod
    def void_authorized_payment(payment):
        """
        Void an authorized payment (release the hold).
        Args:
            payment: Payment instance with 'authorized' status
        Returns:
            bool: True if void succeeds, False otherwise
        """
        if payment.status != 'authorized':
            return False
        
        payment.status = 'voided'
        payment.save()
        return True

    @staticmethod
    def process_refund(payment):
        """
        Process refund for captured payments only.
        Args:
            payment: Payment instance from models.Payment
        Returns:
            bool: True if refund succeeds, False otherwise
        """
        # Simulate refund processing (90% success rate)
        try:
            refund_success = random.random() < 0.90

            if refund_success:
                payment.full_refund()
                WebhookHandler.send_webhook(payment, payment.order.merchant)
                return True
        except ValueError:
            return False


class WebhookHandler:
    @staticmethod
    def send_webhook(payment, merchant):
        """
        Mock webhook sending to merchant's webhook_url.
        Args:
            payment: Payment instance from models.Payment
            merchant: Merchant instance from models.Merchant
        Returns:
            bool: True if webhook sent successfully (mocked), False otherwise
        """
        if not merchant.webhook_url:
            # Log failure if no webhook URL
            WebhookLog.objects.create(
                payment=payment,
                payload={'event': 'payment.' + payment.status, 'error': 'No webhook URL provided'},
                status='failed',
                response='No webhook URL configured for merchant',
                created_at=timezone.now()
            )
            return False

        # Mock webhook payload
        payload = {
            'event': 'payment.' + payment.status,
            'payment_id': str(payment.payment_id),
            'order_id': str(payment.order.order_id),
            'amount': str(payment.amount),
            'currency': payment.order.currency,
            'status': payment.status,
            'created_at': payment.created_at.isoformat()
        }

        try:
            # Simulate webhook request (80% success rate for mock)
            mock_response_status = 200 if random.random() < 0.8 else 500
            mock_response_text = (
                '{"status": "success"}' if mock_response_status == 200
                else '{"error": "Webhook endpoint failed"}'
            )

            # Log webhook attempt
            WebhookLog.objects.create(
                payment=payment,
                payload=payload,
                status='sent' if mock_response_status == 200 else 'failed',
                response=mock_response_text,
                created_at=timezone.now()
            )
            return mock_response_status == 200
        except Exception as e:
            # Log any unexpected errors
            WebhookLog.objects.create(
                payment=payment,
                payload=payload,
                status='failed',
                response=str(e),
                created_at=timezone.now()
            )
            return False