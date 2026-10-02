import { ArrowRight, Bookmark, CalendarClock, Heart, History, Plus, Sparkles, Wallet } from 'lucide-react'
import { Link } from 'react-router-dom'
import DestinationCover from '../components/DestinationCover'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, Skeleton, Stat } from '../components/ui'
import WeatherCard from '../components/WeatherCard'
import { useAuth } from '../context/AuthContext'
import useApi from '../hooks/useApi'
import { trips } from '../services/api'
import { categoryMeta, formatDate, inr } from '../utils/format'

export function TripRow({ t }) {
  return (
    <Link to={`/trip/${t.id}`} className="flex items-center gap-4 rounded-xl p-2 transition hover:bg-slate-50">
      <DestinationCover destination={t.destination} className="h-14 w-14 shrink-0 rounded-xl" />
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold">{t.title}</p>
        <p className="text-xs text-slate-500">{t.destination.name} · {t.start_date ? formatDate(t.start_date) : 'No date'} · {t.duration_days}d</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold">{inr(t.budget?.average)}</p>
        {t.is_completed ? <Badge tone="violet">Travelled</Badge> : t.is_saved ? <Badge tone="brand">Saved</Badge> : <Badge>Draft</Badge>}
      </div>
    </Link>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const { data, error, loading, reload } = useApi(() => trips.dashboard(), [])
  const first = user.name.split(' ')[0]

  if (loading) return <main className="mx-auto max-w-6xl space-y-6 px-4 py-10"><Skeleton className="h-12 w-80" /><div className="grid gap-4 sm:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div><Skeleton className="h-64" /></main>
  if (error) return <main className="mx-auto max-w-3xl px-4 py-16"><ErrorState message={error} onRetry={reload} /></main>

  const { stats, upcoming, recent, favourite_destinations: favs, recent_recommendations: recs, travel_history: history } = data
  const next = upcoming[0]

  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <PageHeader eyebrow="Dashboard" title={`Namaste, ${first}`} subtitle="Your trips, plans and travel history at a glance."
        action={<Link to="/plan-trip"><Button><Plus size={16} />Plan a new trip</Button></Link>} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat icon={CalendarClock} label="Upcoming trip" value={next ? next.destination.name : '—'} hint={next ? formatDate(next.start_date) : 'Nothing scheduled'} />
        <Stat icon={Bookmark} label="Saved plans" value={stats.saved_trips} hint={`${stats.total_trips} trip${stats.total_trips === 1 ? '' : 's'} planned in total`} tone="sky" />
        <Stat icon={Heart} label="Favourite destination" value={favs[0]?.name || '—'} hint={favs[0] ? `${favs[0].count} plan${favs[0].count > 1 ? 's' : ''} or reviews` : 'Plan or review to see favourites'} tone="saffron" />
        <Stat icon={Wallet} label="Average budget" value={inr(stats.average_budget)} hint={stats.saved_trips ? 'Across your saved plans' : 'Across all your plans'} tone="violet" />
      </div>

      {stats.total_trips === 0 ? (
        <div className="mt-8">
          <EmptyState icon={Sparkles} title="Plan your first trip" action={<Link to="/plan-trip"><Button>Get AI recommendations</Button></Link>}>
            Answer a few questions and Margdarshak builds a full plan: destination, hotel, weather, route, itinerary and budget.
          </EmptyState>
        </div>
      ) : (
        <div className="mt-8 grid *:min-w-0 gap-6 lg:grid-cols-[1fr_340px]">
          <div className="space-y-6">
            {next && (
              <Link to={`/trip/${next.id}`} className="block overflow-hidden rounded-2xl shadow-card transition hover:shadow-lift">
                <DestinationCover destination={next.destination} className="h-44">
                  <div className="absolute bottom-4 left-5 text-white">
                    <p className="text-sm text-white/80">Next up · {formatDate(next.start_date, { weekday: 'long', day: 'numeric', month: 'long' })}</p>
                    <p className="text-2xl font-bold">{next.title}</p>
                  </div>
                  <span className="absolute bottom-4 right-5 flex items-center gap-1 rounded-full bg-white/90 px-3 py-1 text-sm font-semibold text-ink">Open <ArrowRight size={14} /></span>
                </DestinationCover>
              </Link>
            )}
            <Card title="Recent trips" action={<Link to="/saved-trips" className="text-sm font-medium text-brand-700">All trips →</Link>}>
              <div className="divide-y divide-slate-100">{recent.map((t) => <TripRow key={t.id} t={t} />)}</div>
            </Card>
            {recs.length > 0 && (
              <Card title="Recent recommendations" subtitle="From your latest plan">
                <div className="grid gap-3 sm:grid-cols-3">
                  {recs.map((r) => (
                    <Link key={r.destination_id} to={`/destination/${r.destination_id}`} className="rounded-xl border border-slate-200 p-3 transition hover:border-brand-300">
                      <p className="text-xs text-slate-500">{categoryMeta(r.category).label}</p>
                      <p className="font-semibold">{r.destination}</p>
                      <p className="mt-1 text-sm text-brand-700">{Math.round(r.score)}/100 match</p>
                    </Link>
                  ))}
                </div>
              </Card>
            )}
          </div>
          <aside className="space-y-6">
            {next && <WeatherCard destinationId={next.destination.id} />}
            <Card title="Favourite destinations">
              {favs.length === 0 ? <p className="text-sm text-slate-500">None yet.</p> : (
                <ul className="space-y-2">{favs.map((f) => <li key={f.id}><Link to={`/destination/${f.id}`} className="flex justify-between rounded-lg p-1.5 text-sm hover:bg-slate-50"><span>{f.name}<span className="text-slate-400"> · {f.state}</span></span><Heart size={14} className="text-rose-400" /></Link></li>)}</ul>
              )}
            </Card>
            <Card title="Travel history" action={<History size={18} className="text-slate-400" />}>
              {history.length === 0 ? <p className="text-sm text-slate-500">Mark a trip as travelled to build your history.</p> : (
                <ol className="space-y-2 text-sm">{history.map((h) => <li key={`${h.trip_id}-${h.visited_on}`} className="flex justify-between"><Link to={`/destination/${h.destination_id}`} className="font-medium hover:text-brand-700">{h.destination}</Link><span className="text-slate-500">{formatDate(h.visited_on)}</span></li>)}</ol>
              )}
            </Card>
          </aside>
        </div>
      )}
    </main>
  )
}
