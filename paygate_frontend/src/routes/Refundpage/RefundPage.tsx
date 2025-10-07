import { useState, useEffect } from 'react'
import Select from 'react-select'
import { api } from '../../utils/http'
import { useAuth } from '../../utils/auth'

type CompletedPayment = {
  payment_id: string
  amount: string
  currency: string
  created_at: string
}

type RefundResponse = {
  status: string
}

export default function RefundPage() {
  const { user } = useAuth()
  const [completedPayments, setCompletedPayments] = useState<CompletedPayment[]>([])
  const [selectedPaymentId, setSelectedPaymentId] = useState('')
  const [loadingPayments, setLoadingPayments] = useState(false)
  const [refundLoading, setRefundLoading] = useState(false)
  const [refundResult, setRefundResult] = useState<RefundResponse | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Fetch all completed payments
  async function fetchCompletedPayments() {
    setLoadingPayments(true)
    setError(null)
    try {
      const res = await api.get('/paygate/api/v1/payment-complete/')
      setCompletedPayments(res.data?.data ?? [])
    } catch (e: any) {
      setError(e?.response?.data?.description || 'Failed to load completed payments')
    } finally {
      setLoadingPayments(false)
    }
  }

  // Process refund request
  async function handleRefund(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedPaymentId) {
      setError('Please select a payment to refund')
      return
    }

    setRefundLoading(true)
    setError(null)
    setRefundResult(null)
    setMessage(null)

    try {
      const res = await api.post('/paygate/api/v1/refunds/', {
        payment_id: selectedPaymentId,
      })
      setRefundResult(res.data?.data ?? null)
      setMessage(res.data?.message ?? 'Refund processed successfully')
      fetchCompletedPayments()
      setSelectedPaymentId('')
    } catch (e: any) {
      setError(e?.response?.data?.description || 'Failed to process refund')
    } finally {
      setRefundLoading(false)
    }
  }

  useEffect(() => {
    if (user) fetchCompletedPayments()
  }, [user])

  if (!user) return null

  // Map payments to react-select options
  const paymentOptions = completedPayments.map((p) => ({
    value: p.payment_id,
    label: `Payment id : ${p.payment_id} , amount: ${p.amount} INR  , Date-time : ${new Date(p.created_at).toLocaleString()}`,
    //  label: `${p.payment_id} — ${p.amount} ${p.currency} — ${new Date(p.created_at).t  oLocaleString()}`,
  }))

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-gray-900">Refund Management</h1>
        <p className="mt-1 text-sm text-gray-600">
          View completed payments and process refunds easily.
        </p>
      </header>

      {/* Completed Payments Section */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Completed Payments</h2>
          <button
            onClick={fetchCompletedPayments}
            disabled={loadingPayments}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium disabled:opacity-60"
          >
            {loadingPayments ? 'Refreshing...' : '↻ Refresh List'}
          </button>
        </div>

        {completedPayments.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No completed payments available.</p>
            <p className="text-sm mt-1">Complete a payment to enable refunds.</p>
          </div>
        ) : (
          <form onSubmit={handleRefund} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Payment
              </label>
              <Select
                options={paymentOptions}
                onChange={(opt) => setSelectedPaymentId(opt?.value || '')}
                value={paymentOptions.find((opt) => opt.value === selectedPaymentId) || null}
                placeholder="Search or select payment..."
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
                {completedPayments.length} completed payment(s) available for refund
              </p>
            </div>

            <button
              type="submit"
              disabled={refundLoading || !selectedPaymentId}
              className="w-full rounded-lg bg-red-600 px-4 py-2.5 font-medium text-white hover:bg-red-700 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {refundLoading ? 'Processing Refund...' : 'Process Refund'}
            </button>
          </form>
        )}

        {/* Refund Result */}
        {refundResult && (
          <div className="mt-4 rounded-xl border border-green-200 bg-green-50 p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-green-700 mb-3 flex items-center">
              <span className="mr-2">✓</span> Refund Status
            </h3>
            <Detail label="Status" value={refundResult.status} />
          </div>
        )}
      </div>

      {/* Global Error or Message */}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <strong className="font-medium">Error:</strong> {error}
        </div>
      )}
      {message && (
        <div className="rounded-md border border-green-200 bg-green-50 p-4 text-sm text-green-700">
          <strong className="font-medium">Success:</strong> {message}
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
