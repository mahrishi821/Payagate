from django.urls import path
from .views import (
    RegisterView, RegisterAdminView, CustomTokenObtainPairView,LogoutView ,CustomTokenRefreshView
     , OrderCreateView, PaymentProcessView, RefundProcessView, AdminStatsView
)


urlpatterns = [
    path('api/v1/auth/register/', RegisterView.as_view(), name='register'),  # register the merchant user
    path('api/v1/auth/register-admin/', RegisterAdminView.as_view(), name='register-admin'),  # register the admin user
    path('api/v1/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # login
    path('api/v1/auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),     # refresh token
    path('api/v1/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/v1/orders/', OrderCreateView.as_view(), name='order_create'),
    path('api/v1/payments/', PaymentProcessView.as_view(), name='payment_process'),
    path('api/v1/refunds/', RefundProcessView.as_view(), name='refund_process'),
    path('api/v1/admin/stats/', AdminStatsView.as_view(), name='admin_stats'),
]