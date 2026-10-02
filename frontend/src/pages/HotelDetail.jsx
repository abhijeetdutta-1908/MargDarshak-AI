import { ArrowLeft, Check, Info, MapPin } from 'lucide-react'
import { useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'
import MapView from '../components/MapView'
import { Badge, Card, ErrorState, Skeleton, Stars } from '../components/ui'
import useApi from '../hooks/useApi'
import { destinations } from '../services/api'
import { inr, titleCase } from '../utils/format'

export default function HotelDetail() {
  const { id } = useParams()
  const { data: h, error, loading, reload } = useApi(() => destinations.hotel(id), [id])
  const nearby = useApi(() => (h ? destinations.places(h.destination_id, { kind: 'attraction', lat: h.latitude, lng: h.longitude }) : Promise.resolve(null)), [h?.id])
  const markers = useMemo(() => h ? [
    { lat: h.latitude, lng: h.longitude, label: h.name, kind: 'hotel' },
    ...(nearby.data?.items?.slice(0, 8).map((p) => ({ lat: p.latitude, lng: p.longitude, label: p.name, sub: `${p.distance_km} km from hotel`, kind: 'attraction' })) || []),
  ] : [], [h, nearby.data])

  if (loading) return <main className="mx-auto max-w-5xl px-4 py-10"><Skeleton className="h-64" /></main>
  if (error) return <main className="mx-auto max-w-3xl px-4 py-16"><ErrorState message={error} onRetry={reload} /></main>

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <Link to={`/destination/${h.destination_id}`} className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-ink"><ArrowLeft size={15} />{h.destination_name}</Link>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Badge tone="sky">{titleCase(h.tier)}</Badge>
          <h1 className="mt-2 text-3xl font-bold">{h.name}</h1>
          <p className="mt-1 flex items-center gap-1 text-slate-500"><MapPin size={15} />{h.address}</p>
          <div className="mt-2 flex items-center gap-2"><Stars value={h.rating} /><span className="text-sm text-slate-600">{h.rating} / 5</span></div>
        </div>
        <div className="rounded-2xl bg-white p-5 text-right shadow-card">
          <p className="font-display text-3xl font-bold">{inr(h.price_per_night)}</p>
          <p className="text-sm text-slate-500">estimated per night</p>
        </div>
      </div>
      <p className="mt-5 flex items-start gap-2 rounded-xl bg-amber-50 p-3 text-sm text-amber-800"><Info size={16} className="mt-0.5 shrink-0" />{h.note}</p>
      <div className="mt-6 grid *:min-w-0 gap-6 lg:grid-cols-[1fr_1.3fr]">
        <Card title="Amenities">
          <ul className="grid grid-cols-2 gap-2">{h.amenities.map((a) => <li key={a} className="flex items-center gap-2 text-sm"><Check size={15} className="text-brand-600" />{a}</li>)}</ul>
        </Card>
        <Card title="Location & nearby sights"><MapView markers={markers} className="h-72" /></Card>
      </div>
    </main>
  )
}
