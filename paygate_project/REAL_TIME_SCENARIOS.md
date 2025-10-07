# 🌐 Real-Time Working Scenarios: Payment Gateway in Action

## 🎯 **Overview**
This document demonstrates how your payment gateway works in real-world scenarios with actual API calls, responses, and business flows.

---

## 🏪 **Scenario 1: E-commerce Store Integration**

### **Business Context:**
"TechMart" - An online electronics store wants to integrate your payment gateway to accept payments for their products.

### **Step-by-Step Real-Time Flow:**

#### **Phase 1: Merchant Onboarding**

**1. TechMart Registration** 
```http
POST /paygate/api/v1/auth/register/
Content-Type: application/json

{
    "user": {
        "email": "admin@techmart.com",
        "name": "TechMart Admin",
        "password": "SecurePass123!"
    },
    "webhook_url": "https://techmart.com/api/payment-webhooks"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Merchant registered successfully",
    "data": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "api_key": "b8f5e2a1-9c4d-4e8f-a2b5-7c9d8e1f2a3b",
        "email": "admin@techmart.com",
        "name": "TechMart Admin",
        "role": "merchant"
    }
}
```

**What happens internally:**
- User account created with UUID: `550e8400-e29b-41d4-a716-446655440001`
- Merchant profile linked with unique API key
- JWT tokens generated (access + refresh cookie)
- Webhook URL stored for payment notifications

#### **Phase 2: Integration Setup**

**2. TechMart Developer Integration**
TechMart's backend integrates your API:

```javascript
// TechMart's Node.js backend
const PAYGATE_API = "http://localhost:8000/paygate/api/v1";
const MERCHANT_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...";

// Function to create payment order
async function createPaymentOrder(amount, currency = 'INR') {
    const response = await fetch(`${PAYGATE_API}/orders/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${MERCHANT_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ amount, currency })
    });
    return response.json();
}
```

---

### **Phase 3: Real Customer Transaction**

**Customer Story:** John wants to buy a laptop for ₹75,000 from TechMart

#### **3.1 Order Creation on TechMart**
```
Customer Action: John adds MacBook Pro (₹75,000) to cart → Clicks "Pay Now"
TechMart Action: Creates order in their system → Calls your payment gateway
```

**API Call from TechMart:**
```http
POST /paygate/api/v1/orders/
Authorization: Bearer eyJ0eXAiOiJKV1Q...
Content-Type: application/json

{
    "amount": 75000.00,
    "currency": "INR"
}
```

**Your System Response:**
```json
{
    "success": true,
    "message": "Order created successfully",
    "data": {
        "order_id": "order-a1b2c3d4-e5f6-7890-ab12-cd34ef567890",
        "amount": "75000.00",
        "currency": "INR",
        "status": "created",
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

**What happens internally:**
- Order record created in your database
- Linked to TechMart's merchant account
- Status set to "created"
- Unique order_id generated

#### **3.2 Payment Page Display**
```
TechMart Action: Shows payment form with order details
Customer Sees: Payment form asking for card details
```

**TechMart's Payment Form:**
```html
<form id="payment-form">
    <h3>Pay ₹75,000 for MacBook Pro</h3>
    <input type="text" placeholder="Card Number" id="card-number">
    <input type="text" placeholder="MM/YY" id="expiry">
    <input type="text" placeholder="CVV" id="cvv">
    <button onclick="processPayment()">Pay Now</button>
</form>

<script>
function processPayment() {
    const cardData = {
        card_number: document.getElementById('card-number').value,
        expiry: document.getElementById('expiry').value,
        cvv: document.getElementById('cvv').value
    };
    
    // Call TechMart's backend
    fetch('/techmart/process-payment', {
        method: 'POST',
        body: JSON.stringify({
            order_id: 'order-a1b2c3d4-e5f6-7890-ab12-cd34ef567890',
            card_details: cardData
        })
    });
}
</script>
```

#### **3.3 Payment Processing**
```
Customer Action: Enters card details → Clicks "Pay Now"
TechMart Backend: Receives card data → Calls your payment API
```

**API Call from TechMart:**
```http
POST /paygate/api/v1/payments/
Authorization: Bearer eyJ0eXAiOiJKV1Q...
Content-Type: application/json

{
    "order_id": "order-a1b2c3d4-e5f6-7890-ab12-cd34ef567890",
    "card_details": {
        "card_number": "4532123456789012",
        "expiry": "12/25",
        "cvv": "123"
    }
}
```

**Your System Processing:**
1. **Validates** merchant ownership of order
2. **Creates** card hash: `sha256("4532123456789012")` = `a8f5f167f44f4964e6c998dee827110c`
3. **Simulates** payment (80% success rate)
4. **Creates** payment record
5. **Updates** order status
6. **Sends** webhook to TechMart

**Your System Response:**
```json
{
    "success": true,
    "message": "Payment processed successfully",
    "data": {
        "payment_id": "pay-b2c3d4e5-f6g7-8901-bc23-de45fg678901",
        "order": "order-a1b2c3d4-e5f6-7890-ab12-cd34ef567890",
        "amount": "75000.00",
        "status": "authorized",
        "created_at": "2024-01-15T10:35:00Z"
    }
}
```

#### **3.4 Webhook Notification**
**Immediately after payment processing:**

**Webhook Sent to TechMart:**
```http
POST https://techmart.com/api/payment-webhooks
Content-Type: application/json

{
    "event": "payment.authorized",
    "payment_id": "pay-b2c3d4e5-f6g7-8901-bc23-de45fg678901",
    "order_id": "order-a1b2c3d4-e5f6-7890-ab12-cd34ef567890",
    "amount": "75000.00",
    "currency": "INR",
    "status": "authorized",
    "created_at": "2024-01-15T10:35:00Z"
}
```

**TechMart's Webhook Handler:**
```javascript
// TechMart's webhook endpoint
app.post('/api/payment-webhooks', (req, res) => {
    const { event, payment_id, order_id, status } = req.body;
    
    if (event === 'payment.authorized' && status === 'authorized') {
        // Update TechMart's order status
        updateOrderStatus(order_id, 'paid');
        
        // Send confirmation email to customer
        sendOrderConfirmation('john@email.com', order_id);
        
        // Trigger fulfillment process
        initiateShipping(order_id);
    }
    
    res.json({ success: true });
});
```

#### **3.5 Customer Experience**
```
Customer Sees: "Payment Successful! Your order is confirmed."
TechMart System: 
- Order status → "Paid"
- Email sent to customer
- Shipping process initiated
- Inventory updated
```

---

## 🔄 **Scenario 2: Subscription Service (SaaS)**

### **Business Context:**
"CloudSync Pro" - A SaaS company offering cloud storage subscriptions wants monthly recurring payments.

### **Monthly Subscription Flow:**

#### **1. Customer Sarah subscribes to Pro Plan ($29/month)**

**Subscription Creation:**
```http
POST /paygate/api/v1/orders/
Authorization: Bearer eyJ0eXAiOiJKV1Q...

{
    "amount": 29.00,
    "currency": "USD"
}
```

**Monthly Billing Cycle:**
```javascript
// CloudSync's billing system (runs monthly)
async function processMonthlyBilling() {
    const activeSubscriptions = await getActiveSubscriptions();
    
    for (let subscription of activeSubscriptions) {
        // Create new order for this month
        const order = await createPaymentOrder(subscription.amount);
        
        // Charge using stored card details
        const payment = await processPayment(order.order_id, subscription.cardToken);
        
        if (payment.status === 'authorized') {
            extendSubscription(subscription.id);
        } else {
            suspendAccount(subscription.id);
        }
    }
}
```

---

## 🛒 **Scenario 3: Marketplace Platform**

### **Business Context:**
"ArtisanMarket" - A marketplace where multiple vendors sell handmade products.

### **Multi-Vendor Payment Split:**

#### **Customer buys from 3 different vendors in one order:**
- Vendor A: Handmade soap (₹500)
- Vendor B: Wooden toy (₹800)  
- Vendor C: Organic honey (₹300)
- **Total: ₹1,600**

**Payment Flow:**
```http
POST /paygate/api/v1/orders/
{
    "amount": 1600.00,
    "currency": "INR"
}
```

**After successful payment, ArtisanMarket splits:**
```javascript
// ArtisanMarket's settlement logic
const paymentSplit = {
    vendorA: 500 - (500 * 0.02), // 2% platform fee
    vendorB: 800 - (800 * 0.02),
    vendorC: 300 - (300 * 0.02),
    platform: 1600 * 0.02 // Platform keeps 2%
};

// Transfer to vendors (outside your gateway)
transferToVendors(paymentSplit);
```

---

## 🔄 **Scenario 4: Refund Processing**

### **Real-Time Refund Example:**

#### **Customer John requests refund for MacBook:**

**1. TechMart initiates refund:**
```http
POST /paygate/api/v1/refunds/
Authorization: Bearer eyJ0eXAiOiJKV1Q...

{
    "payment_id": "pay-b2c3d4e5-f6g7-8901-bc23-de45fg678901"
}
```

**2. Your system processes:**
```json
{
    "success": true,
    "message": "Refund processed successfully",
    "data": {
        "status": "refunded"
    }
}
```

**3. Webhook sent to TechMart:**
```http
POST https://techmart.com/api/payment-webhooks

{
    "event": "payment.refunded",
    "payment_id": "pay-b2c3d4e5-f6g7-8901-bc23-de45fg678901",
    "status": "refunded"
}
```

**4. TechMart's action:**
```javascript
// Update order status and notify customer
if (event === 'payment.refunded') {
    updateOrderStatus(order_id, 'refunded');
    sendRefundConfirmation('john@email.com', order_id);
}
```

---

## 📊 **Scenario 5: Admin Dashboard Monitoring**

### **Real-Time Admin View:**

**Admin checks system stats:**
```http
GET /paygate/api/v1/admin/stats/
Authorization: Bearer admin_jwt_token
```

**Response shows:**
```json
{
    "success": true,
    "data": {
        "total_merchants": 1247,
        "total_orders": 15420,
        "total_successful_payments": 12336,
        "total_successful_refunds": 284,
        "total_canceled_payments": 2800,
        "success_rate": "80.0%"
    }
}
```

**Merchant-specific stats:**
```http
GET /paygate/api/v1/admin/stats/?merchant_id=123
```

**Shows TechMart's performance:**
```json
{
    "user__email": "admin@techmart.com",
    "order_count": 245,
    "successful_payments": 196,
    "successful_refunds": 12,
    "canceled_payments": 37
}
```

---

## 🔧 **Scenario 6: Error Handling in Real-Time**

### **What happens when things go wrong:**

#### **Payment Failure Scenario:**
```
Customer: Enters invalid card number
Your System: Card validation fails (< 12 characters)
Response: Payment failed with error
TechMart: Shows error message to customer
Customer: Corrects card details and retries
```

**Failed Payment API Response:**
```json
{
    "success": false,
    "exception": {
        "code": 1011,
        "message": "Payment failed",
        "description": "Invalid card details"
    }
}
```

**TechMart's Error Handling:**
```javascript
if (!response.success) {
    showErrorMessage("Payment failed. Please check your card details.");
    enableRetryButton();
}
```

#### **Network Timeout Scenario:**
```
Issue: Webhook delivery fails to TechMart
Your System: Logs failed webhook attempt
TechMart: Doesn't receive immediate notification
Resolution: Manual reconciliation or retry mechanism needed
```

---

## 💼 **Business Metrics in Action**

### **Daily Operations Example:**

**Morning (9 AM):** 
- 150 new orders created
- 120 payments processed successfully  
- 30 payment failures
- 5 refunds processed

**Webhook Activity:**
- 125 webhooks sent successfully
- 15 webhook delivery failures
- Merchants receive real-time notifications

**Merchant Dashboard Shows:**
```
TechMart Today:
- Orders: 45
- Successful: 36 (80% success rate)
- Revenue: ₹2,47,500
- Refunds: 2
```

---

## 🎯 **Key Success Factors**

### **What Makes Your System Work:**

1. **Reliable API Endpoints** - Consistent responses
2. **Webhook Notifications** - Real-time updates to merchants  
3. **Proper Error Handling** - Clear error messages
4. **Secure Authentication** - JWT tokens for API access
5. **Audit Trails** - Complete payment history

### **Merchant Benefits:**
- Quick integration (hours, not weeks)
- Real-time payment notifications
- Comprehensive dashboard
- Secure payment processing
- Developer-friendly APIs

### **Customer Experience:**
- Smooth payment flow
- Quick processing
- Immediate confirmation
- Secure card handling

---

## 🚀 **Production Deployment Example**

### **Going Live Process:**

1. **Development Integration** (Current)
2. **Testing Phase** - Sandbox environment
3. **Security Review** - PCI compliance check
4. **Production Deployment:**
   ```
   Domain: https://api.paygate.com
   Rate Limits: 1000 requests/minute
   SLA: 99.9% uptime
   Support: 24/7 monitoring
   ```

5. **Merchant Onboarding:**
   - KYC verification
   - Business documentation
   - Go-live approval
   - Real payment processing

This demonstrates how your payment gateway functions as a complete business solution, handling everything from merchant registration to payment processing, webhooks, and analytics in real-world scenarios.