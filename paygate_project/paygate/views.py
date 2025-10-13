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
from django.utils import timezone
from django.db.models.functions import TruncDate
import  requests
from datetime import timedelta
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




# class AdminStatsView(APIView):
#     permission_classes = [IsAdminUser]
#
#
#     def get(self, request):
#         try:
#             merchant_id = request.query_params.get('merchant_id')
#
#             if merchant_id:
#                 try:
#                     merchant = Merchant.objects.get(id=merchant_id)
#                 except ValueError:
#                     return JSONResponseSender.send_error(
#                         ErrorCodes.STATS_INVALID_MERCHANT_ID,
#                         message=get_error_message(ErrorCodes.STATS_INVALID_MERCHANT_ID),
#                         description='Invalid merchant ID',
#                     )
#                 except Merchant.DoesNotExist:
#                     return JSONResponseSender.send_error(
#                         ErrorCodes.STATS_MERCHANT_NOT_FOUND,
#                         message=get_error_message(ErrorCodes.STATS_MERCHANT_NOT_FOUND),
#                         description='Merchant not found',
#                     )
#                 # Filter metrics by merchant_id
#                 total_orders = Order.objects.filter(merchant=merchant).count()
#                 total_successful_payments = Payment.objects.filter(
#                     order__merchant=merchant, status__in=['captured', 'refunded']
#                 ).count()
#                 total_captured_payments = Payment.objects.filter(
#                     order__merchant=merchant, status='captured'
#                 ).count()
#                 total_authorized_payments = Payment.objects.filter(
#                     order__merchant=merchant, status='authorized'
#                 ).count()
#                 total_successful_refunds = Payment.objects.filter(
#                     order__merchant=merchant, status='refunded'
#                 ).count()
#                 total_canceled_payments = Payment.objects.filter(
#                     order__merchant=merchant, status='failed'
#                 ).count()
#
#                 return JSONResponseSender.send_success(
#                     data={
#                         'user__email': merchant.user.email,
#                         'order_count': total_orders,
#                         'payment_count': total_successful_payments,
#                         'successful_payments': total_successful_payments,
#                         'authorized_payments': total_authorized_payments,
#                         'captured_payments': total_captured_payments,
#                         'successful_refunds': total_successful_refunds,
#                         'canceled_payments': total_canceled_payments
#                     }
#                 )
#             else:
#                 total_merchants = Merchant.objects.count()
#                 total_admins = User.objects.filter(is_staff=True).count()
#                 total_commission = Payment.objects.aggregate(total=Sum('commission_amount'))['total'] or 0
#                 total_orders = Order.objects.count()
#                 total_successful_payments = Payment.objects.filter(status__in=['captured','refunded']).count()
#                 total_captured_payments = Payment.objects.filter(status='captured').count()
#                 total_authorized_payments = Payment.objects.filter(status='authorized').count()
#                 total_successful_refunds = Payment.objects.filter(status='refunded').count()
#                 total_canceled_payments = Payment.objects.filter(status='failed').count()
#                 return JSONResponseSender.send_success(
#                     data={
#                         'total_merchants': total_merchants,
#                         'total_admins': total_admins,
#                         'total_orders': total_orders,
#                         'total_commission': total_commission,
#                         'total_successful_payments': total_successful_payments,
#                         'total_authorized_payments': total_authorized_payments,
#                         'total_captured_payments': total_captured_payments,
#                         'total_successful_refunds': total_successful_refunds,
#                         'total_canceled_payments': total_canceled_payments,
#                     },
#                     message='Admin statistics retrieved successfully',
#                 )
#             # Common metrics (not merchant-specific)
#
#             # total_merchants = Merchant.objects.count()
#             # total_admins = User.objects.filter(is_staff=True).count()
#
#
#         except Exception as e:
#             return JSONResponseSender.send_error(
#                 ErrorCodes.STATS_RETRIEVAL_FAILED,
#                 message=get_error_message(ErrorCodes.STATS_RETRIEVAL_FAILED),
#                 description=str(e),
#             )


# class MerchantStatsView(APIView):
#     permission_classes = [IsAuthenticated, IsMerchantUser]
#     days = int(requests.GET.get('days', 30))
#     start_date = timezone.now() - timedelta(days=days)
#
#     def get(self, request):
#         try:
#             merchant = get_merchant_from_user(request.user)
#             if not merchant:
#                 return JSONResponseSender.send_error(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT,get_error_message(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT),'User is not a merchant')
#
#             total_orders = Order.objects.filter(merchant=merchant).count()
#             total_successful_payments = Payment.objects.filter(
#                 order__merchant=merchant, status='captured'
#             ).count()
#
#             total_revenue = Payment.objects.filter(order__merchant=merchant,status__in=['captured','refunded']).aggregate(total=Sum('merchant_payout'))['total'] or 0
#             # total_revenue = Payment.objects.filter(order__merchant=merchant).aggregate(total=Sum('merchant_payout'))['total'] or 0
#             total_successful_refunds = Payment.objects.filter(
#                 order__merchant=merchant, status='refunded'
#             ).count()
#             total_canceled_payments = Payment.objects.filter(
#                 order__merchant=merchant, status='failed'
#             ).count()
#             total_authorized_payments = Payment.objects.filter(order__merchant=merchant, status='authorized').count()
#
#             return JSONResponseSender.send_success(
#                 data={
#                     'total_orders': total_orders,
#                     'total_revenue': total_revenue,
#                     'successful_payments': total_successful_payments,
#                     'successful_refunds': total_successful_refunds,
#                     'canceled_payments': total_canceled_payments,
#                     'authorized_payments': total_authorized_payments,
#                 }
#             )
#         except Exception as e:
#             return JSONResponseSender.send_error(ErrorCodes.STATS_RETRIEVAL_FAILED,get_error_message(ErrorCodes.STATS_RETRIEVAL_FAILED),str(e))


class MerchantStatsView(APIView):
    permission_classes = [IsAuthenticated, IsMerchantUser]

    def get(self, request):
        try:
            merchant = get_merchant_from_user(request.user)
            if not merchant:
                return JSONResponseSender.send_error(
                    ErrorCodes.UNAUTHORIZED_NOT_MERCHANT,
                    get_error_message(ErrorCodes.UNAUTHORIZED_NOT_MERCHANT),
                    'User is not a merchant'
                )

            # Get date range parameter (default: last 30 days)
            days = int(request.GET.get('days', 30))
            current_period_start = timezone.now() - timedelta(days=days)
            previous_period_start = timezone.now() - timedelta(days=days * 2)
            previous_period_end = current_period_start

            # CURRENT PERIOD STATS
            total_orders = Order.objects.filter(
                merchant=merchant,
                created_at__gte=current_period_start
            ).count()

            total_successful_payments = Payment.objects.filter(
                order__merchant=merchant,
                status='captured',
                created_at__gte=current_period_start
            ).count()

            total_revenue = Payment.objects.filter(
                order__merchant=merchant,
                status__in=['captured', 'refunded'],
                created_at__gte=current_period_start
            ).aggregate(total=Sum('merchant_payout'))['total'] or 0

            total_successful_refunds = Payment.objects.filter(
                order__merchant=merchant,
                status='refunded',
                created_at__gte=current_period_start
            ).count()

            total_canceled_payments = Payment.objects.filter(
                order__merchant=merchant,
                status='failed',
                created_at__gte=current_period_start
            ).count()

            total_authorized_payments = Payment.objects.filter(
                order__merchant=merchant,
                status='authorized',
                created_at__gte=current_period_start
            ).count()

            # PREVIOUS PERIOD STATS (for trend calculation)
            prev_total_orders = Order.objects.filter(
                merchant=merchant,
                created_at__gte=previous_period_start,
                created_at__lt=previous_period_end
            ).count()

            prev_total_revenue = Payment.objects.filter(
                order__merchant=merchant,
                status__in=['captured', 'refunded'],
                created_at__gte=previous_period_start,
                created_at__lt=previous_period_end
            ).aggregate(total=Sum('merchant_payout'))['total'] or 0

            prev_total_successful_payments = Payment.objects.filter(
                order__merchant=merchant,
                status='captured',
                created_at__gte=previous_period_start,
                created_at__lt=previous_period_end
            ).count()

            prev_total_payments = Payment.objects.filter(
                order__merchant=merchant,
                created_at__gte=previous_period_start,
                created_at__lt=previous_period_end
            ).count()

            prev_conversion_rate = (
                (prev_total_successful_payments / prev_total_payments * 100)
                if prev_total_payments > 0 else 0
            )

            prev_avg_order_value = (
                prev_total_revenue / prev_total_successful_payments
                if prev_total_successful_payments > 0 else 0
            )

            # Time-series data for charts
            daily_revenue = Payment.objects.filter(
                order__merchant=merchant,
                status='captured',
                created_at__gte=current_period_start
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                revenue=Sum('merchant_payout'),
                count=Count('id')
            ).order_by('date')

            daily_orders = Order.objects.filter(
                merchant=merchant,
                created_at__gte=current_period_start
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            # Payment status breakdown (for pie chart)
            payment_status_breakdown = Payment.objects.filter(
                order__merchant=merchant,
                created_at__gte=current_period_start
            ).values('status').annotate(
                count=Count('id')
            ).order_by('-count')

            # Calculate conversion rate
            total_payments = Payment.objects.filter(
                order__merchant=merchant,
                created_at__gte=current_period_start
            ).count()
            conversion_rate = (
                (total_successful_payments / total_payments * 100)
                if total_payments > 0 else 0
            )

            # Average order value
            avg_order_value = (
                total_revenue / total_successful_payments
                if total_successful_payments > 0 else 0
            )

            return JSONResponseSender.send_success(
                data={
                    # Summary stats
                    'total_orders': total_orders,
                    'total_revenue': str(total_revenue),
                    'successful_payments': total_successful_payments,
                    'successful_refunds': total_successful_refunds,
                    'canceled_payments': total_canceled_payments,
                    'authorized_payments': total_authorized_payments,
                    'conversion_rate': round(conversion_rate, 2),
                    'avg_order_value': str(round(avg_order_value, 2)),

                    # Previous period for trend calculation
                    'previous_period': {
                        'total_revenue': str(prev_total_revenue),
                        'total_orders': prev_total_orders,
                        'conversion_rate': round(prev_conversion_rate, 2),
                        'avg_order_value': str(round(prev_avg_order_value, 2)),
                    },

                    # Time-series data
                    'daily_revenue': [
                        {
                            'date': item['date'].strftime('%Y-%m-%d'),
                            'revenue': str(item['revenue']),
                            'count': item['count']
                        }
                        for item in daily_revenue
                    ],
                    'daily_orders': [
                        {
                            'date': item['date'].strftime('%Y-%m-%d'),
                            'count': item['count']
                        }
                        for item in daily_orders
                    ],

                    # Payment breakdown
                    'payment_status_breakdown': [
                        {
                            'status': item['status'],
                            'count': item['count']
                        }
                        for item in payment_status_breakdown
                    ]
                }
            )
        except Exception as e:
            return JSONResponseSender.send_error(
                ErrorCodes.STATS_RETRIEVAL_FAILED,
                get_error_message(ErrorCodes.STATS_RETRIEVAL_FAILED),
                str(e)
            )


class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            merchant_id = request.query_params.get('merchant_id')
            days = int(request.GET.get('days', 30))
            current_period_start = timezone.now() - timedelta(days=days)
            previous_period_start = timezone.now() - timedelta(days=days * 2)
            previous_period_end = current_period_start

            if merchant_id:
                # Merchant-specific stats (can be expanded as needed)
                try:
                    merchant = Merchant.objects.get(id=merchant_id)
                except (ValueError, Merchant.DoesNotExist):
                    return JSONResponseSender.send_error(
                        ErrorCodes.STATS_MERCHANT_NOT_FOUND,
                        message=get_error_message(ErrorCodes.STATS_MERCHANT_NOT_FOUND),
                        description='Merchant not found',
                    )

                # Placeholder for merchant-specific stats
                # TODO: implement similar to platform-wide stats

            else:
                # PLATFORM-WIDE CURRENT PERIOD
                total_merchants = Merchant.objects.filter(
                    created_at__gte=current_period_start
                ).count()
                total_admins = User.objects.filter(is_staff=True).count()
                total_commission = Payment.objects.filter(
                    status__in=['captured', 'refunded'],
                    created_at__gte=current_period_start
                ).aggregate(total=Sum('commission_amount'))['total'] or 0

                total_orders = Order.objects.filter(
                    created_at__gte=current_period_start
                ).count()

                total_successful_payments = Payment.objects.filter(
                    status__in=['captured', 'refunded'],
                    created_at__gte=current_period_start
                ).count()

                total_captured_payments = Payment.objects.filter(
                    status='captured',
                    created_at__gte=current_period_start
                ).count()

                total_successful_refunds = Payment.objects.filter(
                    status='refunded',
                    created_at__gte=current_period_start
                ).count()

                total_canceled_payments = Payment.objects.filter(
                    status='failed',
                    created_at__gte=current_period_start
                ).count()

                total_authorized_payments = Payment.objects.filter(
                    status='authorized',
                    created_at__gte=current_period_start
                ).count()

                # Conversion rate
                total_payments = Payment.objects.filter(
                    created_at__gte=current_period_start
                ).count()
                conversion_rate = (
                    (total_captured_payments / total_payments * 100)
                    if total_payments > 0 else 0
                )

                # Average commission per order
                avg_commission_per_order = (
                    total_commission / total_orders if total_orders > 0 else 0
                )

                # PREVIOUS PERIOD for trends
                prev_total_merchants = Merchant.objects.filter(
                    created_at__gte=previous_period_start,
                    created_at__lt=previous_period_end
                ).count()

                prev_total_commission = Payment.objects.filter(
                    status__in=['captured', 'refunded'],
                    created_at__gte=previous_period_start,
                    created_at__lt=previous_period_end
                ).aggregate(total=Sum('commission_amount'))['total'] or 0

                prev_total_orders = Order.objects.filter(
                    created_at__gte=previous_period_start,
                    created_at__lt=previous_period_end
                ).count()

                prev_total_payments = Payment.objects.filter(
                    created_at__gte=previous_period_start,
                    created_at__lt=previous_period_end
                ).count()

                prev_total_captured = Payment.objects.filter(
                    status='captured',
                    created_at__gte=previous_period_start,
                    created_at__lt=previous_period_end
                ).count()

                prev_conversion_rate = (
                    (prev_total_captured / prev_total_payments * 100)
                    if prev_total_payments > 0 else 0
                )

                prev_avg_commission_per_order = (
                    prev_total_commission / prev_total_orders if prev_total_orders > 0 else 0
                )

                # DAILY DATA
                daily_commission = Payment.objects.filter(
                    status='captured',
                    created_at__gte=current_period_start
                ).annotate(
                    date=TruncDate('created_at')
                ).values('date').annotate(
                    commission=Sum('commission_amount'),
                    count=Count('id')
                ).order_by('date')

                daily_orders = Order.objects.filter(
                    created_at__gte=current_period_start
                ).annotate(
                    date=TruncDate('created_at')
                ).values('date').annotate(count=Count('id')).order_by('date')

                daily_merchants = Merchant.objects.filter(
                    created_at__gte=current_period_start
                ).annotate(
                    date=TruncDate('created_at')
                ).values('date').annotate(count=Count('id')).order_by('date')

                # PAYMENT STATUS BREAKDOWN
                payment_status_breakdown = Payment.objects.filter(
                    created_at__gte=current_period_start
                ).values('status').annotate(count=Count('id'))

                # TOP MERCHANTS BY COMMISSION
                top_merchants = Payment.objects.filter(
                    status__in=['captured', 'refunded'],
                    created_at__gte=current_period_start
                ).values(
                    'order__merchant__user__email',
                    'order__merchant__user__name'
                ).annotate(
                    total_commission=Sum('commission_amount'),
                    order_count=Count('id')
                ).order_by('-total_commission')[:10]

                return JSONResponseSender.send_success(
                    data={
                        # Summary stats
                        'total_merchants': total_merchants,
                        'total_admins': total_admins,
                        'total_orders': total_orders,
                        'total_commission': str(total_commission),
                        'total_successful_payments': total_successful_payments,
                        'total_successful_refunds': total_successful_refunds,
                        'total_captured_payments': total_captured_payments,
                        'conversion_rate': round(conversion_rate, 2),
                        'total_canceled_payments': total_canceled_payments,
                        'total_authorized_payments': total_authorized_payments,
                        'avg_commission_per_order': str(round(avg_commission_per_order, 2)),

                        # Previous period
                        'previous_period': {
                            'total_commission': str(prev_total_commission),
                            'total_orders': prev_total_orders,
                            'conversion_rate': round(prev_conversion_rate, 2),
                            'total_merchants': prev_total_merchants,
                            'avg_commission_per_order': str(round(prev_avg_commission_per_order, 2))
                        },

                        # Time-series
                        'daily_commission': [
                            {'date': item['date'].strftime('%Y-%m-%d'),
                             'commission': str(item['commission']),
                             'count': item['count']}
                            for item in daily_commission
                        ],
                        'daily_orders': [
                            {'date': item['date'].strftime('%Y-%m-%d'),
                             'count': item['count']}
                            for item in daily_orders
                        ],
                        'daily_merchants': [
                            {'date': item['date'].strftime('%Y-%m-%d'),
                             'count': item['count']}
                            for item in daily_merchants
                        ],

                        'payment_status_breakdown': [
                            {'status': item['status'], 'count': item['count']}
                            for item in payment_status_breakdown
                        ],

                        'top_merchants': [
                            {
                                'email': item['order__merchant__user__email'],
                                'business_name': item['order__merchant__user__name'],
                                'total_commission': str(item['total_commission']),
                                'order_count': item['order_count']
                            }
                            for item in top_merchants
                        ],
                    },
                    message='Admin statistics retrieved successfully',
                )

        except Exception as e:
            return JSONResponseSender.send_error(
                ErrorCodes.STATS_RETRIEVAL_FAILED,
                message=get_error_message(ErrorCodes.STATS_RETRIEVAL_FAILED),
                description=str(e),
            )
