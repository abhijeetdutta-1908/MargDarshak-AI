import { CalendarDays, Info, Lightbulb, MapPin, Route, Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import BudgetBreakdown from './BudgetBreakdown'
import DestinationCover from './DestinationCover'
import HotelCard from './HotelCard'
import ItineraryTimeline, { RouteSummary } from './ItineraryTimeline'
import MapView from './MapView'
import PlacesPanel from './PlacesPanel'
import { Card, SourceBadge, Tabs } from './ui'
import { WeatherView } from './WeatherCard'
import { DAY_COLORS, MONTHS_LONG, formatDate, inr, seasonLabel } from '../utils/format'

const STOP_KINDS = ['attraction', 'activity', 'shopping', 'meal']

export function tripMapData(trip, dayFilter = null) {
  const markers = []
  const routes = []
  if (trip.hotel) markers.push({ lat: trip.hotel.latitude, lng: trip.hotel.longitude, label: trip.hotel.name, sub: 'Your hotel', kind: 'hotel' })
  trip.days.filter((d) => dayFilter == null || d.day_number === dayFilter).forEach((d) => {
    const color = DAY_COLORS[(d.day_number - 1) % DAY_COLORS.length]
    const stops = d.items.filter((i) => STOP_KINDS.includes(i.category) && i.latitude != null && i.place_id)
    stops.forEach((s, idx) => markers.push({ lat: s.latitude, lng: s.longitude, label: s.title, sub: `Day ${d.day_number} · ${s.start_time}`,
      kind: s.category === 'meal' ? 'restaurant' : 'stop', order: dayFilter != null ? idx + 1 : d.day_number, color: s.category === 'meal' ? undefined : color }))
    const pts = d.items.filter((i) => i.latitude != null).map((i) => [i.latitude, i.longitude])
    routes.push({ points: pts, color, label: `Day ${d.day_number}` })
  })
  return { markers, routes }
}

function travelTips(trip) {
  const tips = []
  const d = trip.destination
  const month = trip.start_date ? new Date(trip.start_date).getMonth() + 1 : null
  tips.push(`Best time to visit ${d.name}: ${seasonLabel(d.best_seasons)}.`)
  if (month && !d.best_seasons.includes(month)) tips.push(`${MONTHS_LONG[month - 1]} is outside the best season, so book flexible tickets and keep a backup plan.`)
  if (trip.days.some((x) => x.rain_likely)) tips.push('Rain is likely on some days: pack a light rain jacket and waterproof bag.')
  if (d.tags.some((t) => ['mountains', 'snow', 'trekking'].includes(t))) tips.push('Mountain weather changes fast. Carry layers, and acclimatise if you are going high.')
  if (d.tags.some((t) => ['temple', 'temples', 'spiritual', 'buddhism', 'ghats'].includes(t))) tips.push('Dress modestly at religious sites. Some temples restrict photography or entry.')
  if (d.tags.includes('beach')) tips.push('Follow lifeguard flags. Some beaches have strong currents.')
  if (d.category === 'wildlife') tips.push('Safari slots sell out. Book with the official forest department portal well ahead.')
  if (trip.unscheduled?.length) tips.push(`Didn't fit: ${trip.unscheduled.join(', ')}. Add a day if these matter to you.`)
  return tips
}

export default function TripView({ trip, actions, readOnly = false }) {
  const [tab, setTab] = useState('itinerary')
  const { markers, routes } = useMemo(() => tripMapData(trip), [trip])
  const d = trip.destination
  const nights = Math.max(1, trip.duration_days - 1)

  return (
    <main className="pb-16">
      <DestinationCover destination={d} className="h-64 sm:h-72" size="lg">
        <div className="absolute inset-x-0 bottom-0 mx-auto max-w-6xl px-4 pb-7 text-white">
          <p className="text-sm text-white/80">{readOnly ? 'Shared trip plan' : trip.is_saved ? 'Saved trip' : 'Draft plan, not saved yet'}</p>
          <h1 className="mt-1 text-3xl font-extrabold drop-shadow sm:text-4xl">{trip.title}</h1>
          <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-white/90">
            <Link to={`/destination/${d.id}`} className="flex items-center gap-1 hover:underline"><MapPin size={14} />{d.name}, {d.state}</Link>
            <span className="flex items-center gap-1"><CalendarDays size={14} />{trip.start_date ? `${formatDate(trip.start_date)} · ` : ''}{trip.duration_days} days</span>
            <span className="flex items-center gap-1"><Users size={14} />{trip.travelers} traveller{trip.travelers > 1 ? 's' : ''}</span>
            <span>Est. {inr(trip.budget.average)}</span>
          </div>
        </div>
      </DestinationCover>

      {actions && <div className="sticky top-16 z-20 border-b border-slate-200 bg-white/90 backdrop-blur"><div className="mx-auto flex max-w-6xl flex-wrap gap-2 px-4 py-3">{actions}</div></div>}

      <div className="mx-auto mt-6 grid *:min-w-0 max-w-6xl gap-6 px-4 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          {trip.explanations?.length > 0 && (
            <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900">
              <p className="mb-1 flex items-center gap-2 font-semibold"><Info size={16} />How the plan adapted</p>
              <ul className="list-disc space-y-0.5 pl-6">{trip.explanations.map((e) => <li key={e}>{e}</li>)}</ul>
            </div>
          )}
          <Card title="Route & map" action={<RouteSummary route={trip.route} />}>
            <MapView markers={markers} routes={routes} className="h-96" />
            <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500">
              {trip.days.map((x) => <span key={x.id} className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: DAY_COLORS[(x.day_number - 1) % DAY_COLORS.length] }} />Day {x.day_number}</span>)}
            </div>
          </Card>

          <Card>
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <Tabs tabs={[['itinerary', 'Day-wise itinerary'], ['places', 'Attractions & restaurants']]} value={tab} onChange={setTab} />
              {!readOnly && tab === 'itinerary' && <Link to={`/itinerary/${trip.id}`} className="text-sm font-medium text-brand-700 hover:underline">Open full itinerary →</Link>}
            </div>
            {tab === 'itinerary' ? (
              <div className="space-y-8">{trip.days.map((day) => <ItineraryTimeline key={day.id} day={day} color={DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length]} />)}</div>
            ) : <PlacesPanel destinationId={d.id} />}
          </Card>
        </div>

        <aside className="space-y-6">
          <Card title="Estimated budget"><BudgetBreakdown budget={trip.budget} /></Card>
          {trip.hotel && (
            <Card title="Your hotel" action={<SourceBadge source="sample" note="Sample listing, not live availability" />}>
              <HotelCard h={trip.hotel} highlight reasons={trip.budget.hotel_reasons} nights={nights} />
            </Card>
          )}
          <Card title="Weather" action={<SourceBadge source={trip.weather.source} note={trip.weather.note} />}><WeatherView w={trip.weather} /></Card>
          <Card title="Travel tips">
            <ul className="space-y-2 text-sm text-slate-700">{travelTips(trip).map((t) => <li key={t} className="flex gap-2"><Lightbulb size={16} className="mt-0.5 shrink-0 text-saffron-500" />{t}</li>)}</ul>
          </Card>
          {trip.recommendations?.length > 1 && !readOnly && (
            <Card title="Other good matches">
              <ul className="space-y-2">{trip.recommendations.filter((r) => r.destination_id !== d.id).slice(0, 3).map((r) => (
                <li key={r.destination_id}><Link to={`/destination/${r.destination_id}`} className="flex items-center justify-between rounded-xl p-2 text-sm hover:bg-slate-50"><span className="flex items-center gap-2"><Route size={15} className="text-slate-400" />{r.destination}</span><span className="text-slate-500">{Math.round(r.score)}/100</span></Link></li>
              ))}</ul>
            </Card>
          )}
        </aside>
      </div>
    </main>
  )
}
