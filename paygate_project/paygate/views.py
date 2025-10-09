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
from django.views.decorators.csrf import csrf_exempt
from .utils.mixins import RateLimitedMixin
from .utils.helpers import get_merchant_from_user
import uuid
from .utils.error_codes_constants import ErrorCodes, get_error_message


@method_decorator(csrf_exempt, name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


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
                code=ErrorCodes.LOGIN_FAILED,
                message=get_error_message(ErrorCodes.LOGIN_FAILED),
                description=str(e),
            )

class RegisterView(RateLimitedMixin,APIView):
    permission_classes = [AllowAny]


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
            ErrorCodes.REGISTRATION_FAILED,
            message=get_error_message(ErrorCodes.REGISTRATION_FAILED),
            description=str(serializer.errors),
        )

class RegisterAdminView(APIView):
    permission_classes = [IsAdminUser]  # Only superusers can access

    def post(self, request):
        user_data = request.data.get('user')
        if not user_data:
            return JSONResponseSender.send_error(
                code=ErrorCodes.ADMIN_REG_MISSING_DATA,
                message=get_error_message(ErrorCodes.ADMIN_REG_MISSING_DATA),
                description='User data required',
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
        return JSONResponseSender.send_error(ErrorCodes.ADMIN_REG_FAILED,'Admin registration failed',str(user_serializer.errors),
        )

class CustomTokenRefreshView(RateLimitedMixin,TokenRefreshView):


    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return JSONResponseSender.send_error(
                code=ErrorCodes.TOKEN_REFRESH_NO_TOKEN,
                message=get_error_message(ErrorCodes.TOKEN_REFRESH_NO_TOKEN),
                description='no_refresh_token',
            )
        try:
            # Create a serializer instance with the refresh token from cookie
            serializer = self.get_serializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)
            return JSONResponseSender.send_success(serializer.validated_data)
        except TokenError as e:
            return JSONResponseSender.send_error(
                code=ErrorCodes.TOKEN_REFRESH_INVALID,
                message=get_error_message(ErrorCodes.TOKEN_REFRESH_INVALID),
                description='token_not_valid',
            )
        except Exception as e:
            return JSONResponseSender.send_error(
                code=ErrorCodes.TOKEN_REFRESH_INVALID,
                message=get_error_message(ErrorCodes.TOKEN_REFRESH_INVALID),
                description='token_not_valid',
            )


class LogoutView(RateLimitedMixin,APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return JSONResponseSender.send_error(
                code=ErrorCodes.LOGOUT_NO_TOKEN,
                message=get_error_message(ErrorCodes.LOGOUT_NO_TOKEN),
                description='No refresh token provided',
            )

        try:
            token = RefreshToken(refresh_token)
            token.verify()      # Ensure it’s valid
            token.blacklist()   # Blacklist the refresh token

            response = JSONResponseSender.send_success(
                data={},
                message='Logout successful',
            )
            response.delete_cookie(
                key='refresh_token',
                path='/',
                samesite='Strict'
            )
            return response

        except TokenError as e:
            return JSONResponseSender.send_error(
                code=ErrorCodes.LOGOUT_INVALID_TOKEN,
                message=get_error_message(ErrorCodes.LOGOUT_INVALID_TOKEN),
                description=f'Invalid or expired refresh token: {str(e)}',
            )

        except Exception as e:
            return JSONResponseSender.send_error(
                code=ErrorCodes.LOGOUT_SERVER_ERROR,
                message=get_error_message(ErrorCodes.LOGOUT_SERVER_ERROR),
                description=str(e),
            )


class OrderCreateView(RateLimitedMixin,APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            merchant = get_merchant_from_user(request.user)
            if not merchant:
                return JSONResponseSender.send_error(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT, get_error_message(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT), "User is not a merchant")

            amount = request.data.get('amount')
            currency = request.data.get('currency', 'INR')
            if not amount:
                return JSONResponseSender.send_error(ErrorCodes.ORDER_MISSING_AMOUNT, get_error_message(ErrorCodes.ORDER_MISSING_AMOUNT), "amount is required")
            if not currency:
                return JSONResponseSender.send_error(ErrorCodes.ORDER_MISSING_CURRENCY, get_error_message(ErrorCodes.ORDER_MISSING_CURRENCY), "currency is required")
            try:
                amount = float(amount)
            except ValueError:
                return JSONResponseSender.send_error(ErrorCodes.ORDER_INVALID_AMOUNT_FORMAT, get_error_message(ErrorCodes.ORDER_INVALID_AMOUNT_FORMAT), "Invalid amount format")
            if amount <= 0:
                return JSONResponseSender.send_error(ErrorCodes.ORDER_AMOUNT_NOT_POSITIVE, get_error_message(ErrorCodes.ORDER_AMOUNT_NOT_POSITIVE), "Amount must be positive")
            order = Order.objects.create(
                merchant=merchant,
                amount=amount,
                currency=currency
            )
            serializer = OrderSerializer(order)
            return JSONResponseSender.send_success(
                data=serializer.data,
                message='Order created successfully',
            )
        except Exception as e:
            return JSONResponseSender.send_error(
                code=ErrorCodes.INTERNAL_SERVER_ERROR,
                message=get_error_message(ErrorCodes.INTERNAL_SERVER_ERROR),
                description=str(e),
            )


class InProgressOrdersView(RateLimitedMixin,APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return list of only order_id for orders with status='created'"""
        try:
            merchant = get_merchant_from_user(request.user)
            if not merchant:
                return JSONResponseSender.send_error(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT, get_error_message(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT), "User is not a merchant")
            order_ids = (
                Order.objects.filter(merchant=merchant, status='created')
                .order_by('-created_at')
                .values_list('order_id', flat=True)
            )

            return JSONResponseSender.send_success(
                data=list(order_ids),
                message='In-progress order IDs retrieved successfully',
                )

        except Exception as e:
            return JSONResponseSender.send_error(ErrorCodes.INTERNAL_SERVER_ERROR, get_error_message(ErrorCodes.INTERNAL_SERVER_ERROR), str(e))

class CompletedPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:
            merchant = get_merchant_from_user(request.user)
            if not merchant:
                return JSONResponseSender.send_error(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT, get_error_message(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT), "User is not a merchant")
            # payment_id = (
            #     Payment.objects.filter(order__merchant=merchant, status='captured').order_by('-created_at').values_list('payment_id', flat=True)
            # )
            payments = (
                Payment.objects.filter(order__merchant=merchant, status='captured').order_by('-created_at')
            )
            serializer = PaymentSerializer(payments, many=True)
            return JSONResponseSender.send_success(serializer.data, message='Payment completed successfully')
        except Exception as e:
            return JSONResponseSender.send_error(ErrorCodes.INTERNAL_SERVER_ERROR, get_error_message(ErrorCodes.INTERNAL_SERVER_ERROR), str(e))

class PaymentProcessView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):

        order_id = request.data.get('order_id')
        card_details = request.data.get('card_details', {})

        try:
            merchant = get_merchant_from_user(request.user)
            if not merchant:
                return JSONResponseSender.send_error(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT, get_error_message(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT), "User is not a merchant")

            order = Order.objects.get(order_id=order_id, merchant=merchant)
            payment, success = PaymentProcessor.process_payment(order, card_details)

            if not payment:
                return JSONResponseSender.send_error(
                    ErrorCodes.PAYMENT_INVALID_CARD,
                    message=get_error_message(ErrorCodes.PAYMENT_INVALID_CARD),
                    description='Invalid card details',
                )

            if success and payment.status=='captured':
                order.status = 'paid'

            elif success:
                order.status = 'created'
            else:
                order.status = 'failed'
            order.save()
            serializer = PaymentSerializer(payment)

            # if success:
            #     WebhookHandler.send_webhook(payment, merchant)

            return JSONResponseSender.send_success(
                data=serializer.data,
                message='Payment processed successfully',
            )
        except Order.DoesNotExist:
            return JSONResponseSender.send_error(
                ErrorCodes.ORDER_NOT_FOUND,
                message=get_error_message(ErrorCodes.ORDER_NOT_FOUND),
                description='Order not found',
            )
        except Exception as e:
            print(str(e))
            return JSONResponseSender.send_error(ErrorCodes.INTERNAL_SERVER_ERROR,get_error_message(ErrorCodes.INTERNAL_SERVER_ERROR),str(e))


class RefundProcessView(RateLimitedMixin,APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):

        try:
            merchant = get_merchant_from_user(request.user)
            if not merchant:
                return JSONResponseSender.send_error(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT, get_error_message(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT), "User is not a merchant")

            payment_id = request.data.get('payment_id')

            payment = Payment.objects.get(payment_id=payment_id, order__merchant=merchant)
            success = PaymentProcessor.process_refund(payment)
            if success:
                WebhookHandler.send_webhook(payment, merchant)
                return JSONResponseSender.send_success(
                    data={'status': 'refunded'},
                    message='Refund processed successfully',
                )
            return JSONResponseSender.send_error(
                ErrorCodes.REFUND_PROCESSING_FAILED,
                message=get_error_message(ErrorCodes.REFUND_PROCESSING_FAILED),
                description='Refund processing failed',
            )
        except Exception as e:
            return JSONResponseSender.send_error(
                ErrorCodes.REFUND_PAYMENT_NOT_FOUND,
                message=get_error_message(ErrorCodes.REFUND_PAYMENT_NOT_FOUND),
                description=str(e),
            )




class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]


    def get(self, request):
        try:
            merchant_id = request.query_params.get('merchant_id')

            if merchant_id:
                try:
                    merchant = Merchant.objects.get(id=merchant_id)
                except ValueError:
                    return JSONResponseSender.send_error(
                        ErrorCodes.STATS_INVALID_MERCHANT_ID,
                        message=get_error_message(ErrorCodes.STATS_INVALID_MERCHANT_ID),
                        description='Invalid merchant ID',
                    )
                except Merchant.DoesNotExist:
                    return JSONResponseSender.send_error(
                        ErrorCodes.STATS_MERCHANT_NOT_FOUND,
                        message=get_error_message(ErrorCodes.STATS_MERCHANT_NOT_FOUND),
                        description='Merchant not found',
                    )
                # Filter metrics by merchant_id
                total_orders = Order.objects.filter(merchant=merchant).count()
                total_successful_payments = Payment.objects.filter(
                    order__merchant=merchant, status__in=['captured', 'refunded']
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
                )
            # Common metrics (not merchant-specific)

            # total_merchants = Merchant.objects.count()
            # total_admins = User.objects.filter(is_staff=True).count()


        except Exception as e:
            return JSONResponseSender.send_error(
                ErrorCodes.STATS_RETRIEVAL_FAILED,
                message=get_error_message(ErrorCodes.STATS_RETRIEVAL_FAILED),
                description=str(e),
            )


class MerchantStatsView(APIView):
    permission_classes = [IsAuthenticated, IsMerchantUser]


    def get(self, request):
        try:
            merchant = get_merchant_from_user(request.user)
            if not merchant:
                return JSONResponseSender.send_error(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT,get_error_message(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT),'User is not a merchant')

            total_orders = Order.objects.filter(merchant=merchant).count()
            total_successful_payments = Payment.objects.filter(
                order__merchant=merchant, status='captured'
            ).count()

            total_revenue = Payment.objects.filter(order__merchant=merchant,status__in=['captured','refunded']).aggregate(total=Sum('merchant_payout'))['total'] or 0
            # total_revenue = Payment.objects.filter(order__merchant=merchant).aggregate(total=Sum('merchant_payout'))['total'] or 0
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
            return JSONResponseSender.send_error(ErrorCodes.STATS_RETRIEVAL_FAILED,get_error_message(ErrorCodes.STATS_RETRIEVAL_FAILED),str(e))