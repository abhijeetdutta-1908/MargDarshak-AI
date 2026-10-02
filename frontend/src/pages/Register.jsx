import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Button, Field, inputClass } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import AuthLayout from '../layouts/AuthLayout'
import { errorMessage } from '../services/api'
import { passwordProblem } from '../utils/options'

export default function Register() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [touched, setTouched] = useState(false)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/profile" replace />

  const errors = {
    name: form.name.trim().length < 2 ? 'Enter your name' : null,
    password: passwordProblem(form.password),
    confirm: form.confirm !== form.password ? 'Passwords do not match' : null,
  }
  const invalid = Object.values(errors).some(Boolean)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setTouched(true)
    if (invalid) return
    setBusy(true)
    try {
      await register({ name: form.name, email: form.email, password: form.password })
      toast.success('Account created. Tell us how you like to travel!')
      navigate('/profile', { replace: true })
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const show = (k) => (touched ? errors[k] : null)

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Get personalised recommendations in minutes."
      footer={<>Already have an account? <Link to="/login" className="font-semibold text-brand-600 hover:text-brand-700">Sign in</Link></>}
    >
      <form onSubmit={submit} className="space-y-4">
        <Field label="Full name" error={show('name')}>
          <input required autoComplete="name" className={inputClass} value={form.name} onChange={set('name')} />
        </Field>
        <Field label="Email">
          <input type="email" required autoComplete="email" className={inputClass} value={form.email} onChange={set('email')} />
        </Field>
        <Field label="Password" error={show('password')} hint="8+ characters, letters plus a number or symbol">
          <input type="password" required autoComplete="new-password" className={inputClass} value={form.password} onChange={set('password')} />
        </Field>
        <Field label="Confirm password" error={show('confirm')}>
          <input type="password" required autoComplete="new-password" className={inputClass} value={form.confirm} onChange={set('confirm')} />
        </Field>
        <Button type="submit" loading={busy} className="w-full">Create account</Button>
      </form>
    </AuthLayout>
  )
}
