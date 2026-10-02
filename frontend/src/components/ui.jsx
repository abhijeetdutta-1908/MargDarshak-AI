// Shared primitives so every screen looks and behaves the same.
import { AlertTriangle, Inbox, Star, X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import Spinner from './Spinner'

export function Field({ label, error, hint, children, className = '' }) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1.5 block text-sm font-medium text-slate-700">{label}</span>
      {children}
      {error ? (
        <span className="mt-1 block text-xs text-rose-600" role="alert">{error}</span>
      ) : (
        hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>
      )}
    </label>
  )
}

export const inputClass =
  'w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-100 disabled:bg-slate-100'

const BUTTON = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700 shadow-sm',
  accent: 'bg-saffron-500 text-white hover:bg-saffron-600 shadow-sm',
  secondary: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
  ghost: 'text-slate-600 hover:bg-slate-100',
  danger: 'bg-rose-600 text-white hover:bg-rose-700',
  light: 'bg-white/90 text-ink hover:bg-white shadow-sm',
}

export function Button({ loading, children, variant = 'primary', size = 'md', className = '', ...props }) {
  const sizes = { sm: 'px-3 py-1.5 text-xs', md: 'px-4 py-2.5 text-sm', lg: 'px-6 py-3.5 text-base' }
  return (
    <button
      disabled={loading || props.disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition active:scale-[.98] disabled:cursor-not-allowed disabled:opacity-60 ${sizes[size]} ${BUTTON[variant]} ${className}`}
      {...props}
    >
      {loading && <Spinner className="h-4 w-4" />}
      {children}
    </button>
  )
}

export function Card({ title, subtitle, action, children, className = '', bodyClass = '' }) {
  return (
    <section className={`rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card sm:p-6 ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            {title && <h2 className="text-lg font-bold">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className={bodyClass}>{children}</div>
    </section>
  )
}

const BADGE = {
  slate: 'bg-slate-100 text-slate-700',
  brand: 'bg-brand-50 text-brand-700 ring-1 ring-brand-100',
  amber: 'bg-amber-50 text-amber-800 ring-1 ring-amber-100',
  rose: 'bg-rose-50 text-rose-700 ring-1 ring-rose-100',
  sky: 'bg-sky-50 text-sky-700 ring-1 ring-sky-100',
  violet: 'bg-violet-50 text-violet-700 ring-1 ring-violet-100',
}

export function Badge({ children, tone = 'slate', className = '' }) {
  return <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${BADGE[tone]} ${className}`}>{children}</span>
}

/** Labels data that is not live (seeded, estimated, fallback) so it is never mistaken for live data. */
export function SourceBadge({ source, note }) {
  const live = ['live', 'google_places', 'google_routes', 'forecast'].includes(source)
  const label = { live: 'Live', google_places: 'Live · Google Places', google_routes: 'Live · Google Routes', forecast: 'Forecast',
    seeded: 'Curated data', sample: 'Sample data', fallback: 'Seasonal guidance', estimate: 'Estimated', seasonal: 'Seasonal guidance' }[source] || source
  return (
    <span title={note || undefined}>
      <Badge tone={live ? 'brand' : 'amber'}>
        <span className={`h-1.5 w-1.5 rounded-full ${live ? 'bg-brand-500' : 'bg-amber-500'}`} />
        {label}
      </Badge>
    </span>
  )
}

export function ChipGroup({ options, value, onChange, labels = {} }) {
  const toggle = (opt) => onChange(value.includes(opt) ? value.filter((v) => v !== opt) : [...value, opt])
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => {
        const on = value.includes(opt)
        return (
          <button
            type="button"
            key={opt}
            aria-pressed={on}
            onClick={() => toggle(opt)}
            className={`rounded-full border px-3.5 py-1.5 text-sm capitalize transition ${
              on ? 'border-brand-600 bg-brand-600 text-white shadow-sm' : 'border-slate-300 bg-white text-slate-700 hover:border-brand-500 hover:text-brand-700'
            }`}
          >
            {labels[opt] || opt}
          </button>
        )
      })}
    </div>
  )
}

export function Skeleton({ className = '' }) {
  return <div className={`animate-pulse rounded-xl bg-slate-200/70 ${className}`} />
}

export function EmptyState({ icon: Icon = Inbox, title, children, action }) {
  return (
    <div className="flex flex-col items-center rounded-2xl border border-dashed border-slate-300 bg-white/60 px-6 py-12 text-center">
      <div className="mb-3 rounded-2xl bg-slate-100 p-3 text-slate-500"><Icon size={26} /></div>
      <h3 className="font-semibold">{title}</h3>
      {children && <p className="mt-1 max-w-md text-sm text-slate-500">{children}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center rounded-2xl border border-rose-200 bg-rose-50/60 px-6 py-10 text-center" role="alert">
      <AlertTriangle className="mb-2 text-rose-500" size={26} />
      <p className="text-sm text-rose-700">{message}</p>
      {onRetry && <Button variant="secondary" className="mt-4" onClick={onRetry}>Try again</Button>}
    </div>
  )
}

export function Modal({ open, onClose, title, children, footer, wide = false }) {
  const ref = useRef(null)
  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    ref.current?.querySelector('input,textarea,select,button')?.focus()
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 p-0 backdrop-blur-sm sm:items-center sm:p-4" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div ref={ref} role="dialog" aria-modal="true" aria-label={title}
        className={`max-h-[92vh] w-full animate-fade-up overflow-y-auto rounded-t-3xl bg-white p-6 shadow-lift sm:rounded-3xl ${wide ? 'sm:max-w-3xl' : 'sm:max-w-md'}`}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold">{title}</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-500 hover:bg-slate-100" aria-label="Close"><X size={18} /></button>
        </div>
        {children}
        {footer && <div className="mt-6 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  )
}

export function ConfirmDialog({ open, title, message, confirmLabel = 'Confirm', danger = false, loading, onConfirm, onClose }) {
  return (
    <Modal open={open} onClose={onClose} title={title}
      footer={<>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button variant={danger ? 'danger' : 'primary'} loading={loading} onClick={onConfirm}>{confirmLabel}</Button>
      </>}>
      <p className="text-sm text-slate-600">{message}</p>
    </Modal>
  )
}

export function Tabs({ tabs, value, onChange }) {
  return (
    <div className="flex gap-1 overflow-x-auto rounded-xl bg-slate-100 p-1" role="tablist">
      {tabs.map(([key, label]) => (
        <button key={key} role="tab" aria-selected={value === key} onClick={() => onChange(key)}
          className={`whitespace-nowrap rounded-lg px-3.5 py-1.5 text-sm font-medium transition ${value === key ? 'bg-white text-ink shadow-sm' : 'text-slate-600 hover:text-ink'}`}>
          {label}
        </button>
      ))}
    </div>
  )
}

export function Stars({ value = 0, size = 14, onChange }) {
  return (
    <span className="inline-flex items-center gap-0.5" aria-label={`${value} out of 5 stars`}>
      {[1, 2, 3, 4, 5].map((n) => {
        const fill = n <= Math.round(value)
        const icon = <Star size={size} className={fill ? 'fill-saffron-400 text-saffron-400' : 'text-slate-300'} />
        return onChange ? (
          <button key={n} type="button" onClick={() => onChange(n)} aria-label={`${n} star${n > 1 ? 's' : ''}`} className="p-0.5">{icon}</button>
        ) : <span key={n}>{icon}</span>
      })}
    </span>
  )
}

export function ScoreRing({ score, size = 64 }) {
  const r = (size - 8) / 2
  const c = 2 * Math.PI * r
  const color = score >= 80 ? '#05916d' : score >= 60 ? '#fb8f1f' : '#e11d48'
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} aria-label={`Match score ${score} out of 100`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#e2e8f0" strokeWidth="6" fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth="6" fill="none" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - score / 100)} style={{ transition: 'stroke-dashoffset .8s ease' }} />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-sm font-bold">{Math.round(score)}</span>
    </div>
  )
}

export function Stat({ icon: Icon, label, value, hint, tone = 'brand' }) {
  const tones = { brand: 'bg-brand-50 text-brand-700', saffron: 'bg-saffron-50 text-saffron-600', sky: 'bg-sky-50 text-sky-700', violet: 'bg-violet-50 text-violet-700' }
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card">
      <div className="flex items-center gap-3">
        <div className={`rounded-xl p-2.5 ${tones[tone]}`}><Icon size={20} /></div>
        <p className="text-sm text-slate-500">{label}</p>
      </div>
      <p className="mt-3 font-display text-2xl font-bold">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
    </div>
  )
}

export function PageHeader({ title, subtitle, action, eyebrow }) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-brand-600">{eyebrow}</p>}
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{title}</h1>
        {subtitle && <p className="mt-2 max-w-2xl text-slate-600">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
