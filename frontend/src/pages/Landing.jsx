import { ArrowRight, Brain, CalendarRange, CloudSun, Compass, MapPinned, Quote, Route, Sparkles, Wallet } from 'lucide-react'
import { Link } from 'react-router-dom'
import DestinationCard from '../components/DestinationCard'
import { Skeleton, Stars } from '../components/ui'
import useApi from '../hooks/useApi'
import { destinations, reviews } from '../services/api'

const STEPS = [
  [Compass, 'Tell us your style', 'Budget, days, interests, dates, hotel and transport preferences.'],
  [Brain, 'AI ranks destinations', 'Semantic matching plus nine weighted factors, each one explained.'],
  [CalendarRange, 'Get a day-wise plan', 'Hotels, attractions, meals and routes, scheduled around the weather.'],
  [Wallet, 'Know the cost', 'A transparent budget with minimum, average and maximum estimates.'],
]

const FEATURES = [
  [Sparkles, 'AI-powered recommendations', 'Sentence-Transformer embeddings and a FAISS vector index find destinations that match how you describe your trip, then a weighted score ranks them.'],
  [CalendarRange, 'Smart itinerary', 'Attractions chosen for your interests, grouped by area, with lunch near where you are and evening events in the evening.'],
  [Wallet, 'Budget planning', 'Accommodation, transport (including getting there), food, activities and contingencies, broken down so nothing surprises you.'],
  [CloudSun, 'Weather-aware planning', 'Rainy day in the forecast? Museums and indoor sights move to that day and treks move to sunny ones.'],
  [Route, 'Route optimisation', 'Each day’s stops are ordered with nearest-neighbour, 2-opt and Or-opt search to cut travel time.'],
  [MapPinned, 'Everything on a map', 'Your hotel, every stop and each day’s route, colour-coded, on an interactive map.'],
]

export default function Landing() {
  const popular = useApi(() => destinations.list({ page_size: 6 }), [])
  const testimonials = useApi(() => reviews.recent(3), [])

  return (
    <main>
      {/* Hero */}
      <section className="relative overflow-hidden bg-ink text-white">
        <div className="absolute inset-0 opacity-60" style={{ background: 'radial-gradient(ellipse at 15% 20%, #05916d 0, transparent 45%), radial-gradient(ellipse at 85% 30%, #7c3aed 0, transparent 40%), radial-gradient(ellipse at 60% 100%, #fb8f1f 0, transparent 45%)' }} />
        <div className="relative mx-auto grid *:min-w-0 max-w-6xl items-center gap-12 px-4 py-20 sm:py-28 lg:grid-cols-[1.2fr_1fr]">
          <div className="animate-fade-up">
            <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium ring-1 ring-white/20"><Sparkles size={13} />AI-based smart trip &amp; travel planner</span>
            <h1 className="mt-5 text-5xl font-extrabold leading-[1.05] sm:text-6xl lg:text-7xl">Plan Smarter.<br /><span className="bg-gradient-to-r from-brand-300 via-white to-saffron-400 bg-clip-text text-transparent">Travel Better.</span></h1>
            <p className="mt-6 max-w-xl text-lg text-white/75">Margdarshak uses AI to create personalized travel plans based on your interests, budget, duration and preferences.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/plan-trip" className="inline-flex items-center gap-2 rounded-xl bg-saffron-500 px-6 py-3.5 font-semibold text-white shadow-lg shadow-saffron-500/30 transition hover:bg-saffron-600">Plan My Trip<ArrowRight size={18} /></Link>
              <Link to="/explore" className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-6 py-3.5 font-semibold ring-1 ring-white/25 transition hover:bg-white/20">Explore Destinations</Link>
            </div>
            <p className="mt-6 text-sm text-white/50">36 Indian destinations · 290+ attractions & restaurants · Weather, maps and routes</p>
          </div>
          <div className="hidden lg:block">
            <div className="rotate-2 rounded-3xl bg-white/95 p-5 text-ink shadow-2xl">
              <div className="flex items-center justify-between"><p className="font-display font-bold">Manali — 4 days</p><span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700">92/100 match</span></div>
              <ul className="mt-3 space-y-1.5 text-sm">
                {['Strong match for your mountain preference', 'Suitable for trekking, nature, photography', 'Fits your budget', 'November is one of the best months'].map((r) => <li key={r} className="flex gap-2"><span className="text-brand-600">✓</span>{r}</li>)}
              </ul>
              <div className="mt-4 space-y-2 border-t border-slate-100 pt-4 text-xs">
                {[['09:00', 'Hadimba Devi Temple'], ['12:30', 'Lunch near Old Manali'], ['14:00', 'Jogini Waterfalls trek'], ['19:30', 'Dinner · Himachali dham']].map(([t, x]) => <p key={t} className="flex gap-3"><span className="font-mono text-slate-400">{t}</span>{x}</p>)}
              </div>
            </div>
            <p className="mt-3 text-center text-xs text-white/40">Example output</p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <p className="text-center text-sm font-semibold uppercase tracking-widest text-brand-600">How it works</p>
        <h2 className="mt-2 text-center text-3xl font-bold sm:text-4xl">From “where should we go?” to a full plan</h2>
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map(([Icon, title, text], i) => (
            <div key={title} className="relative rounded-2xl border border-slate-200/80 bg-white p-6 shadow-card">
              <span className="absolute right-5 top-4 font-display text-4xl font-extrabold text-slate-100">{i + 1}</span>
              <Icon className="text-brand-600" size={26} />
              <h3 className="mt-4 font-bold">{title}</h3>
              <p className="mt-1 text-sm text-slate-600">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-3xl font-bold sm:text-4xl">Everything a trip needs, in one place</h2>
          <p className="mt-2 max-w-2xl text-slate-600">No more juggling ten tabs for destinations, hotels, weather, routes and spreadsheets.</p>
          <div className="mt-10 grid gap-x-10 gap-y-8 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(([Icon, title, text]) => (
              <div key={title} className="flex gap-4">
                <div className="h-fit rounded-xl bg-brand-50 p-2.5 text-brand-700"><Icon size={22} /></div>
                <div><h3 className="font-bold">{title}</h3><p className="mt-1 text-sm leading-relaxed text-slate-600">{text}</p></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Popular destinations */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <div className="flex items-end justify-between gap-4">
          <div><h2 className="text-3xl font-bold sm:text-4xl">Popular destinations</h2><p className="mt-1 text-slate-600">Most-loved places in our catalogue.</p></div>
          <Link to="/explore" className="hidden items-center gap-1 font-semibold text-brand-700 sm:flex">View all<ArrowRight size={16} /></Link>
        </div>
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {popular.loading ? Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-72" />)
            : popular.error ? <p className="text-sm text-slate-500">Destinations will appear here once the server is reachable.</p>
              : popular.data.items.map((d) => <DestinationCard key={d.id} d={d} />)}
        </div>
      </section>

      {/* Testimonials: real reviews only */}
      {testimonials.data?.length > 0 && (
        <section className="bg-brand-900 py-20 text-white">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="text-3xl font-bold">What travellers say</h2>
            <div className="mt-8 grid gap-5 md:grid-cols-3">
              {testimonials.data.map((r) => (
                <figure key={r.id} className="rounded-2xl bg-white/10 p-6 ring-1 ring-white/15">
                  <Quote className="text-brand-300" size={22} />
                  <blockquote className="mt-3 text-white/90">{r.comment}</blockquote>
                  <figcaption className="mt-4 flex items-center justify-between text-sm"><span>{r.user_name} · <Link to={`/destination/${r.destination_id}`} className="underline">{r.destination_name}</Link></span><Stars value={r.rating} size={13} /></figcaption>
                </figure>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-600 to-brand-800 px-8 py-14 text-center text-white">
          <h2 className="text-3xl font-bold sm:text-4xl">Your next trip, planned in a minute</h2>
          <p className="mx-auto mt-3 max-w-xl text-white/80">Free to use. Your trips are saved to your account and can be shared with a link.</p>
          <Link to="/plan-trip" className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3.5 font-semibold text-brand-800 transition hover:bg-brand-50">Plan My Trip<ArrowRight size={18} /></Link>
        </div>
      </section>
    </main>
  )
}
