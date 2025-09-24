from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid
import hashlib

class UserManager(BaseUserManager):
    """Manager for User"""
    def create_user(self, email, password=None, **extra_fields):
        """Create, save, and return a new user"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

    def get_queryset(self):
        # Exclude deleted users
        return super().get_queryset().filter(deleted=False)

    def all_with_deleted(self):
        # Get all users including deleted ones
        return super().get_queryset()

class User(AbstractBaseUser, PermissionsMixin):
    """User in the system, used for authentication"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Tracks when user account was created
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)
    deleted = models.BooleanField(default=False)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def delete(self, *args, **kwargs):
        """Soft delete the user by setting `deleted` flag and `deleted_at` timestamp"""
        self.deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted', 'deleted_at'])

    def hard_delete(self, *args, **kwargs):
        """Permanent delete the user from the database"""
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.email

class Merchant(models.Model):
    """Merchant profile for payment gateway functionality"""
    user = models.OneToOneField('User', on_delete=models.CASCADE)
    api_key = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    webhook_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Tracks when merchant profile was created

    def __str__(self):
        return self.user.email

class Order(models.Model):
    order_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, default='created')  # created, paid, failed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_id

class Payment(models.Model):
    payment_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # pending, authorized, captured, failed
    card_hash = models.CharField(max_length=64, blank=True)  # Simulated card token
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id

class WebhookLog(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    payload = models.JSONField()
    status = models.CharField(max_length=20)  # sent, failed
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Webhook for {self.payment.payment_id}"