import { Clock, IndianRupee, MapPin, Umbrella } from 'lucide-react'
import { useState } from 'react'
import useApi from '../hooks/useApi'
import { destinations } from '../services/api'
import { inr, minutesLabel, titleCase } from '../utils/format'
import { EmptyState, ErrorState, Skeleton, SourceBadge, Stars, Tabs } from './ui'

const KINDS = [['attraction', 'Attractions'], ['restaurant', 'Restaurants'], ['activity', 'Activities'], ['shopping', 'Shopping']]

export default function PlacesPanel({ destinationId, initialKind = 'attraction', limit }) {
  const [kind, setKind] = useState(initialKind)
  const { data, error, loading, reload } = useApi(() => destinations.places(destinationId, { kind }), [destinationId, kind])
  const items = data?.items?.slice(0, limit) || []
  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Tabs tabs={KINDS} value={kind} onChange={setKind} />
        {data && <SourceBadge source={data.source} note={data.note} />}
      </div>
      {loading ? (
        <div className="grid gap-3 sm:grid-cols-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}</div>
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : items.length === 0 ? (
        <EmptyState title={`No ${kind} listed yet`}>Try another category.</EmptyState>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {items.map((p) => (
            <li key={p.id ?? p.external_id} className="flex gap-3 rounded-xl border border-slate-200 bg-white p-3">
              {p.photo && <img src={p.photo} alt="" loading="lazy" className="h-20 w-20 shrink-0 rounded-lg object-cover" />}
              <div className="min-w-0">
                <p className="font-semibold">{p.name}</p>
                <div className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-slate-500">
                  {p.rating && <span className="flex items-center gap-1"><Stars value={p.rating} size={11} />{p.rating}</span>}
                  <span className="flex items-center gap-0.5"><MapPin size={11} />{p.distance_km} km</span>
                  {p.duration_minutes && <span className="flex items-center gap-0.5"><Clock size={11} />{minutesLabel(p.duration_minutes)}</span>}
                  {p.estimated_cost != null && <span className="flex items-center gap-0.5"><IndianRupee size={11} />{p.estimated_cost ? inr(p.estimated_cost).slice(1) : 'Free'}</span>}
                  {p.is_indoor && <span className="flex items-center gap-0.5"><Umbrella size={11} />Indoor</span>}
                </div>
                {p.description && <p className="mt-1 line-clamp-2 text-xs text-slate-600">{p.description}</p>}
                {!p.description && p.address && <p className="mt-1 line-clamp-1 text-xs text-slate-500">{p.address} · {titleCase(p.category)}</p>}
              </div>
            </li>
          ))}
        </ul>
      )}
      {data?.note && data.source !== 'google_places' && <p className="mt-3 text-xs text-slate-500">{data.note}</p>}
    </div>
  )
}
