import { useState } from 'react'
import { api } from '../../utils/http'
import { useAuth } from '../../utils/auth'

type AdminResponse = {
  access: string
  email: string
  name: string
  role: string
}

export default function AdminOnboardingPage() {
  const { user } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [newAdmin, setNewAdmin] = useState<AdminResponse | null>(null)

  async function handleRegisterAdmin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccessMessage(null)
    setNewAdmin(null)

    if (!name || !email || !password) {
      setError('All fields are required')
      setLoading(false)
      return
    }

    try {
      const res = await api.post('/paygate/api/v1/auth/register-admin/', {
        user: { name, email, password },
      })
      setNewAdmin(res.data?.data ?? null)
      setSuccessMessage(res.data?.message ?? 'Admin registered successfully')
      setName('')
      setEmail('')
      setPassword('')
    } catch (e: any) {
      setError(e?.response?.data?.description || 'Failed to register admin')
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-gray-900">Admin Onboarding</h1>
        <p className="mt-1 text-sm text-gray-600">
          Register new admins to manage the platform.
        </p>
      </header>

      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Register New Admin</h2>
        <form onSubmit={handleRegisterAdmin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500"
              placeholder="Enter full name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500"
              placeholder="admin@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500"
              placeholder="Enter password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2 font-medium text-emerald-700 hover:bg-emerald-100 disabled:opacity-60"
          >
            {loading ? 'Registering...' : 'Register Admin'}
          </button>
        </form>

        {successMessage && newAdmin && (
          <div className="mt-4 rounded-xl border border-green-200 bg-green-50 p-4">
            <h3 className="text-sm font-semibold text-green-700 mb-3 flex items-center">
              <span className="mr-2">✓</span> {successMessage}
            </h3>
            <div className="grid gap-2 text-sm text-gray-700">
              <Detail label="Name" value={newAdmin.name} />
              <Detail label="Email" value={newAdmin.email} />
              <Detail label="Role" value={newAdmin.role} />
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <strong className="font-medium">Error:</strong> {error}
          </div>
        )}
      </div>
    </div>
  )
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-gray-100 py-1">
      <span className="font-medium text-gray-600">{label}</span>
      <span className="text-gray-900">{value}</span>
    </div>
  )
}
