"""
Factory classes for creating test data.
"""
import factory
import uuid
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from paygate.models import Merchant, Order, Payment, WebhookLog

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker('name')
    is_active = True
    is_staff = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default _create method to use create_user."""
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class AdminUserFactory(UserFactory):
    """Factory for creating admin User instances."""
    
    email = factory.Sequence(lambda n: f"admin{n}@example.com")
    is_staff = True
    is_superuser = True


class MerchantFactory(DjangoModelFactory):
    """Factory for creating Merchant instances."""
    
    class Meta:
        model = Merchant
    
    user = factory.SubFactory(UserFactory)
    api_key = factory.LazyFunction(lambda: str(uuid.uuid4()))
    webhook_url = factory.Faker('url')


class OrderFactory(DjangoModelFactory):
    """Factory for creating Order instances."""
    
    class Meta:
        model = Order
    
    order_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    merchant = factory.SubFactory(MerchantFactory)
    amount = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    currency = 'INR'
    status = 'created'


class PaymentFactory(DjangoModelFactory):
    """Factory for creating Payment instances."""
    
    class Meta:
        model = Payment
    
    payment_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    order = factory.SubFactory(OrderFactory)
    amount = factory.LazyAttribute(lambda obj: obj.order.amount)
    status = 'pending'
    card_hash = factory.Faker('sha256')


class WebhookLogFactory(DjangoModelFactory):
    """Factory for creating WebhookLog instances."""
    
    class Meta:
        model = WebhookLog
    
    payment = factory.SubFactory(PaymentFactory)
    payload = factory.LazyAttribute(lambda obj: {
        'event': f'payment.{obj.payment.status}',
        'payment_id': str(obj.payment.payment_id),
        'order_id': str(obj.payment.order.order_id),
        'amount': str(obj.payment.amount),
        'status': obj.payment.status
    })
    status = 'sent'
    response = '{"status": "success"}'