import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Button, Field, inputClass } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import AuthLayout from '../layouts/AuthLayout'
import { errorMessage } from '../services/api'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/dashboard'
  const expired = new URLSearchParams(location.search).has('expired')
  const [form, setForm] = useState({ email: '', password: '' })
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={from} replace />

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await login(form)
      toast.success('Welcome back!')
      navigate(from, { replace: true })
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to continue planning your trips."
      footer={<>New to Margdarshak? <Link to="/register" className="font-semibold text-brand-600 hover:text-brand-700">Create an account</Link></>}
    >
      {expired && <p className="mb-4 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">Your session ended. Please sign in again.</p>}
      <form onSubmit={submit} className="space-y-4">
        <Field label="Email">
          <input type="email" required autoComplete="email" className={inputClass} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </Field>
        <Field label="Password">
          <input type="password" required autoComplete="current-password" className={inputClass} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </Field>
        <Button type="submit" loading={busy} className="w-full">Sign in</Button>
      </form>
    </AuthLayout>
  )
}
