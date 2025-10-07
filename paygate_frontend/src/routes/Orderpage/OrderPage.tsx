import { useState, useEffect } from 'react'
import Select from 'react-select'
import { api } from '../../utils/http'
import { useAuth } from '../../utils/auth'

type OrderResponse = {
  order_id: string
  amount: string
  currency: string
  status: string
  created_at: string
}

type PaymentResponse = {
  payment_id: string
  order: string
  amount: string
  status: string
  created_at: string
}

export default function OrderPage() {
  const { user } = useAuth()
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('US')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [order, setOrder] = useState<OrderResponse | null>(null)

  const [inProgressOrders, setInProgressOrders] = useState<string[]>([])
  const [selectedOrderId, setSelectedOrderId] = useState('')
  const [cardNumber, setCardNumber] = useState('')
  const [expiry, setExpiry] = useState('')
  const [cvv, setCvv] = useState('')
  const [paymentLoading, setPaymentLoading] = useState(false)
  const [paymentResult, setPaymentResult] = useState<PaymentResponse | null>(null)
  const [fetchingOrders, setFetchingOrders] = useState(false)

  async function handleCreateOrder(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setMessage(null)
    setOrder(null)

    if (parseFloat(amount) <= 0) {
      setError('Amount must be greater than 0')
      setLoading(false)
      return
    }

    try {
      const res = await api.post('/paygate/api/v1/orders/', {
        amount: parseFloat(amount),
        currency,
      })

      setMessage(res.data?.message ?? 'Order created successfully')
      setOrder(res.data?.data ?? null)
      fetchInProgressOrders()
    } catch (e: any) {
      setError(e?.response?.data?.description || 'Failed to create order')
    } finally {
      setLoading(false)
    }
  }

  async function fetchInProgressOrders() {
    setFetchingOrders(true)
    try {
      const res = await api.get('/paygate/api/v1/payment-process')
      setInProgressOrders(res.data?.data ?? [])
    } catch (e: any) {
      console.error('Failed to fetch in-progress orders:', e)
    } finally {
      setFetchingOrders(false)
    }
  }

  async function handleProcessPayment(e: React.FormEvent) {
    e.preventDefault()
    setPaymentLoading(true)
    setError(null)
    setPaymentResult(null)

    try {
      const res = await api.post('/paygate/api/v1/payments/', {
        order_id: selectedOrderId,
        card_details: {
          card_number: cardNumber.replace(/\s/g, ''),
          expiry,
          cvv,
        },
      })

      setPaymentResult(res.data?.data ?? null)
      setMessage(res.data?.message ?? 'Payment processed successfully')

      setCardNumber('')
      setExpiry('')
      setCvv('')
      setSelectedOrderId('')
      fetchInProgressOrders()
    } catch (e: any) {
      setError(e?.response?.data?.description || 'Failed to process payment')
    } finally {
      setPaymentLoading(false)
    }
  }

  useEffect(() => {
    if (user) fetchInProgressOrders()
  }, [user])

  if (!user) return null

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-gray-900">Order & Payment Management</h1>
        <p className="mt-1 text-sm text-gray-600">
          Create new orders and process payments for existing orders.
        </p>
      </header>

      {/* --- Create Order Section --- */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Create New Order</h2>
        <form onSubmit={handleCreateOrder} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Amount</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500"
                placeholder="Enter amount greater than 0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500"
              >
                {/* <option value="US">US</option> */}
                <option value="IN">IN</option>
                {/* <option value="EU">EU</option> */}
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2 font-medium text-emerald-700 hover:bg-emerald-100 disabled:opacity-60"
          >
            {loading ? 'Creating...' : 'Create Order'}
          </button>
        </form>

        {order && (
          <div className="mt-4 rounded-xl border border-gray-200 bg-gray-50 p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
              <span className="mr-2">✓</span> Order Created Successfully
            </h3>
            <div className="grid gap-2 text-sm text-gray-700">
              <Detail label="Order ID" value={order.order_id} />
              <Detail label="Amount" value={`${order.amount}`} />
              <Detail label="Currency" value={order.currency} />
              <Detail label="Status" value={order.status} />
              <Detail label="Created At" value={new Date(order.created_at).toLocaleString()} />
            </div>
          </div>
        )}
      </div>

      {/* --- Process Payment Section --- */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Process Payment</h2>
          <button
            onClick={fetchInProgressOrders}
            disabled={fetchingOrders}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium disabled:opacity-60"
          >
            {fetchingOrders ? 'Refreshing...' : '↻ Refresh Orders'}
          </button>
        </div>

        {inProgressOrders.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No in-progress orders available.</p>
            <p className="text-sm mt-1">Create an order above to get started.</p>
          </div>
        ) : (
          <form onSubmit={handleProcessPayment} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Order ID
              </label>
              <Select
                options={inProgressOrders.map((id) => ({ value: id, label: id }))}
                onChange={(opt) => setSelectedOrderId(opt?.value || '')}
                value={
                  inProgressOrders
                    .map((id) => ({ value: id, label: id }))
                    .find((opt) => opt.value === selectedOrderId) || null
                }
                placeholder="Search or select order..."
                isSearchable
                className="text-sm"
                styles={{
                  control: (base) => ({
                    ...base,
                    borderColor: '#d1d5db',
                    borderRadius: '0.5rem',
                    boxShadow: 'none',
                    minHeight: '44px',
                    '&:hover': { borderColor: '#9ca3af' },
                  }),
                  menu: (base) => ({
                    ...base,
                    zIndex: 100,
                    maxHeight: 180,
                    overflowY: 'auto',
                    borderRadius: '0.5rem',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                  }),
                  menuList: (base) => ({
                    ...base,
                    maxHeight: 180,
                    overflowY: 'auto',
                  }),
                }}
              />
              <p className="mt-1 text-xs text-gray-600">
                {inProgressOrders.length} order(s) available for payment
              </p>
            </div>

            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Card Details</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Card Number</label>
                  <input
                    type="text"
                    value={cardNumber}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\s/g, '')
                      if (val.length <= 16 && /^\d*$/.test(val)) {
                        setCardNumber(val.replace(/(\d{4})/g, '$1 ').trim())
                      }
                    }}
                    placeholder="4111 1111 1111 1111"
                    required
                    maxLength={19}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Expiry</label>
                    <input
                      type="text"
                      value={expiry}
                      onChange={(e) => {
                        let val = e.target.value.replace(/\D/g, '')
                        if (val.length >= 2) val = val.slice(0, 2) + '/' + val.slice(2, 4)
                        if (val.length <= 5) setExpiry(val)
                      }}
                      placeholder="MM/YY"
                      required
                      maxLength={5}
                      className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">CVV</label>
                    <input
                      type="text"
                      value={cvv}
                      onChange={(e) => {
                        const val = e.target.value
                        if (val.length <= 3 && /^\d*$/.test(val)) setCvv(val)
                      }}
                      placeholder="123"
                      required
                      maxLength={3}
                      className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={paymentLoading || !selectedOrderId}
              className="w-full rounded-lg bg-blue-600 px-4 py-2.5 font-medium text-white hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {paymentLoading ? 'Processing Payment...' : 'Process Payment'}
            </button>
          </form>
        )}

        {paymentResult && (
          <div className="mt-4 rounded-xl border border-green-200 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-green-700 mb-3 flex items-center">
              <span className="mr-2">✓</span> Payment Successful
            </h3>
            <div className="grid gap-2 text-sm text-gray-700">
              <Detail label="Payment ID" value={paymentResult.payment_id} />
              <Detail label="Order ID" value={paymentResult.order} />
              <Detail label="Amount" value={`${paymentResult.amount}`} />
              <Detail label="Status" value={paymentResult.status} />
              <Detail label="Created At" value={new Date(paymentResult.created_at).toLocaleString()} />
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <strong className="font-medium">Error:</strong> {error}
        </div>
      )}
    </div>
  )
}

function Detail({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between border-b border-gray-100 py-1">
      <span className="font-medium text-gray-600">{label}</span>
      <span className="text-gray-900">{value}</span>
    </div>
  )
}
