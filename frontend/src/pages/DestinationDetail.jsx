import { ArrowLeft, CalendarDays, Clock, MapPin, Sparkles, Star, Wallet } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import DestinationCover from '../components/DestinationCover'
import HotelCard from '../components/HotelCard'
import MapView from '../components/MapView'
import PlacesPanel from '../components/PlacesPanel'
import ReviewSection from '../components/ReviewSection'
import WeatherCard from '../components/WeatherCard'
import { Badge, Button, Card, ErrorState, Field, Modal, Skeleton, inputClass } from '../components/ui'
import useApi from '../hooks/useApi'
import useGenerateTrip from '../hooks/useGenerateTrip'
import { destinations } from '../services/api'
import { categoryMeta, inr, seasonLabel, titleCase } from '../utils/format'
import { todayISO } from '../utils/plan'

function QuickPlan({ dest, open, onClose, onPlan, busy }) {
  const [f, setF] = useState({ duration: Math.min(dest.ideal_max_days, Math.max(dest.ideal_min_days, 3)), travelers: 2, budget: '', travel_date: '' })
  const budget = f.budget || dest.average_daily_cost * f.duration * f.travelers
  return (
    <Modal open={open} onClose={onClose} title={`Plan a trip to ${dest.name}`}
      footer={<Button loading={busy} onClick={() => onPlan({ destination_id: dest.id, duration: Number(f.duration), travelers: Number(f.travelers), budget: Number(budget), travel_date: f.travel_date || null, destination_types: [dest.category] })}><Sparkles size={16} />Build itinerary</Button>}>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Days"><input type="number" min={1} max={30} className={inputClass} value={f.duration} onChange={(e) => setF({ ...f, duration: e.target.value })} /></Field>
        <Field label="Travellers"><input type="number" min={1} max={50} className={inputClass} value={f.travelers} onChange={(e) => setF({ ...f, travelers: e.target.value })} /></Field>
        <Field label="Budget (₹)" hint={f.budget ? null : `Suggested ${inr(budget)}`}><input type="number" min={1} className={inputClass} value={f.budget} placeholder={String(budget)} onChange={(e) => setF({ ...f, budget: e.target.value })} /></Field>
        <Field label="Start date"><input type="date" min={todayISO()} className={inputClass} value={f.travel_date} onChange={(e) => setF({ ...f, travel_date: e.target.value })} /></Field>
      </div>
      <p className="mt-3 text-xs text-slate-500">For full personalisation (interests, hotel tier, transport) use <Link to="/plan-trip" className="text-brand-700">Plan Trip</Link>.</p>
    </Modal>
  )
}

export default function DestinationDetail() {
  const { id } = useParams()
  const dest = useApi(() => destinations.get(id), [id])
  const hotels = useApi(() => destinations.hotels(id, { preferred_tier: 'standard' }), [id])
  const attractions = useApi(() => destinations.places(id, { kind: 'attraction' }), [id])
  const { generate, overlay, busy } = useGenerateTrip()
  const [planning, setPlanning] = useState(false)

  const markers = useMemo(() => {
    if (!dest.data) return []
    const m = [{ lat: dest.data.latitude, lng: dest.data.longitude, label: dest.data.name, kind: 'destination' }]
    attractions.data?.items?.slice(0, 12).forEach((p) => m.push({ lat: p.latitude, lng: p.longitude, label: p.name, sub: `${p.distance_km} km away`, kind: 'attraction' }))
    hotels.data?.items?.forEach((h) => m.push({ lat: h.latitude, lng: h.longitude, label: h.name, sub: `${inr(h.price_per_night)}/night`, kind: 'hotel' }))
    return m
  }, [dest.data, attractions.data, hotels.data])

  if (dest.loading) return <main className="mx-auto max-w-6xl px-4 py-10"><Skeleton className="h-72" /><Skeleton className="mt-6 h-40" /></main>
  if (dest.error) return <main className="mx-auto max-w-3xl px-4 py-16"><ErrorState message={dest.error} onRetry={dest.reload} /></main>
  const d = dest.data
  const meta = categoryMeta(d.category)

  return (
    <main>
      <DestinationCover destination={d} className="h-72 sm:h-80" size="lg">
        <div className="absolute inset-x-0 bottom-0 mx-auto max-w-6xl px-4 pb-8 text-white">
          <Link to="/explore" className="mb-4 inline-flex items-center gap-1 text-sm text-white/80 hover:text-white"><ArrowLeft size={15} />All destinations</Link>
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold backdrop-blur">{meta.label}</span>
              <h1 className="mt-2 text-4xl font-extrabold drop-shadow sm:text-5xl">{d.name}</h1>
              <p className="mt-1 flex items-center gap-1 text-white/85"><MapPin size={15} />{d.state}, {d.country}
                {d.average_rating && <span className="ml-3 flex items-center gap-1"><Star size={14} className="fill-saffron-400 text-saffron-400" />{d.average_rating} ({d.review_count})</span>}</p>
            </div>
            <Button variant="accent" size="lg" onClick={() => setPlanning(true)}><Sparkles size={18} />Plan a trip here</Button>
          </div>
        </div>
      </DestinationCover>

      <div className="mx-auto grid *:min-w-0 max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          <Card title="Overview">
            <p className="leading-relaxed text-slate-700">{d.description}</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl bg-slate-50 p-3"><p className="flex items-center gap-1 text-xs text-slate-500"><CalendarDays size={13} />Best time</p><p className="font-semibold">{seasonLabel(d.best_seasons)}</p></div>
              <div className="rounded-xl bg-slate-50 p-3"><p className="flex items-center gap-1 text-xs text-slate-500"><Clock size={13} />Ideal stay</p><p className="font-semibold">{d.ideal_min_days}–{d.ideal_max_days} days</p></div>
              <div className="rounded-xl bg-slate-50 p-3"><p className="flex items-center gap-1 text-xs text-slate-500"><Wallet size={13} />Typical spend</p><p className="font-semibold">{inr(d.average_daily_cost)} / person / day</p></div>
            </div>
            <div className="mt-4 flex flex-wrap gap-1.5">{d.tags.map((t) => <Badge key={t}>{titleCase(t)}</Badge>)}</div>
            <p className="mt-4 text-xs text-slate-400">{d.cost_note}</p>
          </Card>
          <Card title="Things to do & places to eat"><PlacesPanel destinationId={d.id} /></Card>
          <Card title="Map" subtitle="Destination, top attractions and hotels"><MapView markers={markers} className="h-96" /></Card>
          <Card title="Reviews"><ReviewSection destinationId={d.id} /></Card>
        </div>
        <aside className="space-y-6">
          <WeatherCard destinationId={d.id} />
          <Card title="Hotels" subtitle={hotels.data?.note}>
            {hotels.loading ? <Skeleton className="h-40" /> : hotels.error ? <ErrorState message={hotels.error} onRetry={hotels.reload} /> : (
              <div className="space-y-3">{hotels.data.items.map((h) => <HotelCard key={h.id} h={h} reasons={[]} />)}</div>
            )}
          </Card>
        </aside>
      </div>
      <QuickPlan dest={d} open={planning} onClose={() => setPlanning(false)} busy={busy} onPlan={(req) => { setPlanning(false); generate(req) }} />
      {overlay}
    </main>
  )
}
