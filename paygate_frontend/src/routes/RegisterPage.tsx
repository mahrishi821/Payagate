import { FormEvent, useState } from 'react'
import { useAuth } from '../utils/auth'
import { Link, useNavigate } from 'react-router-dom'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorDetail, setErrorDetail] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setErrorDetail(null)
    setSuccess(null)
    try {
      const data = await register(name, email, password, webhookUrl)
      setSuccess(data?.message || 'Registration successful')
      setTimeout(()=> navigate('/'), 500)
    } catch (e: any) {
      setError(e?.response?.data?.message || 'Registration failed')
      setErrorDetail(e?.response?.data?.description || null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[80vh] bg-gradient-to-b from-emerald-50 to-blue-50">
      <div className="mx-auto flex max-w-6xl items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center">
            {/* <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">$</div> */}
            <h1 className="text-2xl font-semibold text-gray-900">Create your merchant account</h1>
            <p className="mt-1 text-sm text-gray-600">Start accepting payments with confidence</p>
          </div>
          <div className="rounded-2xl border border-emerald-100 bg-white p-8 shadow-sm">
            <div className="mb-5 flex items-center justify-center gap-2 text-xs text-gray-500">
            </div>
            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm text-gray-700">Name</label>
                <input className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-200" value={name} onChange={e=>setName(e.target.value)} required />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-700">Email</label>
                <input className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-200" type="email" value={email} onChange={e=>setEmail(e.target.value)} required />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-700">Password</label>
                <input className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-200" type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
              </div>
              {/* <div>
                <label className="mb-1 block text-sm text-gray-700">Webhook URL (optional)</label>
                <input className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-200" value={webhookUrl} onChange={e=>setWebhookUrl(e.target.value)} placeholder="https://example.com/webhook" />
              </div> */}
              {error && (
                <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  <p className="font-medium">{error}</p>
                  {errorDetail && <p className="mt-1 text-red-600">{errorDetail}</p>}
                </div>
              )}
              {success && (
                <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
                  {success}
                </div>
              )}
              <button disabled={loading} className="w-full rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white transition hover:bg-emerald-700 disabled:opacity-60">
                {loading ? 'Creating…' : 'Create account'}
              </button>
            </form>
          </div>
          <p className="mt-4 text-center text-sm text-gray-600">
            Already have an account? <Link to="/login" className="text-emerald-700 hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}


