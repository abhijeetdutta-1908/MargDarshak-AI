import { Car, CloudRain, Clock, MapPin, Sun } from 'lucide-react'
import { ITEM_STYLE, formatDate, inr, minutesLabel } from '../utils/format'
import { SourceBadge } from './ui'

export function DayHeader({ day, color }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl font-display text-lg font-bold text-white" style={{ background: color }}>{day.day_number}</span>
        <div>
          <p className="font-semibold">{day.title || `Day ${day.day_number}`}</p>
          <p className="text-xs text-slate-500">{day.date ? formatDate(day.date, { weekday: 'long', day: 'numeric', month: 'short' }) : `Day ${day.day_number}`} · {day.total_distance_km} km · {minutesLabel(day.total_travel_minutes)} travel</p>
        </div>
      </div>
      <span className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs ${day.rain_likely ? 'bg-sky-50 text-sky-700' : 'bg-amber-50 text-amber-700'}`}>
        {day.rain_likely ? <CloudRain size={13} /> : <Sun size={13} />}{day.weather_note}
        {day.weather_source && <span className="opacity-70">· {day.weather_source === 'forecast' ? 'forecast' : 'seasonal'}</span>}
      </span>
    </div>
  )
}

export default function ItineraryTimeline({ day, color = '#05916d', compact = false }) {
  return (
    <div>
      <DayHeader day={day} color={color} />
      <ol className="relative mt-4 ml-5 border-l-2 border-dashed border-slate-200">
        {day.items.map((it) => {
          const style = ITEM_STYLE[it.category] || ITEM_STYLE.attraction
          const sight = ['attraction', 'activity', 'shopping'].includes(it.category)
          return (
            <li key={it.id ?? `${it.start_time}-${it.title}`} className="relative mb-1 pl-6">
              {it.travel_minutes > 4 && !compact && (
                <p className="mb-1 -ml-1 flex items-center gap-1 text-[11px] text-slate-400"><Car size={11} />{minutesLabel(it.travel_minutes)}</p>
              )}
              <span className={`absolute -left-[7px] top-2.5 h-3 w-3 rounded-full ring-4 ring-white ${style.dot}`} />
              <div className={`rounded-xl px-3 py-2 ${sight ? 'bg-slate-50' : ''}`}>
                <div className="flex flex-wrap items-baseline gap-x-3">
                  <span className="w-24 shrink-0 font-mono text-xs text-slate-500">{it.start_time}–{it.end_time}</span>
                  <span className={`text-sm ${sight ? 'font-semibold' : 'text-slate-700'}`}>{it.title}</span>
                  {it.estimated_cost > 0 && <span className="text-xs text-slate-500">{inr(it.estimated_cost)}</span>}
                </div>
                {!compact && sight && it.description && <p className="mt-1 text-xs text-slate-500 sm:ml-[108px]">{it.description}</p>}
                {!compact && sight && it.location && it.location !== it.title && (
                  <p className="mt-0.5 flex items-center gap-1 text-[11px] text-slate-400 sm:ml-[108px]"><MapPin size={11} />{it.location} · <Clock size={11} />{minutesLabel(it.duration_minutes)}</p>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

export function RouteSummary({ route }) {
  if (!route) return null
  return (
    <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
      <span><strong className="text-ink">{route.total_distance_km} km</strong> total travel</span>
      <span>·</span>
      <span><strong className="text-ink">{minutesLabel(route.total_travel_minutes)}</strong> on the move</span>
      <SourceBadge source={route.source} note={route.note} />
    </div>
  )
}
