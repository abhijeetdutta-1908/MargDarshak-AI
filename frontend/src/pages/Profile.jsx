import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Button, Card, ChipGroup, Field, inputClass } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { errorMessage, users } from '../services/api'
import { DESTINATION_TYPES, FOOD, HOTEL_TIERS, INTERESTS, passwordProblem, TRANSPORT } from '../utils/options'

function AccountCard() {
  const { user, setUser } = useAuth()
  const [form, setForm] = useState({ name: user.name, email: user.email, profile_image: user.profile_image || '' })
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      setUser(await users.update({ ...form, profile_image: form.profile_image || null }))
      toast.success('Profile updated')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const initials = user.name.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase()

  return (
    <Card title="Account" subtitle="How you appear in Margdarshak.">
      <form onSubmit={save} className="space-y-4">
        <div className="flex items-center gap-4">
          {form.profile_image ? (
            <img src={form.profile_image} alt="" className="h-16 w-16 rounded-full object-cover ring-2 ring-brand-100" onError={(e) => (e.currentTarget.style.display = 'none')} />
          ) : (
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-100 text-lg font-bold text-brand-700">{initials}</div>
          )}
          <div className="text-sm text-slate-500">Member since {new Date(user.created_at).toLocaleDateString()}</div>
        </div>
        <Field label="Name">
          <input required minLength={2} maxLength={120} className={inputClass} value={form.name} onChange={set('name')} />
        </Field>
        <Field label="Email">
          <input type="email" required className={inputClass} value={form.email} onChange={set('email')} />
        </Field>
        <Field label="Profile picture URL" hint="Link to an image (https://…)">
          <input type="url" className={inputClass} value={form.profile_image} onChange={set('profile_image')} placeholder="https://" />
        </Field>
        <Button type="submit" loading={busy}>Save profile</Button>
      </form>
    </Card>
  )
}

const EMPTY_PREFS = {
  destination_types: [], interests: [], budget_min: '', budget_max: '', hotel_preference: '',
  transport_preference: '', food_preference: '', travelers: '', starting_location: '',
}

function PreferencesCard() {
  const [prefs, setPrefs] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = () => {
    setLoadError(null)
    users
      .getPreferences()
      .then((p) => setPrefs(Object.fromEntries(Object.entries({ ...EMPTY_PREFS, ...p }).map(([k, v]) => [k, v ?? '']))))
      .catch((err) => setLoadError(errorMessage(err)))
  }
  useEffect(load, [])

  if (loadError)
    return (
      <Card title="Travel preferences">
        <p className="text-sm text-rose-600">{loadError}</p>
        <Button variant="secondary" className="mt-3" onClick={load}>Retry</Button>
      </Card>
    )
  if (!prefs) return <Card title="Travel preferences"><div className="h-64 animate-pulse rounded-xl bg-slate-100" /></Card>

  const set = (k) => (e) => setPrefs({ ...prefs, [k]: e.target.value })
  const num = (v) => (v === '' ? null : Number(v))
  const budgetError = prefs.budget_min !== '' && prefs.budget_max !== '' && Number(prefs.budget_min) > Number(prefs.budget_max)
    ? 'Minimum cannot exceed maximum' : null

  const save = async (e) => {
    e.preventDefault()
    if (budgetError) return
    setBusy(true)
    try {
      await users.putPreferences({
        ...prefs,
        budget_min: num(prefs.budget_min),
        budget_max: num(prefs.budget_max),
        travelers: num(prefs.travelers),
        hotel_preference: prefs.hotel_preference || null,
        transport_preference: prefs.transport_preference || null,
        food_preference: prefs.food_preference || null,
        starting_location: prefs.starting_location.trim() || null,
      })
      toast.success('Preferences saved')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card title="Travel preferences" subtitle="Used as defaults when you plan a trip.">
      <form onSubmit={save} className="space-y-6">
        <Field label="Favourite destination types">
          <ChipGroup options={DESTINATION_TYPES} value={prefs.destination_types} onChange={(v) => setPrefs({ ...prefs, destination_types: v })} />
        </Field>
        <Field label="Interests & activities">
          <ChipGroup options={INTERESTS} value={prefs.interests} onChange={(v) => setPrefs({ ...prefs, interests: v })} />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Budget min (₹)" error={budgetError}>
            <input type="number" min={0} step={500} className={inputClass} value={prefs.budget_min} onChange={set('budget_min')} />
          </Field>
          <Field label="Budget max (₹)">
            <input type="number" min={0} step={500} className={inputClass} value={prefs.budget_max} onChange={set('budget_max')} />
          </Field>
          <Field label="Hotel preference">
            <select className={inputClass} value={prefs.hotel_preference} onChange={set('hotel_preference')}>
              <option value="">No preference</option>
              {HOTEL_TIERS.map((t) => <option key={t} value={t} className="capitalize">{t[0].toUpperCase() + t.slice(1)}</option>)}
            </select>
          </Field>
          <Field label="Transportation">
            <select className={inputClass} value={prefs.transport_preference} onChange={set('transport_preference')}>
              <option value="">No preference</option>
              {TRANSPORT.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </Field>
          <Field label="Food preference">
            <select className={inputClass} value={prefs.food_preference} onChange={set('food_preference')}>
              <option value="">No preference</option>
              {FOOD.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </Field>
          <Field label="Usual number of travellers">
            <input type="number" min={1} max={50} className={inputClass} value={prefs.travelers} onChange={set('travelers')} />
          </Field>
        </div>
        <Field label="Starting location">
          <input maxLength={120} className={inputClass} value={prefs.starting_location} onChange={set('starting_location')} placeholder="e.g. Bhubaneswar" />
        </Field>
        <Button type="submit" loading={busy}>Save preferences</Button>
      </form>
    </Card>
  )
}

function PasswordCard() {
  const { acceptSession } = useAuth()
  const [form, setForm] = useState({ current_password: '', new_password: '' })
  const [busy, setBusy] = useState(false)
  const problem = form.new_password && passwordProblem(form.new_password)

  const save = async (e) => {
    e.preventDefault()
    if (problem) return
    setBusy(true)
    try {
      acceptSession(await users.changePassword(form))
      setForm({ current_password: '', new_password: '' })
      toast.success('Password changed. Other devices have been signed out.')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card title="Change password">
      <form onSubmit={save} className="space-y-4">
        <Field label="Current password">
          <input type="password" required autoComplete="current-password" className={inputClass} value={form.current_password} onChange={(e) => setForm({ ...form, current_password: e.target.value })} />
        </Field>
        <Field label="New password" error={problem}>
          <input type="password" required autoComplete="new-password" className={inputClass} value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} />
        </Field>
        <Button type="submit" variant="secondary" loading={busy}>Update password</Button>
      </form>
    </Card>
  )
}

export default function Profile() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="text-3xl font-bold tracking-tight">Your profile</h1>
      <div className="mt-8 grid *:min-w-0 gap-6 lg:grid-cols-[1fr_1.4fr]">
        <div className="space-y-6">
          <AccountCard />
          <PasswordCard />
        </div>
        <PreferencesCard />
      </div>
    </main>
  )
}
