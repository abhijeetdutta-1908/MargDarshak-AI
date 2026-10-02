import { Check, Loader2, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'

export const TRIP_STEPS = [
  'Analyzing your preferences...', 'Finding destinations...', 'Checking weather...', 'Finding places...',
  'Optimizing route...', 'Calculating budget...', 'Building your itinerary...',
]
export const RECOMMEND_STEPS = TRIP_STEPS.slice(0, 2).concat(['Scoring and explaining matches...'])

/**
 * Step-by-step progress while a request runs. The server does all steps in one call, so steps
 * advance on a timer and the list completes when the response arrives (done=true).
 */
export default function GenerationProgress({ steps = TRIP_STEPS, done = false, finalLabel = 'Your personalized trip is ready!' }) {
  const [active, setActive] = useState(0)
  useEffect(() => {
    if (done) return
    const t = setInterval(() => setActive((a) => Math.min(a + 1, steps.length - 1)), 650)
    return () => clearInterval(t)
  }, [done, steps.length])
  const current = done ? steps.length : active
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm" role="status" aria-live="polite">
      <div className="w-full max-w-sm animate-fade-up rounded-3xl bg-white p-7 shadow-lift">
        <div className="mb-5 flex items-center gap-3">
          <div className="rounded-2xl bg-brand-50 p-2.5 text-brand-600"><Sparkles size={22} /></div>
          <div>
            <p className="font-display text-lg font-bold">{done ? finalLabel : 'Planning with Margdarshak AI'}</p>
            <div className="mt-1 h-1.5 w-48 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-brand-500 transition-all duration-500" style={{ width: `${(current / steps.length) * 100}%` }} />
            </div>
          </div>
        </div>
        <ol className="space-y-2.5">
          {steps.map((s, i) => (
            <li key={s} className={`flex items-center gap-2.5 text-sm transition ${i <= current ? 'text-ink' : 'text-slate-400'}`}>
              {i < current ? <Check size={16} className="text-brand-600" /> : i === current && !done ? <Loader2 size={16} className="animate-spin text-brand-600" /> : <span className="h-4 w-4 rounded-full border-2 border-slate-200" />}
              {s}
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
