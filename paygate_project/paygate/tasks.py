from celery import shared_task
from .models import Payment, WebhookLog, Merchant
import random
from django.utils import timezone
import logging


@shared_task(bind=True, max_retries=3)
def send_webhook_task(self, payment_id, merchant_id):
    """
    Async task to send webhook. Retries on failure.
    """
    print("sending webhook task")
    try:
        payment = Payment.objects.get(id=payment_id)
        merchant = Merchant.objects.get(id=merchant_id)

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

        success = mock_response_status == 200
        if not success:
            raise Exception("Webhook failed")  # Trigger retry

        logging.info(f"Webhook sent successfully for payment {payment_id}")
        return True
    except Exception as exc:
        logging.error(f"Webhook task failed for payment {payment_id}: {str(exc)}")
        # Celery will retry automatically
        self.retry(exc=exc)