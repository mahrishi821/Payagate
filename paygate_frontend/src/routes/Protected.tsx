import { Navigate } from 'react-router-dom'
import { useAuth } from '../utils/auth'

export default function Protected({ children, role }: { children: JSX.Element, role?: 'admin' | 'merchant' | 'user' }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role) return <Navigate to="/" replace />
  return children
}




