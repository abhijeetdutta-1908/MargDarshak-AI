import { ArrowLeft, Printer } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ItineraryTimeline, { RouteSummary } from '../components/ItineraryTimeline'
import MapView from '../components/MapView'
import { tripMapData } from '../components/TripView'
import { Button, Card, ErrorState, PageHeader, Skeleton, Tabs } from '../components/ui'
import useApi from '../hooks/useApi'
import { trips } from '../services/api'
import { DAY_COLORS, formatDate, inr } from '../utils/format'

export default function Itinerary() {
  const { id } = useParams()
  const { data: trip, error, loading, reload } = useApi(() => trips.get(id), [id])
  const [day, setDay] = useState('all')
  const map = useMemo(() => (trip ? tripMapData(trip, day === 'all' ? null : Number(day)) : { markers: [], routes: [] }), [trip, day])

  if (loading) return <main className="mx-auto max-w-6xl px-4 py-10"><Skeleton className="h-96" /></main>
  if (error) return <main className="mx-auto max-w-3xl px-4 py-16"><ErrorState message={error} onRetry={reload} /></main>
  const shown = day === 'all' ? trip.days : trip.days.filter((d) => d.day_number === Number(day))
  const total = (d) => d.items.reduce((s, i) => s + i.estimated_cost, 0)

  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <Link to={`/trip/${trip.id}`} className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-ink print:hidden"><ArrowLeft size={15} />Back to trip</Link>
      <PageHeader eyebrow={trip.destination.name} title={trip.title}
        subtitle={`${trip.start_date ? formatDate(trip.start_date) + ' · ' : ''}${trip.duration_days} days · ${trip.travelers} traveller${trip.travelers > 1 ? 's' : ''}`}
        action={<Button variant="secondary" onClick={() => window.print()} className="print:hidden"><Printer size={16} />Print</Button>} />
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3 print:hidden">
        <Tabs tabs={[['all', 'All days'], ...trip.days.map((d) => [String(d.day_number), `Day ${d.day_number}`])]} value={day} onChange={setDay} />
        <RouteSummary route={trip.route} />
      </div>
      <div className="grid *:min-w-0 gap-6 lg:grid-cols-[1fr_400px]">
        <div className="space-y-6">
          {shown.map((d) => (
            <Card key={d.id}>
              <ItineraryTimeline day={d} color={DAY_COLORS[(d.day_number - 1) % DAY_COLORS.length]} />
              <p className="mt-4 border-t border-slate-100 pt-3 text-right text-sm text-slate-600">Day spend on sights & meals: <strong>{inr(total(d))}</strong></p>
            </Card>
          ))}
        </div>
        <div className="lg:sticky lg:top-24 lg:self-start print:hidden">
          <Card title={day === 'all' ? 'Whole trip' : `Day ${day} route`}><MapView markers={map.markers} routes={map.routes} className="h-[28rem]" /></Card>
        </div>
      </div>
    </main>
  )
}
