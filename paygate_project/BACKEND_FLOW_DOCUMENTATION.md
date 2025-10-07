# Payment Gateway Backend Flow Documentation

## 🎯 Overview
This document explains the backend flow of the Payment Gateway system for frontend developers and UI/UX designers. It covers all API endpoints, user roles, data flows, and business logic.

## 🏗️ System Architecture

### Core Components
1. **Authentication System** - JWT-based with refresh tokens
2. **User Management** - Admin and Merchant roles
3. **Payment Processing** - Order creation and payment handling
4. **Webhook System** - Notification system for payment events
5. **Analytics** - Statistics for admins and merchants

## 👥 User Roles & Permissions

### 1. Admin Users
- **Permissions**: Full system access, can create other admins
- **Access**: System-wide statistics, merchant management
- **Identification**: `is_staff=True` and `is_superuser=True`

### 2. Merchant Users
- **Permissions**: Create orders, process payments, view own statistics
- **Access**: Own orders, payments, and statistics only
- **Identification**: Has associated `Merchant` profile with `api_key`

## 🔐 Authentication Flow

### Registration Flow

#### Merchant Registration
```
POST /paygate/api/v1/auth/register/
```

**Frontend Flow:**
1. User fills registration form (email, name, password, webhook_url)
2. Backend creates User + Merchant profile
3. Auto-generates unique API key for merchant
4. Returns JWT tokens + user data
5. Sets HTTP-only refresh token cookie

**Response Format:**
```json
{
    "success": true,
    "message": "Merchant registered successfully",
    "data": {
        "access": "jwt_access_token",
        "api_key": "merchant_api_key",
        "email": "user@example.com",
        "name": "User Name",
        "role": "merchant"
    }
}
```

#### Admin Registration
```
POST /paygate/api/v1/auth/register-admin/
```
- **Restriction**: Only existing admins can create new admins
- **Same response format** but with `"role": "admin"`

### Login Flow
```
POST /paygate/api/v1/auth/token/
```

**Frontend Flow:**
1. User enters email/password
2. Backend validates credentials
3. Returns JWT tokens + user profile data
4. Sets refresh token in HTTP-only cookie

**UI Considerations:**
- Show different dashboards based on `role` field
- Store `api_key` for merchants (needed for payment operations)
- Handle rate limiting (5 requests per minute per IP)

### Token Management

#### Refresh Token
```
POST /paygate/api/v1/auth/refresh/
```
- **Automatic**: Reads refresh token from HTTP-only cookie
- **Frontend**: Should handle this automatically when access token expires

#### Logout
```
POST /paygate/api/v1/auth/logout/
```
- **Action**: Blacklists refresh token and clears cookie
- **Frontend**: Clear all stored user data

## 💳 Payment Processing Flow

### Step 1: Create Order
```
POST /paygate/api/v1/orders/
```

**Required Data:**
```json
{
    "amount": 100.00,
    "currency": "INR"  // Optional, defaults to INR
}
```

**Business Logic:**
- Only authenticated merchants can create orders
- Amount must be positive number
- Auto-generates unique `order_id` (UUID)
- Initial status: "created"

**Response:**
```json
{
    "success": true,
    "data": {
        "order_id": "unique-uuid",
        "amount": "100.00",
        "currency": "INR",
        "status": "created",
        "created_at": "2023-10-06T10:30:00Z"
    }
}
```

### Step 2: Process Payment
```
POST /paygate/api/v1/payments/
```

**Required Data:**
```json
{
    "order_id": "order-uuid-from-step-1",
    "card_details": {
        "card_number": "1234567890123456",
        "expiry": "12/25",
        "cvv": "123"
    }
}
```

**Backend Processing:**
1. **Validation**: Verify order belongs to merchant
2. **Card Processing**: Simulate payment (80% success rate)
3. **Payment Record**: Create payment with unique `payment_id`
4. **Order Status**: Update to "paid" or "failed"
5. **Webhook**: Send notification to merchant (if webhook_url configured)

**Success Response:**
```json
{
    "success": true,
    "data": {
        "payment_id": "payment-uuid",
        "order": "order-uuid",
        "amount": "100.00",
        "status": "authorized", // or "failed"
        "created_at": "2023-10-06T10:35:00Z"
    }
}
```

### Step 3: Refund Processing
```
POST /paygate/api/v1/refunds/
```

**Required Data:**
```json
{
    "payment_id": "payment-uuid"
}
```

**Business Logic:**
- Only authorized/captured payments can be refunded
- Updates payment status to "refunded"
- Sends webhook notification

## 📊 Analytics & Statistics

### Merchant Statistics
```
GET /paygate/api/v1/merchants/stats/
```

**Available to**: Authenticated merchants (own data only)

**Response:**
```json
{
    "success": true,
    "data": {
        "total_orders": 50,
        "successful_payments": 40,
        "successful_refunds": 5,
        "canceled_payments": 10
    }
}
```

### Admin Statistics
```
GET /paygate/api/v1/admin/stats/
```

**Available to**: Admin users only

**Global Statistics:**
```json
{
    "success": true,
    "data": {
        "total_merchants": 25,
        "total_admins": 3,
        "total_orders": 1000,
        "total_successful_payments": 800,
        "total_successful_refunds": 50,
        "total_canceled_payments": 200
    }
}
```

**Merchant-Specific Statistics:**
```
GET /paygate/api/v1/admin/stats/?merchant_id=123
```

## 🔄 Webhook System

### How Webhooks Work
1. **Trigger Events**: Payment authorized, failed, or refunded
2. **Payload**: Sent to merchant's registered `webhook_url`
3. **Retry Logic**: Currently mock (80% success rate)
4. **Logging**: All webhook attempts logged in `WebhookLog`

### Webhook Payload Format
```json
{
    "event": "payment.authorized", // or payment.failed, payment.refunded
    "payment_id": "payment-uuid",
    "order_id": "order-uuid",
    "amount": "100.00",
    "currency": "INR",
    "status": "authorized",
    "created_at": "2023-10-06T10:35:00Z"
}
```

## 🎨 UI/UX Guidelines

### Dashboard Design Considerations

#### Merchant Dashboard
- **Order Management**: Create new orders, view order history
- **Payment Tracking**: Real-time payment status updates
- **Statistics**: Visual charts for payment metrics
- **Webhook Configuration**: Form to set/update webhook URL

#### Admin Dashboard
- **System Overview**: Global statistics and metrics
- **Merchant Management**: View all merchants and their statistics
- **System Health**: Payment success rates, failed transactions

### Status Indicators

#### Order Statuses
- 🟡 **"created"** - Order created, awaiting payment
- 🟢 **"paid"** - Payment successful
- 🔴 **"failed"** - Payment failed

#### Payment Statuses
- 🟡 **"pending"** - Payment initiated
- 🟢 **"authorized"** - Payment successful
- 🟢 **"captured"** - Payment captured (same as authorized in this system)
- 🔄 **"refunded"** - Payment refunded
- 🔴 **"failed"** - Payment failed

### Error Handling

#### Common Error Responses
```json
{
    "success": false,
    "exception": {
        "code": 1001,
        "message": "Login failed",
        "description": "Invalid credentials",
        "meta": null
    }
}
```

#### Error Codes Reference
- **1001-1003**: Authentication errors
- **1008-1015**: Payment processing errors
- **1019-1020**: Statistics/Admin errors

### Rate Limiting
- **Limit**: 5 requests per minute per IP address
- **UI Behavior**: Show loading states, disable buttons temporarily
- **Error Handling**: Display "Too many requests" message

## 🔒 Security Features

### Data Protection
- **Password Hashing**: Django's built-in password hashing
- **Card Data**: Only store SHA256 hash, never plain card numbers
- **JWT Tokens**: Short-lived access tokens (15 min default)
- **Refresh Tokens**: HTTP-only cookies, 7-day expiry

### Soft Delete System
- **User Deletion**: Soft delete with `deleted` flag and `deleted_at` timestamp
- **Data Retention**: Deleted users excluded from normal queries
- **Recovery**: Admin can access deleted users via `all_with_deleted()`

## 📱 Frontend Integration Tips

### State Management
- **User State**: Store user role, email, name, api_key
- **Authentication**: Handle token refresh automatically
- **Payment Flow**: Track order_id through the payment process

### Real-time Updates
- **Payment Status**: Poll payment endpoint or implement WebSocket for real-time updates
- **Statistics**: Refresh dashboard data periodically

### Form Validation
- **Email**: Standard email validation
- **Amount**: Positive numbers only, decimal precision
- **Card Details**: Basic format validation (length, digits)

## 🧪 Testing Considerations

### Mock Payment Behavior
- **Success Rate**: 80% of payments succeed (random)
- **Card Validation**: Minimum 12 characters required
- **Webhook Success**: 80% webhook delivery success rate

### Test Data
- Use any email format for registration
- Card numbers: Any 12+ digit string works
- Amounts: Any positive decimal number

## 📋 API Endpoints Summary

| Method | Endpoint | Purpose | Auth Required | Role |
|--------|----------|---------|---------------|------|
| POST | `/paygate/api/v1/auth/register/` | Register merchant | No | - |
| POST | `/paygate/api/v1/auth/register-admin/` | Register admin | Yes | Admin |
| POST | `/paygate/api/v1/auth/token/` | Login | No | - |
| POST | `/paygate/api/v1/auth/refresh/` | Refresh token | No | - |
| POST | `/paygate/api/v1/auth/logout/` | Logout | Yes | Any |
| POST | `/paygate/api/v1/orders/` | Create order | Yes | Merchant |
| POST | `/paygate/api/v1/payments/` | Process payment | Yes | Merchant |
| POST | `/paygate/api/v1/refunds/` | Process refund | Yes | Merchant |
| GET | `/paygate/api/v1/merchants/stats/` | Merchant stats | Yes | Merchant |
| GET | `/paygate/api/v1/admin/stats/` | Admin stats | Yes | Admin |

## 🔧 Development Notes

### Database Models
- **User**: Custom user model with soft delete
- **Merchant**: One-to-one with User, has API key
- **Order**: Belongs to merchant, tracks payment orders
- **Payment**: Belongs to order, tracks payment attempts
- **WebhookLog**: Tracks webhook delivery attempts

### Key Features
- **UUID Primary Keys**: All IDs are UUIDs for security
- **Timezone Aware**: All timestamps include timezone info
- **Audit Trail**: Created/updated timestamps on all models
- **Extensible**: Easy to add new payment methods or currencies

This documentation should help your frontend and UI/UX teams understand the complete backend flow and build an intuitive user interface that aligns with the business logic and security requirements.