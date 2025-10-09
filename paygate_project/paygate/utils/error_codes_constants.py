"""
Error codes for Payment Gateway API
Organized by domain for easy maintenance and reference
"""


class ErrorCodes:
    """
    Error code structure: [Category][Sequence]
    
    1xxx = Authentication & Authorization (1000-1099)
    2xxx = Order Management (2000-2099)
    3xxx = Payment Processing (3000-3099)
    4xxx = Refund Processing (4000-4099)
    5xxx = Statistics & Reporting (5000-5099)
    9xxx = System/Server Errors (9000-9099)
    """
    
    # ========================================
    # 1xxx - Authentication & Authorization
    # ========================================
    
    # Login (1000-1009)
    LOGIN_FAILED = 1001
    LOGIN_ACCOUNT_DISABLED = 1002
    LOGIN_ACCOUNT_LOCKED = 1003
    
    # Registration (1010-1019)
    REGISTRATION_FAILED = 1010
    REGISTRATION_EMAIL_EXISTS = 1011
    REGISTRATION_INVALID_EMAIL = 1012
    
    # Admin Registration (1020-1029)
    ADMIN_REG_MISSING_DATA = 1020
    ADMIN_REG_FAILED = 1021
    
    # Token Management (1030-1039)
    TOKEN_REFRESH_NO_TOKEN = 1030
    TOKEN_REFRESH_INVALID = 1031
    TOKEN_REFRESH_EXPIRED = 1032
    
    # Logout (1040-1049)
    LOGOUT_NO_TOKEN = 1040
    LOGOUT_INVALID_TOKEN = 1041
    LOGOUT_SERVER_ERROR = 1042
    
    # Authorization (1050-1059)
    UNAUTHORIZED_NOT_MERCHANT = 1050
    UNAUTHORIZED_NOT_ADMIN = 1051
    FORBIDDEN_INSUFFICIENT_PERMISSIONS = 1052
    
    # ========================================
    # 2xxx - Order Management
    # ========================================
    
    # Order Creation (2000-2009)
    ORDER_MISSING_AMOUNT = 2001
    ORDER_INVALID_AMOUNT_FORMAT = 2002
    ORDER_AMOUNT_NOT_POSITIVE = 2003
    ORDER_MISSING_CURRENCY = 2004
    ORDER_INVALID_CURRENCY = 2005
    
    # Order Retrieval (2010-2019)
    ORDER_NOT_FOUND = 2010
    ORDER_NOT_FOUND_OR_UNAUTHORIZED = 2011
    
    # Order Operations (2020-2029)
    ORDER_RETRIEVAL_FAILED = 2020
    ORDER_UPDATE_FAILED = 2021
    
    # ========================================
    # 3xxx - Payment Processing
    # ========================================
    
    # Payment Failures (3000-3009)
    PAYMENT_INVALID_CARD = 3001
    PAYMENT_INSUFFICIENT_FUNDS = 3002
    PAYMENT_CARD_EXPIRED = 3003
    PAYMENT_CARD_DECLINED = 3004
    PAYMENT_PROCESSING_FAILED = 3005
    
    # Payment Retrieval (3010-3019)
    PAYMENT_NOT_FOUND = 3010
    PAYMENT_NOT_FOUND_OR_UNAUTHORIZED = 3011
    
    # Payment Capture (3020-3029)
    PAYMENT_CAPTURE_FAILED = 3020
    PAYMENT_ALREADY_CAPTURED = 3021
    PAYMENT_NOT_AUTHORIZED = 3022
    
    # Payment Void (3030-3039)
    PAYMENT_VOID_FAILED = 3030
    PAYMENT_ALREADY_VOIDED = 3031
    
    # Payment Operations (3040-3049)
    PAYMENT_RETRIEVAL_FAILED = 3040
    PAYMENT_UPDATE_FAILED = 3041
    
    # ========================================
    # 4xxx - Refund Processing
    # ========================================
    
    # Refund Validation (4000-4009)
    REFUND_NOT_CAPTURED = 4001
    REFUND_ALREADY_REFUNDED = 4002
    REFUND_INVALID_AMOUNT = 4003
    REFUND_PROCESSING_FAILED = 4004
    
    # Refund Retrieval (4010-4019)
    REFUND_PAYMENT_NOT_FOUND = 4010
    REFUND_PAYMENT_NOT_FOUND_OR_UNAUTHORIZED = 4011
    
    # ========================================
    # 5xxx - Statistics & Reporting
    # ========================================
    
    # Stats Operations (5000-5009)
    STATS_RETRIEVAL_FAILED = 5001
    STATS_CALCULATION_ERROR = 5002
    
    # Stats Validation (5010-5019)
    STATS_MERCHANT_NOT_FOUND = 5010
    STATS_INVALID_MERCHANT_ID = 5011
    STATS_INVALID_DATE_RANGE = 5012
    
    # ========================================
    # 9xxx - System/Server Errors
    # ========================================
    
    INTERNAL_SERVER_ERROR = 9000
    DATABASE_CONNECTION_ERROR = 9001
    EXTERNAL_SERVICE_UNAVAILABLE = 9002
    UNKNOWN_ERROR = 9099


# Human-readable messages for each error code
ERROR_MESSAGES = {
    # Authentication & Authorization
    ErrorCodes.LOGIN_FAILED: "Login failed",
    ErrorCodes.LOGIN_ACCOUNT_DISABLED: "Account is disabled",
    ErrorCodes.LOGIN_ACCOUNT_LOCKED: "Account is locked",
    
    ErrorCodes.REGISTRATION_FAILED: "Registration failed",
    ErrorCodes.REGISTRATION_EMAIL_EXISTS: "Email already exists",
    ErrorCodes.REGISTRATION_INVALID_EMAIL: "Invalid email format",
    
    ErrorCodes.ADMIN_REG_MISSING_DATA: "Admin registration - missing user data",
    ErrorCodes.ADMIN_REG_FAILED: "Admin registration failed",
    
    ErrorCodes.TOKEN_REFRESH_NO_TOKEN: "No refresh token provided",
    ErrorCodes.TOKEN_REFRESH_INVALID: "Invalid refresh token",
    ErrorCodes.TOKEN_REFRESH_EXPIRED: "Refresh token expired",
    
    ErrorCodes.LOGOUT_NO_TOKEN: "No refresh token provided",
    ErrorCodes.LOGOUT_INVALID_TOKEN: "Invalid refresh token",
    ErrorCodes.LOGOUT_SERVER_ERROR: "Logout failed - server error",
    
    ErrorCodes.UNAUTHORIZED_NOT_MERCHANT: "User is not a merchant",
    ErrorCodes.UNAUTHORIZED_NOT_ADMIN: "User is not an admin",
    ErrorCodes.FORBIDDEN_INSUFFICIENT_PERMISSIONS: "Insufficient permissions",
    
    # Order Management
    ErrorCodes.ORDER_MISSING_AMOUNT: "Amount is required",
    ErrorCodes.ORDER_INVALID_AMOUNT_FORMAT: "Invalid amount format",
    ErrorCodes.ORDER_AMOUNT_NOT_POSITIVE: "Amount must be positive",
    ErrorCodes.ORDER_MISSING_CURRENCY: "Currency is required",
    ErrorCodes.ORDER_INVALID_CURRENCY: "Invalid currency code",
    
    ErrorCodes.ORDER_NOT_FOUND: "Order not found",
    ErrorCodes.ORDER_NOT_FOUND_OR_UNAUTHORIZED: "Order not found",
    
    ErrorCodes.ORDER_RETRIEVAL_FAILED: "Failed to retrieve orders",
    ErrorCodes.ORDER_UPDATE_FAILED: "Failed to update order",
    
    # Payment Processing
    ErrorCodes.PAYMENT_INVALID_CARD: "Invalid card details",
    ErrorCodes.PAYMENT_INSUFFICIENT_FUNDS: "Insufficient funds",
    ErrorCodes.PAYMENT_CARD_EXPIRED: "Card has expired",
    ErrorCodes.PAYMENT_CARD_DECLINED: "Card was declined",
    ErrorCodes.PAYMENT_PROCESSING_FAILED: "Payment processing failed",
    
    ErrorCodes.PAYMENT_NOT_FOUND: "Payment not found",
    ErrorCodes.PAYMENT_NOT_FOUND_OR_UNAUTHORIZED: "Payment not found",
    
    ErrorCodes.PAYMENT_CAPTURE_FAILED: "Payment capture failed",
    ErrorCodes.PAYMENT_ALREADY_CAPTURED: "Payment already captured",
    ErrorCodes.PAYMENT_NOT_AUTHORIZED: "Payment not authorized",
    
    ErrorCodes.PAYMENT_VOID_FAILED: "Payment void failed",
    ErrorCodes.PAYMENT_ALREADY_VOIDED: "Payment already voided",
    
    ErrorCodes.PAYMENT_RETRIEVAL_FAILED: "Failed to retrieve payment",
    ErrorCodes.PAYMENT_UPDATE_FAILED: "Failed to update payment",
    
    # Refund Processing
    ErrorCodes.REFUND_NOT_CAPTURED: "Only captured payments can be refunded",
    ErrorCodes.REFUND_ALREADY_REFUNDED: "Payment already refunded",
    ErrorCodes.REFUND_INVALID_AMOUNT: "Invalid refund amount",
    ErrorCodes.REFUND_PROCESSING_FAILED: "Refund processing failed",
    
    ErrorCodes.REFUND_PAYMENT_NOT_FOUND: "Payment not found for refund",
    ErrorCodes.REFUND_PAYMENT_NOT_FOUND_OR_UNAUTHORIZED: "Payment not found",
    
    # Statistics & Reporting
    ErrorCodes.STATS_RETRIEVAL_FAILED: "Failed to retrieve statistics",
    ErrorCodes.STATS_CALCULATION_ERROR: "Error calculating statistics",
    
    ErrorCodes.STATS_MERCHANT_NOT_FOUND: "Merchant not found",
    ErrorCodes.STATS_INVALID_MERCHANT_ID: "Invalid merchant ID",
    ErrorCodes.STATS_INVALID_DATE_RANGE: "Invalid date range",
    
    # System Errors
    ErrorCodes.INTERNAL_SERVER_ERROR: "Internal server error",
    ErrorCodes.DATABASE_CONNECTION_ERROR: "Database connection error",
    ErrorCodes.EXTERNAL_SERVICE_UNAVAILABLE: "External service unavailable",
    ErrorCodes.UNKNOWN_ERROR: "Unknown error occurred",
}


def get_error_message(code):
    """Get human-readable message for an error code."""
    return ERROR_MESSAGES.get(code, "Unknown error")


# Usage example:
"""
from .error_codes import ErrorCodes, get_error_message

# In your views:
return JSONResponseSender.send_error(
    code=ErrorCodes.ORDER_MISSING_AMOUNT,
    message=get_error_message(ErrorCodes.ORDER_MISSING_AMOUNT),
    description='Amount field is required for order creation',
    status=400
)
"""
