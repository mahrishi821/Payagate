import { FormEvent, useState } from 'react'
import { useAuth } from '../utils/auth'
import { Link, useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
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
    // try {
    //   const data = await login(email, password)
    //   setSuccess(data?.message|| 'Login successful')
    //   setTimeout(()=> navigate('/'), 400)
    // } catch (e: any) {
    //   setError(e?.exception?.message || 'Login failed')
    //   setErrorDetail(e?.response?.data?.description || null)
    // } finally {
    //   setLoading(false)
    // }
    const data = await login(email, password)
  if (data.success) {
    setSuccess(data.message)
    setTimeout(() => navigate('/'), 400)
  } else {
    setError(data.message)
    setErrorDetail(data.description)
  }
   setLoading(false)
  }

  return (
    <div className="min-h-[80vh] bg-gradient-to-b from-emerald-50 to-blue-50">
      <div className="mx-auto flex max-w-6xl items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center">
            {/* <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">$</div> */}
            <h1 className="text-2xl font-semibold text-gray-900">Sign in to PayGate</h1>
            <p className="mt-1 text-sm text-gray-600">Secure access to your payments dashboard</p>
          </div>
          <div className="rounded-2xl border border-emerald-100 bg-white p-8 shadow-sm">
            <div className="mb-5 flex items-center justify-center gap-2 text-xs text-gray-500">
            </div>
            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm text-gray-700">Email</label>
                <input className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-200" type="email" value={email} onChange={e=>setEmail(e.target.value)} required />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-700">Password</label>
                <input className="w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-200" type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
              </div>
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
                {loading ? 'Signing in…' : 'Sign in'}
              </button>
            </form>
          </div>
          <p className="mt-4 text-center text-sm text-gray-600">
            No account? <Link to="/register" className="text-emerald-700 hover:underline">Register</Link>
          </p>
        </div>
      </div>
    </div>
  )
}


