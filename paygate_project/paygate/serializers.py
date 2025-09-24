from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Merchant , Order, Payment, WebhookLog

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        print(f"inside the validate")
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['email'] = self.user.email
        data['name'] = self.user.name
        try:
            merchant = Merchant.objects.get(user=self.user)
            data['api_key'] = merchant.api_key
            data['role'] = 'merchant'
        except Merchant.DoesNotExist:
            data['api_key'] = None
            data['role'] = 'admin' if self.user.is_staff else 'user'
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class MerchantSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Merchant
        fields = ['user', 'api_key', 'webhook_url']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer().create(user_data)
        merchant = Merchant.objects.create(user=user, **validated_data)
        return merchant

class OrderSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField()
    class Meta:
        model = Order
        fields = ['order_id', 'amount', 'currency', 'status', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    payment_id = serializers.CharField()  # Explicitly define as CharField
    order = serializers.CharField(source='order.order_id')  # Serialize order as order_id string
    class Meta:
        model = Payment
        fields = ['payment_id', 'order', 'amount', 'status', 'created_at']

class WebhookLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookLog
        fields = ['payment', 'payload', 'status', 'response', 'created_at']