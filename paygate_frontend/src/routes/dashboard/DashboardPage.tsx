import { useEffect, useState } from 'react'
import { useAuth } from '../../utils/auth'
import { api } from '../../utils/http'

type AdminStats = {
  total_merchants: number
  total_admins: number
  total_orders: number
  total_successful_payments: number
  total_successful_refunds: number
  total_canceled_payments: number
}

type MerchantStats = {
  total_orders: number
  successful_payments: number
  successful_refunds: number
  canceled_payments: number
}

export default function DashboardPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const isMerchant = user?.role === 'merchant'

  // shared
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [refreshedAt, setRefreshedAt] = useState<string | null>(null)

  // admin
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [adminMsg, setAdminMsg] = useState<string | null>(null)

  // merchant
  const [merchantStats, setMerchantStats] = useState<MerchantStats | null>(null)
  const [merchantMsg, setMerchantMsg] = useState<string | null>(null)

  async function fetchAdminStats() {
    if (!isAdmin) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.get('/paygate/api/v1/admin/stats')
      setStats(res.data?.data ?? null)
      setAdminMsg(res.data?.message ?? null)
      setRefreshedAt(new Date().toLocaleString())
    } catch (e: any) {
      setError(e?.response?.data?.description || 'Failed to load admin stats')
    } finally {
      setLoading(false)
    }
  }

  async function fetchMerchantStats() {
    if (!isMerchant) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.get('/paygate/api/v1/merchants/stats')
      setMerchantStats(res.data?.data ?? null)
      setMerchantMsg(res.data?.message ?? null)
      setRefreshedAt(new Date().toLocaleString())
    } catch (e: any) {
      setError(e?.response?.data?.description || 'Failed to load merchant stats')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAdmin) fetchAdminStats()
    if (isMerchant) fetchMerchantStats()
  }, [isAdmin, isMerchant])

  if (!user) return null

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-gray-900">Welcome, {user.name}</h1>
        {/* <p className="mt-1 text-sm text-gray-600"></p> */}
      </header>

      {/* ─── Merchant Dashboard ───────────────────── */}
      {isMerchant && (
        <section className="space-y-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Overview</h2>
              {/* {merchantMsg && <p className="text-sm text-gray-600">{merchantMsg}</p>} */}
            </div>
            <div className="flex items-center gap-3">
              {refreshedAt && <span className="text-xs text-gray-500">Last updated: {refreshedAt}</span>}
              <button
                onClick={fetchMerchantStats}
                disabled={loading}
                className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-emerald-700 hover:bg-emerald-100 disabled:opacity-60"
              >
                Refresh
              </button>
            </div>
          </div>

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
          )}

          {loading && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-24 animate-pulse rounded-xl border bg-white p-5 shadow-sm">
                  <div className="h-4 w-24 rounded bg-gray-200"></div>
                  <div className="mt-3 h-6 w-16 rounded bg-gray-200"></div>
                </div>
              ))}
            </div>
          )}

          {!loading && merchantStats && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <KpiCard label="Total Orders" value={merchantStats.total_orders} tone="neutral" />
              <KpiCard label="Total Revenue" value={merchantStats.total_revenue} tone="neutral" />
              <KpiCard label="Successful Payments" value={merchantStats.successful_payments} tone="success" />
              <KpiCard label="Successful Refunds" value={merchantStats.successful_refunds} tone="success" />
              <KpiCard label="Total authorized payments" value={merchantStats.authorized_payments} tone="neutral" />
              <KpiCard
                label="Canceled Payments"
                value={merchantStats.canceled_payments}
                tone={merchantStats.canceled_payments > 0 ? 'warn' : 'neutral'}
              />
            </div>
          )}
        </section>
      )}

      {/* ─── Admin Dashboard (unchanged) ─────────── */}
      {isAdmin && (
        <section className="space-y-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Overview </h2>
              {/* {adminMsg && <p className="text-sm text-gray-600">{adminMsg}</p>} */}
            </div>
            <div className="flex items-center gap-3">
              {refreshedAt && <span className="text-xs text-gray-500">Last updated: {refreshedAt}</span>}
              <button
                onClick={fetchAdminStats}
                disabled={loading}
                className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-emerald-700 hover:bg-emerald-100 disabled:opacity-60"
              >
                Refresh
              </button>
            </div>
          </div>

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
          )}

          {!loading && stats && (
            <div className="grid gap-4 md:grid-cols-3">
              <KpiCard label="Total merchants" value={stats.total_merchants} tone="neutral" />
              <KpiCard label="Total admins" value={stats.total_admins} tone="neutral" />
              <KpiCard label="Total orders" value={stats.total_orders} tone="neutral" />
               <KpiCard label="Total Revenue " value={stats.total_commission} tone="success" />
              <KpiCard label="Total Authorized Payments" value={stats.total_authorized_payments} tone="neutral" />
              <KpiCard label="Total Captured Payments" value={stats.total_captured_payments} tone="neutral" />
              <KpiCard label="Successful payments" value={stats.total_successful_payments} tone="success" />
              <KpiCard label="Successful refunds" value={stats.total_successful_refunds} tone="success" />
              <KpiCard
                label="Canceled payments"
                value={stats.total_canceled_payments}
                tone={stats.total_canceled_payments > 0 ? 'warn' : 'neutral'}
              />
            </div>
          )}
        </section>
      )}
    </div>
  )
}

function KpiCard({
  label,
  value,
  tone,
}: {
  label: string
  value: number | string
  tone: 'neutral' | 'success' | 'warn'
}) {
  const toneClasses =
    tone === 'success'
      ? 'border-emerald-200'
      : tone === 'warn'
      ? 'border-amber-200'
      : 'border-gray-200'
  const valueClasses =
    tone === 'success'
      ? 'text-emerald-700'
      : tone === 'warn'
      ? 'text-amber-700'
      : 'text-gray-900'
  return (
    <div className={`rounded-xl border ${toneClasses} bg-white p-5 shadow-sm`}>
      <p className="text-sm text-gray-600">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${valueClasses}`}>{value}</p>
    </div>
  )
}

