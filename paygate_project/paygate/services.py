import logging
import random
import hashlib
import requests
from django.utils import timezone
from django.db import transaction
from .models import Payment, WebhookLog
from .tasks import send_webhook_task

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
        auth_success = random.random() < 0.85

        if not auth_success:
            # Create failed payment
            card_hash = hashlib.sha256(card_number.encode()).hexdigest()
            with transaction.atomic():
                payment = Payment.objects.create(
                    order=order,
                    amount=order.amount,
                    status='failed',
                    card_hash=card_hash,
                    created_at=timezone.now()
                )
            WebhookHandler.send_webhook(payment, payment.order.merchant)
            return payment, False

        # Authorization successful - now determine capture
        # 70% chance of immediate capture, 30% chance of staying authorized
        immediate_capture = random.random() < 0.7
        status = 'captured' if immediate_capture else 'authorized'

        # Create card hash for storage (simulating secure tokenization)
        card_hash = hashlib.sha256(card_number.encode()).hexdigest()

        # Create Payment instance
        with transaction.atomic():
            payment = Payment.objects.create(
                order=order,
                amount=order.amount,
                status=status,
                card_hash=card_hash,
            )
        WebhookHandler.send_webhook(payment, payment.order.merchant)
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
            with transaction.atomic():
                payment.status = 'captured'
                payment.save()
                WebhookHandler.send_webhook(payment, payment.order.merchant)
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
        if payment.status != 'captured':
            return False
        # Simulate refund processing (90% success rate)
        try:
            refund_success = random.random() < 0.90

            if refund_success:
                with transaction.atomic():
                    payment.full_refund()
                    WebhookHandler.send_webhook(payment, payment.order.merchant)
                return True
        except Exception as e:
            logging.error(e)
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
        print("yup:  here i was ")
        print(f"webhook url : {merchant.webhook_url}")
        if not merchant.webhook_url:
            print(f"payment id : {payment.id} \n merchant id : {merchant.id}")
            # Log failure if no webhook URL
            WebhookLog.objects.create(
                payment=payment,
                payload={'event': 'payment.' + payment.status, 'error': 'No webhook URL provided'},
                status='failed',
                response='No webhook URL configured for merchant',
                created_at=timezone.now()
            )
            return False

        # Trigger the async task (no loop here—the task won't call back)
        print(f"payment id : {payment.id} \n merchant id : {merchant.id}")
        send_webhook_task.delay(payment.id, merchant.id)
        return True  # Return immediately, assuming the task will handle it