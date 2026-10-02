import { ArrowRight, CalendarDays, Check, ChevronDown, Cpu, Info, MapPin, Sparkles, TriangleAlert } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import DestinationCover from '../components/DestinationCover'
import MapView from '../components/MapView'
import { Badge, Button, Card, EmptyState, PageHeader, ScoreRing } from '../components/ui'
import useGenerateTrip from '../hooks/useGenerateTrip'
import { categoryMeta, inr, seasonLabel, titleCase } from '../utils/format'
import { LAST_PLAN_KEY } from './PlanTrip'

const COMPONENT_LABEL = {
  interest: 'Interest match', semantic: 'AI text similarity', type: 'Destination type', budget: 'Budget fit',
  duration: 'Trip length', season: 'Season', activity: 'Activities available', hotel: 'Hotel availability', popularity: 'Popularity',
}

function ScoreBreakdown({ components, weights }) {
  return (
    <div className="mt-4 grid gap-x-6 gap-y-2 sm:grid-cols-2">
      {Object.entries(components).map(([k, v]) => (
        <div key={k}>
          <div className="flex justify-between text-xs"><span className="text-slate-600">{COMPONENT_LABEL[k] || k}</span><span className="text-slate-500">{Math.round(v)} × {Math.round((weights?.[k] || 0) * 100)}%</span></div>
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-brand-500" style={{ width: `${v}%` }} /></div>
        </div>
      ))}
    </div>
  )
}

function RecommendationCard({ r, rank, weights, onPlan, busy }) {
  const [open, setOpen] = useState(false)
  const meta = categoryMeta(r.category)
  return (
    <article className="animate-fade-up overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-card" style={{ animationDelay: `${rank * 60}ms` }}>
      <div className="grid sm:grid-cols-[220px_1fr]">
        <DestinationCover destination={r} className="h-36 sm:h-full">
          <span className="absolute left-3 top-3 rounded-full bg-white/90 px-2.5 py-0.5 text-xs font-bold text-ink">#{rank}</span>
          <span className="absolute bottom-3 left-3 rounded-full bg-black/30 px-2.5 py-0.5 text-xs text-white backdrop-blur">{meta.label}</span>
        </DestinationCover>
        <div className="p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold">{r.destination} <span className="text-base font-normal text-slate-500">— {Math.round(r.score)}/100</span></h2>
              <p className="flex items-center gap-1 text-sm text-slate-500"><MapPin size={13} />{r.state}</p>
            </div>
            <ScoreRing score={r.score} />
          </div>

          <ul className="mt-3 space-y-1">
            {r.reasons.map((x) => <li key={x} className="flex items-start gap-2 text-sm"><Check size={16} className="mt-0.5 shrink-0 text-brand-600" />{x}</li>)}
            {r.warnings.map((x) => <li key={x} className="flex items-start gap-2 text-sm text-amber-700"><TriangleAlert size={15} className="mt-0.5 shrink-0" />{x}</li>)}
          </ul>

          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
            <Badge tone="brand">Est. {inr(r.estimated_cost.minimum)} – {inr(r.estimated_cost.maximum)}</Badge>
            <Badge><CalendarDays size={12} />Best: {seasonLabel(r.best_seasons)}</Badge>
            <Badge tone="violet">Confidence {Math.round(r.confidence * 100)}%</Badge>
          </div>

          <button onClick={() => setOpen(!open)} className="mt-3 flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-ink" aria-expanded={open}>
            Why this score? <ChevronDown size={14} className={`transition ${open ? 'rotate-180' : ''}`} />
          </button>
          {open && <ScoreBreakdown components={r.components} weights={weights} />}

          <div className="mt-5 flex flex-wrap gap-2">
            <Button onClick={() => onPlan(r)} loading={busy}><Sparkles size={16} />Plan this trip</Button>
            <Link to={`/destination/${r.destination_id}`} className="inline-flex items-center gap-1 rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-100">Explore {r.destination}<ArrowRight size={15} /></Link>
          </div>
        </div>
      </div>
    </article>
  )
}

export default function Recommendations() {
  const location = useLocation()
  const saved = useMemo(() => {
    if (location.state?.result) return location.state
    try { return JSON.parse(sessionStorage.getItem(LAST_PLAN_KEY)) } catch { return null }
  }, [location.state])
  const { generate, overlay, busy } = useGenerateTrip()
  const recs = useMemo(() => saved?.result?.recommendations || [], [saved])
  const markers = useMemo(() => recs.map((r, i) => ({ lat: r.latitude, lng: r.longitude, label: `#${i + 1} ${r.destination}`, sub: `${Math.round(r.score)}/100`, kind: 'stop', order: i + 1 })), [recs])

  if (!saved?.result) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <EmptyState icon={Sparkles} title="No recommendations yet" action={<Link to="/plan-trip"><Button>Plan a trip</Button></Link>}>
          Tell us your budget, dates and interests to get personalised destination matches.
        </EmptyState>
      </main>
    )
  }

  const { request, result } = saved
  const summary = [
    request.destination_types?.map(titleCase).join(', '),
    request.interests?.length && request.interests.join(', '),
    `${request.duration} days`, `${request.travelers} traveller${request.travelers > 1 ? 's' : ''}`, `up to ${inr(request.budget)}`,
  ].filter(Boolean).join(' · ')

  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <PageHeader eyebrow="Your matches" title="Recommended destinations" subtitle={summary}
        action={<Link to="/plan-trip"><Button variant="secondary">Refine preferences</Button></Link>} />
      {result.notes?.map((n) => <p key={n} className="mb-4 flex items-center gap-2 rounded-xl bg-amber-50 p-3 text-sm text-amber-800"><Info size={16} />{n}</p>)}
      <div className="grid *:min-w-0 gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-5">
          {recs.length === 0
            ? <EmptyState title="No destination matched">Try a larger budget, more days or fewer constraints.</EmptyState>
            : recs.map((r, i) => <RecommendationCard key={r.destination_id} r={r} rank={i + 1} weights={result.engine.weights} busy={busy}
                onPlan={() => generate({ ...request, destination_id: r.destination_id })} />)}
        </div>
        <aside className="space-y-5 lg:sticky lg:top-24 lg:self-start">
          <Card title="On the map"><MapView markers={markers} className="h-64" zoom={5} /></Card>
          <Card title="How the AI ranked these">
            <p className="text-sm text-slate-600">Each destination gets nine component scores, combined with the weights below. Off-season destinations lose 20%.</p>
            <ul className="mt-3 space-y-1 text-xs text-slate-600">
              {Object.entries(result.engine.weights).map(([k, w]) => <li key={k} className="flex justify-between"><span>{COMPONENT_LABEL[k]}</span><span>{Math.round(w * 100)}%</span></li>)}
            </ul>
            <p className="mt-4 flex items-start gap-2 rounded-xl bg-slate-50 p-3 text-xs text-slate-500"><Cpu size={14} className="mt-0.5 shrink-0" />
              Embeddings: {result.engine.embedding} · Index: {result.engine.index}</p>
            <p className="mt-2 text-xs text-slate-400">Query: “{result.query}”</p>
          </Card>
        </aside>
      </div>
      {overlay}
    </main>
  )
}
