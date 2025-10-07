from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from .models import Merchant,User , Order, Payment
from ratelimit.decorators import ratelimit
from .serializers import MerchantSerializer, UserSerializer , CustomTokenObtainPairSerializer , OrderSerializer, PaymentSerializer
from .jsonResponse.response import JSONResponseSender
from django.utils.decorators import method_decorator
from .services import WebhookHandler, PaymentProcessor
from rest_framework.decorators import action
from django.db.models import Count, Q, Sum
from .utils.permissions import IsMerchantUser
import uuid


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @method_decorator(ratelimit(key='ip', rate='5/m', block=True,method='POST'), name='dispatch')
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            refresh_token = data['refresh']
            response = JSONResponseSender.send_success(
                data={
                    'access': data['access'],
                    'email': data['email'],
                    'name': data['name'],
                    'api_key': data.get('api_key'),
                    'role': data.get('role')
                },
                message='Login successful'
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=getattr(request, 'is_secure', False),  # Secure in production
                samesite='None',
                max_age=7*24*60*60  # 7 days
            )
            return response
        except Exception as e:
            return JSONResponseSender.send_error(
                1001,
                'Login failed',
                str(e),
                None,
                400
            )

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/m', block=True,method='POST'), name='dispatch')
    def post(self, request):
        serializer = MerchantSerializer(data=request.data)
        if serializer.is_valid():
            merchant = serializer.save()
            refresh = CustomTokenObtainPairSerializer.get_token(merchant.user)
            access_token = str(refresh.access_token)
            response = JSONResponseSender.send_success(
                data={
                    'access': access_token,
                    'api_key': merchant.api_key,
                    'email': str(merchant.user.email),
                    'name': str(merchant.user.name),
                    'role': 'merchant'
                },
                message='Merchant registered successfully',
                status=201
            )
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=getattr(request, 'is_secure', False),
                samesite='Strict',
                max_age=7*24*60*60
            )
            return response
        return JSONResponseSender.send_error(
            1002,
            message='Registration failed',
            description=str(serializer.errors),
            status=400
        )

class RegisterAdminView(APIView):
    permission_classes = [IsAdminUser]  # Only superusers can access

    def post(self, request):
        user_data = request.data.get('user')
        if not user_data:
            return JSONResponseSender.send_error(
                code=1003,
                message='Invalid input',
                description='User data required',
                status=400
            )
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = User.objects.create_user(
                email=user_data['email'],
                name=user_data['name'],
                password=user_data['password'],
                is_staff=True,
                is_superuser=True
            )
            refresh = CustomTokenObtainPairSerializer.get_token(user)
            access_token = str(refresh.access_token)
            response = JSONResponseSender.send_success(
                data={
                    'access': access_token,
                    'email': user.email,
                    'name': user.name,
                    'role': 'admin'
                },
                message='Admin registered successfully',
                status=201
            )
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=getattr(request, 'is_secure', False),
                samesite='Strict',
                max_age=7*24*60*60
            )
            return response
        return JSONResponseSender.send_error(500,'Admin registration failed',str(user_serializer.errors),
            status=400
        )

class CustomTokenRefreshView(TokenRefreshView):

    @method_decorator(ratelimit(key='ip', rate='5/m', block=True,method='POST'), name='dispatch')
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return JSONResponseSender.send_error(
                code=400,
                message='No valid refresh token found in cookie.',
                description='no_refresh_token',
                status=400
            )
        try:
            # Create a serializer instance with the refresh token from cookie
            serializer = self.get_serializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)
            return JSONResponseSender.send_success(serializer.validated_data)
        except TokenError as e:
            return JSONResponseSender.send_error(
                code=401,
                message=str(e),
                description='token_not_valid',
                status=401
            )
        except Exception as e:
            return JSONResponseSender.send_error(
                code=400,
                message=str(e),
                description='token_not_valid',
                status=400
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m', block=True, method='POST'), name='dispatch')
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return JSONResponseSender.send_error(
                code=1011,
                message='Logout failed',
                description='No refresh token provided',
                status=400
            )

        try:
            token = RefreshToken(refresh_token)
            token.verify()      # Ensure it’s valid
            token.blacklist()   # Blacklist the refresh token

            response = JSONResponseSender.send_success(
                data={},
                message='Logout successful',
                status=200
            )
            response.delete_cookie(
                key='refresh_token',
                path='/',
                samesite='Strict'
            )
            return response

        except TokenError as e:
            return JSONResponseSender.send_error(
                code=1012,
                message='Logout failed',
                description=f'Invalid or expired refresh token: {str(e)}',
                status=400
            )

        except Exception as e:
            return JSONResponseSender.send_error(
                code=1013,
                message='Internal server error',
                description=str(e),
                status=500
            )


class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m', block=True, method='POST'), name='dispatch')
    def post(self, request):
        try:
            merchant = Merchant.objects.get(user=request.user)
        except Merchant.DoesNotExist:
            return JSONResponseSender.send_error(
                code=1008,
                message='Unauthorized',
                description='User is not a merchant',
                status=403
            )
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'INR')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            order = Order.objects.create(
                merchant=merchant,
                amount=amount,
                currency=currency
            )
            serializer = OrderSerializer(order)
            return JSONResponseSender.send_success(
                data=serializer.data,
                message='Order created successfully',
                status=201
            )
        except (ValueError, TypeError) as e:
            return JSONResponseSender.send_error(
                code=1009,
                message='Invalid input',
                description=str(e),
                status=400
            )


class InProgressOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return list of only order_id for orders with status='created'"""
        try:
            merchant = Merchant.objects.get(user=request.user)
            order_ids = (
                Order.objects.filter(merchant=merchant, status='created')
                .order_by('-created_at')
                .values_list('order_id', flat=True)
            )

            return JSONResponseSender.send_success(
                data=list(order_ids),
                message='In-progress order IDs retrieved successfully',
                )

        except Merchant.DoesNotExist:
            return JSONResponseSender.send_error(
                code=1007,
                message='Unauthorized',
                description='User is not a merchant',
                status=403
            )
        except Exception as e:
            return JSONResponseSender.send_error("500", str(e), str(e))

class CompletedPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            merchant = Merchant.objects.get(user=request.user)
            # payment_id = (
            #     Payment.objects.filter(order__merchant=merchant, status='captured').order_by('-created_at').values_list('payment_id', flat=True)
            # )
            payments = (
                Payment.objects.filter(order__merchant=merchant, status='captured').order_by('-created_at')
            )
            serializer = PaymentSerializer(payments, many=True)
            return JSONResponseSender.send_success(serializer.data, message='Payment completed successfully')
        except Exception as e:
            return JSONResponseSender.send_error("500", str(e), str(e))

class PaymentProcessView(APIView):
    permission_classes = [IsAuthenticated]

    # @method_decorator(ratelimit(key='ip', rate='5/m', block=True, method='POST'), name='dispatch')
    def post(self, request):

        order_id = request.data.get('order_id')
        card_details = request.data.get('card_details', {})

        try:
            merchant = Merchant.objects.get(user=request.user)
            order = Order.objects.get(order_id=order_id, merchant=merchant)
            payment, success = PaymentProcessor.process_payment(order, card_details)

            if not payment:
                return JSONResponseSender.send_error(
                    code=1011,
                    message='Payment failed',
                    description='Invalid card details',
                    status=400
                )

            if success and payment.status=='captured':
                order.status = 'paid'
                order.save()
                WebhookHandler.send_webhook(payment, merchant)
            elif success:
                order.status = 'In-process'
            else:
                order.status = 'failed'
                order.save()
            serializer = PaymentSerializer(payment)
            return JSONResponseSender.send_success(
                data=serializer.data,
                message='Payment processed successfully',
                status=201
            )
        except Order.DoesNotExist:
            return JSONResponseSender.send_error(
                code=1012,
                message='Not found',
                description='Order not found',
                status=404
            )
        except Exception as e:
            print(str(e))
            return JSONResponseSender.send_error("500",str(e),str(e))


class RefundProcessView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m', block=True, method='POST'), name='dispatch')
    def post(self, request):

        try:
            merchant = Merchant.objects.get(user=request.user)
        except Merchant.DoesNotExist:
            return JSONResponseSender.send_error(
                code=1013,
                message='Unauthorized',
                description='User is not a merchant',
                status=403
            )
        payment_id = request.data.get('payment_id')
        try:
            payment = Payment.objects.get(payment_id=payment_id, order__merchant=merchant)
            if PaymentProcessor.process_refund(payment):
                WebhookHandler.send_webhook(payment, merchant)
                return JSONResponseSender.send_success(
                    data={'status': 'refunded'},
                    message='Refund processed successfully',
                    status=200
                )
            return JSONResponseSender.send_error(
                code=1014,
                message='Refund failed',
                description='Refund processing failed',
                status=400
            )
        except Payment.DoesNotExist:
            return JSONResponseSender.send_error(
                code=1015,
                message='Not found',
                description='Payment not found',
                status=404
            )



class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    # @method_decorator(ratelimit(key='ip', rate='5/m', block=True, method='POST'), name='dispatch')
    def get(self, request):
        try:
            merchant_id = request.query_params.get('merchant_id')
            print(f'merchant_id: {merchant_id}')
            if merchant_id:
                try:
                    # Validate UUID
                    # uuid_obj = uuid.UUID(merchant_id)
                    merchant = Merchant.objects.get(id=merchant_id)
                except (ValueError, Merchant.DoesNotExist):
                    return JSONResponseSender.send_error(
                        code=1019,
                        message='Invalid merchant ID',
                        description='Merchant not found or invalid UUID',
                        status=404
                    )
                # Filter metrics by merchant_id
                total_orders = Order.objects.filter(merchant=merchant).count()
                total_successful_payments = Payment.objects.filter(
                    order__merchant=merchant, status__in=['captured']
                ).count()
                total_captured_payments = Payment.objects.filter(
                    order__merchant=merchant, status='captured'
                ).count()
                total_authorized_payments = Payment.objects.filter(
                    order__merchant=merchant, status='authorized'
                ).count()
                total_successful_refunds = Payment.objects.filter(
                    order__merchant=merchant, status='refunded'
                ).count()
                total_canceled_payments = Payment.objects.filter(
                    order__merchant=merchant, status='failed'
                ).count()

                return JSONResponseSender.send_success(
                    data={
                        'user__email': merchant.user.email,
                        'order_count': total_orders,
                        'payment_count': total_successful_payments,
                        'successful_payments': total_successful_payments,
                        'authorized_payments': total_authorized_payments,
                        'captured_payments': total_captured_payments,
                        'successful_refunds': total_successful_refunds,
                        'canceled_payments': total_canceled_payments
                    }
                )
            else:
                total_merchants = Merchant.objects.count()
                total_admins = User.objects.filter(is_staff=True).count()
                total_commission = Payment.objects.aggregate(total=Sum('commission_amount'))['total'] or 0
                total_orders = Order.objects.count()
                total_successful_payments = Payment.objects.filter(status__in=['captured','refunded']).count()
                total_captured_payments = Payment.objects.filter(status='captured').count()
                total_authorized_payments = Payment.objects.filter(status='authorized').count()
                total_successful_refunds = Payment.objects.filter(status='refunded').count()
                total_canceled_payments = Payment.objects.filter(status='failed').count()
                return JSONResponseSender.send_success(
                    data={
                        'total_merchants': total_merchants,
                        'total_admins': total_admins,
                        'total_orders': total_orders,
                        'total_commission': total_commission,
                        'total_successful_payments': total_successful_payments,
                        'total_authorized_payments': total_authorized_payments,
                        'total_captured_payments': total_captured_payments,
                        'total_successful_refunds': total_successful_refunds,
                        'total_canceled_payments': total_canceled_payments,
                    },
                    message='Admin statistics retrieved successfully',
                    status=200
                )
            # Common metrics (not merchant-specific)

            # total_merchants = Merchant.objects.count()
            # total_admins = User.objects.filter(is_staff=True).count()


        except Exception as e:
            return JSONResponseSender.send_error(
                code=1020,
                message='Failed to retrieve statistics',
                description=str(e),
                status=500
            )


class MerchantStatsView(APIView):
    permission_classes = [IsAuthenticated, IsMerchantUser]

    #@method_decorator(ratelimit(key='ip', rate='5/m', block=True, method='GET'), name='dispatch')
    def get(self, request):
        try:
            merchant = Merchant.objects.get(user=request.user)
            if not merchant:
                return JSONResponseSender.send_error('403','Unauthorized','User is not a merchant')

            total_orders = Order.objects.filter(merchant=merchant).count()
            total_successful_payments = Payment.objects.filter(
                order__merchant=merchant, status='captured'
            ).count()

            total_revenue = Payment.objects.filter(order__merchant=merchant,status='captured').aggregate(total=Sum('merchant_payout'))['total'] or 0
            total_successful_refunds = Payment.objects.filter(
                order__merchant=merchant, status='refunded'
            ).count()
            total_canceled_payments = Payment.objects.filter(
                order__merchant=merchant, status='failed'
            ).count()
            total_authorized_payments = Payment.objects.filter(order__merchant=merchant, status='authorized').count()

            return JSONResponseSender.send_success(
                data={
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                    'successful_payments': total_successful_payments,
                    'successful_refunds': total_successful_refunds,
                    'canceled_payments': total_canceled_payments,
                    'authorized_payments': total_authorized_payments,
                }
            )
        except Exception as e:
            return JSONResponseSender.send_error("500","Failed to retrieve merchant statistics",str(e))


