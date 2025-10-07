# 📊 Merchant Transaction History System

## 🎯 **Overview**
This document outlines the comprehensive transaction history that merchants can access through your payment gateway dashboard and APIs.

---

## 📋 **Current Data Available (Based on Your Models)**

### **1. Orders History**
```python
# Available from Order model
- order_id: "order-a1b2c3d4-e5f6-7890-ab12-cd34ef567890"
- merchant: TechMart
- amount: ₹75,000.00
- currency: "INR"
- status: "created", "paid", "failed"
- created_at: "2024-01-15T10:30:00Z"
```

### **2. Payments History**
```python
# Available from Payment model
- payment_id: "pay-b2c3d4e5-f6g7-8901-bc23-de45fg678901"
- order: linked to order_id
- amount: ₹75,000.00
- status: "pending", "authorized", "captured", "failed", "refunded"
- card_hash: "a8f5f167f44f4964e6c998dee827110c" (last 4 digits for display)
- created_at: "2024-01-15T10:35:00Z"
```

### **3. Webhook Activity History**
```python
# Available from WebhookLog model
- payment: linked to payment_id
- payload: JSON data sent to merchant
- status: "sent", "failed"
- response: merchant's response
- created_at: "2024-01-15T10:35:30Z"
```

---

## 🏪 **Transaction History API Endpoints (To Implement)**

### **1. All Transactions Overview**
```http
GET /paygate/api/v1/merchants/transactions/
Authorization: Bearer merchant_jwt_token
```

**Response:**
```json
{
    "success": true,
    "data": {
        "transactions": [
            {
                "transaction_id": "txn-001",
                "order_id": "order-a1b2c3d4-e5f6-7890-ab12-cd34ef567890",
                "payment_id": "pay-b2c3d4e5-f6g7-8901-bc23-de45fg678901",
                "type": "payment",
                "amount": "75000.00",
                "currency": "INR",
                "status": "authorized",
                "customer_card": "**** **** **** 9012",
                "gateway_fee": "1500.00",
                "net_amount": "73500.00",
                "created_at": "2024-01-15T10:35:00Z",
                "updated_at": "2024-01-15T10:35:00Z"
            },
            {
                "transaction_id": "txn-002",
                "order_id": "order-c2d3e4f5-g6h7-8901-cd23-ef45gh789012",
                "payment_id": "pay-d3e4f5g6-h7i8-9012-de34-fg56hi890123",
                "type": "refund",
                "amount": "-25000.00",
                "currency": "INR",
                "status": "refunded",
                "customer_card": "**** **** **** 5678",
                "gateway_fee": "-500.00",
                "net_amount": "-24500.00",
                "created_at": "2024-01-15T14:20:00Z",
                "refund_reason": "Customer return"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 25,
            "total": 156,
            "total_pages": 7
        }
    }
}
```

### **2. Transaction Details by ID**
```http
GET /paygate/api/v1/merchants/transactions/{transaction_id}/
```

**Response:**
```json
{
    "success": true,
    "data": {
        "transaction_id": "txn-001",
        "order_details": {
            "order_id": "order-a1b2c3d4-e5f6-7890-ab12-cd34ef567890",
            "created_at": "2024-01-15T10:30:00Z",
            "status": "paid"
        },
        "payment_details": {
            "payment_id": "pay-b2c3d4e5-f6g7-8901-bc23-de45fg678901",
            "method": "card",
            "card_brand": "visa",
            "card_last4": "9012",
            "card_exp_month": "12",
            "card_exp_year": "25",
            "status": "authorized",
            "amount": "75000.00",
            "currency": "INR",
            "processed_at": "2024-01-15T10:35:00Z"
        },
        "fee_details": {
            "gateway_fee": "1500.00",
            "gateway_fee_percent": "2.00",
            "net_amount": "73500.00"
        },
        "webhook_status": {
            "attempted": true,
            "delivered": true,
            "attempts": 1,
            "last_attempt": "2024-01-15T10:35:30Z",
            "response_code": 200
        }
    }
}
```

### **3. Filtered Transaction History**
```http
GET /paygate/api/v1/merchants/transactions/?status=authorized&date_from=2024-01-01&date_to=2024-01-31&limit=50
```

### **4. Transaction Summary/Analytics**
```http
GET /paygate/api/v1/merchants/transactions/summary/
```

**Response:**
```json
{
    "success": true,
    "data": {
        "period": {
            "from": "2024-01-01T00:00:00Z",
            "to": "2024-01-31T23:59:59Z"
        },
        "totals": {
            "total_transactions": 156,
            "successful_payments": 124,
            "failed_payments": 20,
            "refunds": 12,
            "gross_amount": "1247500.00",
            "total_fees": "24950.00",
            "net_amount": "1222550.00"
        },
        "daily_breakdown": [
            {
                "date": "2024-01-15",
                "transactions": 8,
                "amount": "125000.00",
                "fees": "2500.00"
            }
        ]
    }
}
```

---

## 📊 **Transaction History Dashboard Views**

### **1. Main Transaction List View**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TechMart - Transaction History                   │
├─────────────────────────────────────────────────────────────────────┤
│ Filter: [All Types ▼] [Last 30 days ▼] [Search: Order ID...    ] 🔍 │
├─────────────────────────────────────────────────────────────────────┤
│ Date       │ Order ID      │ Type    │ Amount    │ Status     │ Action│
├─────────────────────────────────────────────────────────────────────┤
│ 15/01/2024 │ order-a1b2... │ Payment │ ₹75,000   │ ✅ Success │ [View]│
│ 15/01/2024 │ order-c2d3... │ Refund  │ -₹25,000  │ ✅ Success │ [View]│
│ 14/01/2024 │ order-e4f5... │ Payment │ ₹12,500   │ ❌ Failed  │ [View]│
│ 14/01/2024 │ order-g6h7... │ Payment │ ₹89,000   │ ✅ Success │ [View]│
└─────────────────────────────────────────────────────────────────────┘
```

### **2. Transaction Detail View**

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Transaction Details                            │
├─────────────────────────────────────────────────────────────────────┤
│ Transaction ID: txn-001                                             │
│ Order ID: order-a1b2c3d4-e5f6-7890-ab12-cd34ef567890              │
│ Payment ID: pay-b2c3d4e5-f6g7-8901-bc23-de45fg678901              │
├─────────────────────────────────────────────────────────────────────┤
│ 💳 PAYMENT DETAILS                                                 │
│   Amount: ₹75,000.00 INR                                           │
│   Card: **** **** **** 9012 (Visa)                                │
│   Status: ✅ Authorized                                            │
│   Processed: 15/01/2024 at 10:35 AM                               │
├─────────────────────────────────────────────────────────────────────┤
│ 💰 FEE BREAKDOWN                                                   │
│   Gross Amount: ₹75,000.00                                         │
│   Gateway Fee (2%): ₹1,500.00                                      │
│   Net Amount: ₹73,500.00                                           │
├─────────────────────────────────────────────────────────────────────┤
│ 🔔 WEBHOOK STATUS                                                  │
│   Status: ✅ Delivered                                             │
│   Attempts: 1                                                      │
│   Response: 200 OK                                                 │
│   Delivered At: 15/01/2024 at 10:35 AM                            │
└─────────────────────────────────────────────────────────────────────┘
```

### **3. Analytics Dashboard View**

```
┌─────────────────────────────────────────────────────────────────────┐
│                        This Month Summary                           │
├─────────────────────────────────────────────────────────────────────┤
│ 📊 OVERVIEW                                                         │
│   Total Transactions: 156                                          │
│   Success Rate: 89.7% (140/156)                                    │
│   Total Volume: ₹12,47,500                                          │
│   Net Revenue: ₹12,22,550 (after ₹24,950 fees)                     │
├─────────────────────────────────────────────────────────────────────┤
│ 📈 TRANSACTION BREAKDOWN                                            │
│   ✅ Successful Payments: 124 (₹11,85,000)                         │
│   ❌ Failed Payments: 20 (₹1,87,500 attempted)                     │
│   🔄 Refunds: 12 (₹62,500)                                         │
├─────────────────────────────────────────────────────────────────────┤
│ 📅 DAILY CHART                                                     │
│   [===▓▓▓▓▓▓▓===] Transaction Volume Graph                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 **Key Transaction Data Points for Merchants**

### **Essential Information:**
1. **Transaction Identification**
   - Transaction ID, Order ID, Payment ID
   - Timestamp (created, processed, updated)

2. **Financial Details**
   - Amount (gross, fees, net)
   - Currency
   - Fee breakdown (percentage + fixed)

3. **Payment Information**
   - Payment method (card, wallet, etc.)
   - Card details (masked): **** **** **** 1234
   - Payment status and lifecycle

4. **Customer Data** (Privacy-Safe)
   - Card brand (Visa, Mastercard)
   - Last 4 digits of card
   - Payment country/region

5. **Processing Details**
   - Success/failure reasons
   - Processing time
   - Gateway response codes

6. **Webhook Information**
   - Delivery status
   - Retry attempts
   - Response codes from merchant's server

### **Advanced Analytics:**
1. **Time-based Trends**
   - Daily/weekly/monthly volumes
   - Success rate trends
   - Peak transaction hours

2. **Payment Method Analysis**
   - Breakdown by card types
   - Success rates by payment method
   - Geographic distribution

3. **Business Intelligence**
   - Average transaction value
   - Customer payment patterns
   - Refund rates and reasons

---

## 🔍 **Search and Filter Options**

### **Filter Categories:**
```python
# Transaction Status
- All Transactions
- Successful Payments
- Failed Payments  
- Pending Payments
- Refunds
- Chargebacks

# Date Ranges
- Today
- Last 7 days
- Last 30 days
- Last 90 days
- This Month
- Last Month
- Custom Date Range

# Amount Ranges
- Under ₹1,000
- ₹1,000 - ₹10,000
- ₹10,000 - ₹1,00,000
- Above ₹1,00,000
- Custom Amount Range

# Payment Methods
- All Cards
- Visa
- Mastercard
- Debit Cards
- Credit Cards
```

### **Search Options:**
- Order ID
- Payment ID  
- Transaction ID
- Customer card last 4 digits
- Amount (exact or range)

---

## 📤 **Export and Reporting**

### **Export Formats:**
1. **CSV Export** - For accounting systems
2. **PDF Reports** - For business records
3. **Excel Format** - For analysis
4. **API Export** - For system integration

### **Report Types:**
1. **Transaction Report** - All transaction details
2. **Settlement Report** - Net amounts and fees
3. **Tax Report** - For GST/tax compliance
4. **Reconciliation Report** - For bank matching

---

## 🔔 **Real-time Notifications**

### **Dashboard Alerts:**
- New successful payments
- Failed payment attempts
- Refund requests
- Webhook delivery failures
- Unusual transaction patterns

### **Email Reports:**
- Daily transaction summary
- Weekly performance report
- Monthly settlement statement
- Failed webhook notifications

---

## 🎯 **Business Value for Merchants**

### **Why This Matters:**
1. **Financial Reconciliation** - Match payments with bank deposits
2. **Business Analytics** - Understand payment patterns
3. **Customer Service** - Track specific customer transactions
4. **Compliance** - Maintain transaction records for audits
5. **Performance Monitoring** - Track success rates and issues

### **Competitive Advantage:**
- **Comprehensive Data** - More detailed than basic payment processors
- **Real-time Updates** - Immediate transaction visibility
- **Business Intelligence** - Actionable insights for merchants
- **Easy Integration** - API access for merchant systems

This transaction history system positions your payment gateway as a **professional, enterprise-ready solution** that provides merchants with complete visibility and control over their payment operations.