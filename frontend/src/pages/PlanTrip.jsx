import { CalendarDays, Compass, MapPin, Sparkles, Users, Wallet } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import GenerationProgress, { RECOMMEND_STEPS } from '../components/GenerationProgress'
import { Button, Card, ChipGroup, Field, PageHeader, inputClass } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { errorMessage, recommend, users } from '../services/api'
import { DESTINATION_TYPES, FOOD, HOTEL_TIERS, INTERESTS, TRANSPORT } from '../utils/options'
import { EMPTY_PLAN, planFromPreferences, toRequest, todayISO, validatePlan } from '../utils/plan'

export const LAST_PLAN_KEY = 'margdarshak_last_plan'

function Section({ icon: Icon, title, children }) {
  return (
    <div>
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500"><Icon size={16} />{title}</h3>
      {children}
    </div>
  )
}

export default function PlanTrip() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(() => {
    try { return { ...EMPTY_PLAN, ...JSON.parse(sessionStorage.getItem(LAST_PLAN_KEY))?.form } } catch { return { ...EMPTY_PLAN } }
  })
  const [touched, setTouched] = useState(false)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  // Prefill from saved profile preferences the first time.
  useEffect(() => {
    if (!user || sessionStorage.getItem(LAST_PLAN_KEY)) return
    users.getPreferences().then((p) => setForm((f) => ({ ...planFromPreferences(p), duration: f.duration, travel_date: f.travel_date }))).catch(() => {})
  }, [user])

  const errors = validatePlan(form)
  const show = (k) => (touched ? errors[k] : null)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setTouched(true)
    if (Object.keys(errors).length) {
      toast.error('Please fix the highlighted fields')
      return
    }
    setBusy(true)
    setDone(false)
    try {
      const request = toRequest(form)
      const result = await recommend({ ...request, top_k: 6 })
      sessionStorage.setItem(LAST_PLAN_KEY, JSON.stringify({ form, request, result }))
      setDone(true)
      setTimeout(() => navigate('/recommendations', { state: { request, result } }), 500)
    } catch (err) {
      toast.error(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <PageHeader eyebrow="Plan your trip" title="Tell us how you like to travel"
        subtitle="Margdarshak scores 36 destinations against your interests, budget, dates and style, then explains every recommendation." />
      <form onSubmit={submit} noValidate>
        <Card bodyClass="space-y-8">
          <Section icon={Compass} title="What kind of trip?">
            <Field label="Destination type" hint="Pick any that appeal">
              <ChipGroup options={DESTINATION_TYPES} value={form.destination_types} onChange={(v) => setForm({ ...form, destination_types: v })} />
            </Field>
            <Field label="Interests & activities" error={show('interests')} className="mt-5">
              <ChipGroup options={INTERESTS} value={form.interests} onChange={(v) => setForm({ ...form, interests: v })} />
            </Field>
            <Field label="Describe your ideal trip (optional)" error={show('notes')} hint="Used for AI semantic matching, e.g. “peaceful mountains, sunrise views and local food”" className="mt-5">
              <textarea className={`${inputClass} min-h-20`} maxLength={300} value={form.notes} onChange={set('notes')} placeholder="I enjoy..." />
            </Field>
          </Section>

          <Section icon={CalendarDays} title="When and how long?">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={`Trip length: ${form.duration} day${form.duration > 1 ? 's' : ''}`} error={show('duration')}>
                <div className="flex items-center gap-3">
                  <input type="range" min={1} max={30} value={form.duration} onChange={set('duration')} className="flex-1 accent-brand-600" aria-label="Trip length in days" />
                  <input type="number" min={1} max={30} value={form.duration} onChange={set('duration')} className={`${inputClass} w-20`} aria-label="Days" />
                </div>
              </Field>
              <Field label="Travel date" error={show('travel_date')} hint="Used for season and forecast checks">
                <input type="date" min={todayISO()} value={form.travel_date} onChange={set('travel_date')} className={inputClass} />
              </Field>
            </div>
          </Section>

          <Section icon={Wallet} title="Budget">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Minimum (₹, optional)" error={show('budget_min')}>
                <input type="number" min={0} step={500} value={form.budget_min} onChange={set('budget_min')} className={inputClass} />
              </Field>
              <Field label="Maximum for the whole group (₹)" error={show('budget_max')}>
                <input type="number" min={1} step={500} value={form.budget_max} onChange={set('budget_max')} className={inputClass} required />
              </Field>
              <Field label="Hotel preference">
                <select className={inputClass} value={form.hotel_preference} onChange={set('hotel_preference')}>
                  <option value="">No preference</option>
                  {HOTEL_TIERS.map((t) => <option key={t} value={t}>{t[0].toUpperCase() + t.slice(1)}</option>)}
                </select>
              </Field>
              <Field label="Food preference">
                <select className={inputClass} value={form.food_preference} onChange={set('food_preference')}>
                  <option value="">No preference</option>
                  {FOOD.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </Field>
            </div>
          </Section>

          <Section icon={Users} title="Who and how?">
            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="Travellers" error={show('travelers')}>
                <input type="number" min={1} max={50} value={form.travelers} onChange={set('travelers')} className={inputClass} />
              </Field>
              <Field label="Transportation">
                <select className={inputClass} value={form.transport_preference} onChange={set('transport_preference')}>
                  <option value="">No preference</option>
                  {TRANSPORT.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </Field>
              <Field label="Starting from (optional)" hint="Adds travel cost to the estimate">
                <div className="relative">
                  <MapPin size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input className={`${inputClass} pl-9`} maxLength={120} value={form.starting_location} onChange={set('starting_location')} placeholder="e.g. Bhubaneswar" />
                </div>
              </Field>
            </div>
          </Section>

          <div className="flex flex-col-reverse gap-3 border-t border-slate-100 pt-6 sm:flex-row sm:items-center sm:justify-between">
            <button type="button" className="text-sm text-slate-500 hover:text-ink" onClick={() => { setForm({ ...EMPTY_PLAN }); setTouched(false); sessionStorage.removeItem(LAST_PLAN_KEY) }}>Reset form</button>
            <Button type="submit" size="lg" loading={busy && !done}><Sparkles size={18} />Get AI recommendations</Button>
          </div>
        </Card>
      </form>
      {busy && <GenerationProgress steps={RECOMMEND_STEPS} done={done} finalLabel="Your matches are ready!" />}
    </main>
  )
}
