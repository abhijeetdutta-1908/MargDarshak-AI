import { BedDouble, Check, MapPin } from 'lucide-react'
import { Link } from 'react-router-dom'
import { inr, titleCase } from '../utils/format'
import { Badge, Stars } from './ui'

const TIER_TONE = { budget: 'slate', standard: 'sky', premium: 'violet', luxury: 'amber' }

export default function HotelCard({ h, highlight = false, reasons = h.reasons, nights }) {
  return (
    <div className={`rounded-2xl border p-4 transition ${highlight ? 'border-brand-300 bg-brand-50/40 ring-2 ring-brand-100' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={TIER_TONE[h.tier]}>{titleCase(h.tier)}</Badge>
            {highlight && <Badge tone="brand">Selected for your trip</Badge>}
            {h.score != null && <span className="text-xs text-slate-500">Match {Math.round(h.score)}/100</span>}
          </div>
          <Link to={`/hotel/${h.id}`} className="mt-1.5 block font-semibold hover:text-brand-700">{h.name}</Link>
          <p className="mt-0.5 flex items-center gap-1 text-xs text-slate-500"><MapPin size={12} />{h.address}</p>
          <div className="mt-1 flex items-center gap-1.5 text-xs"><Stars value={h.rating} size={12} /><span className="text-slate-600">{h.rating}</span></div>
        </div>
        <div className="shrink-0 text-right">
          <p className="font-display text-lg font-bold">{inr(h.price_per_night)}</p>
          <p className="text-xs text-slate-500">per night</p>
          {nights > 0 && <p className="mt-1 text-xs text-slate-500"><BedDouble size={12} className="mr-1 inline" />{nights} nights</p>}
        </div>
      </div>
      {reasons?.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
          {reasons.map((r) => <li key={r} className="flex items-center gap-1 text-xs text-brand-700"><Check size={12} />{r}</li>)}
        </ul>
      )}
      <p className="mt-3 line-clamp-1 text-xs text-slate-500">{h.amenities?.join(' · ')}</p>
    </div>
  )
}
