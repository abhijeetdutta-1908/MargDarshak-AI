import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { EmptyState } from './ui'
import Spinner from './Spinner'

export default function ProtectedRoute({ children, admin = false }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <Spinner full />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (admin && !user.is_admin) {
    return <main className="mx-auto max-w-xl px-4 py-16"><EmptyState title="Admins only">You don't have access to this page.</EmptyState></main>
  }
  return children
}
