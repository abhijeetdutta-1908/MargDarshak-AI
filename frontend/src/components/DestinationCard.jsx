import { CalendarDays, MapPin, Wallet } from 'lucide-react'
import { Link } from 'react-router-dom'
import { categoryMeta, inr, seasonLabel } from '../utils/format'
import DestinationCover from './DestinationCover'

export default function DestinationCard({ d }) {
  const meta = categoryMeta(d.category)
  return (
    <Link to={`/destination/${d.id}`}
      className="group block overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-card transition hover:-translate-y-0.5 hover:shadow-lift">
      <DestinationCover destination={d} className="h-40">
        <span className="absolute left-3 top-3 rounded-full bg-white/90 px-2.5 py-0.5 text-xs font-semibold text-ink">{meta.label}</span>
        <div className="absolute bottom-3 left-4 text-white">
          <h3 className="text-xl font-bold drop-shadow">{d.name}</h3>
          <p className="flex items-center gap-1 text-xs text-white/85"><MapPin size={12} />{d.state}</p>
        </div>
      </DestinationCover>
      <div className="space-y-3 p-4">
        <p className="line-clamp-2 text-sm text-slate-600">{d.description}</p>
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-1"><CalendarDays size={13} />{seasonLabel(d.best_seasons)}</span>
          <span className="flex items-center gap-1"><Wallet size={13} />~{inr(d.average_daily_cost)}/day</span>
        </div>
      </div>
    </Link>
  )
}
