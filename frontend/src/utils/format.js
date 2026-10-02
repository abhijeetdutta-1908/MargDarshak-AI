import {
  Building2, Church, Landmark, Mountain, PawPrint, Palmtree, Tent, Trees, Drama,
} from 'lucide-react'

export const inr = (v) => (v == null || Number.isNaN(Number(v)) ? '—' : `₹${Math.round(Number(v)).toLocaleString('en-IN')}`)

export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
export const MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

/** "Oct–Mar" style label for a list of month numbers (handles wrap-around). */
export function seasonLabel(months = []) {
  if (!months.length) return '—'
  if (months.length === 12) return 'Year-round'
  const set = new Set(months)
  const starts = months.filter((m) => !set.has(m === 1 ? 12 : m - 1))
  const ranges = starts.map((s) => {
    let e = s
    while (set.has(e === 12 ? 1 : e + 1) && (e === 12 ? 1 : e + 1) !== s) e = e === 12 ? 1 : e + 1
    return s === e ? MONTHS[s - 1] : `${MONTHS[s - 1]}–${MONTHS[e - 1]}`
  })
  return ranges.join(', ')
}

export const formatDate = (iso, opts = { day: 'numeric', month: 'short', year: 'numeric' }) =>
  iso ? new Date(iso + (iso.length === 10 ? 'T00:00:00' : '')).toLocaleDateString('en-IN', opts) : '—'

export const minutesLabel = (m) => {
  if (m == null) return '—'
  const h = Math.floor(m / 60)
  const r = Math.round(m % 60)
  return h ? `${h} h${r ? ` ${r} min` : ''}` : `${r} min`
}

export const titleCase = (s = '') => s.replace(/[-_]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

// Visual identity per destination category (used for cover art in place of stock photos).
export const CATEGORY = {
  beach: { icon: Palmtree, from: '#06b6d4', via: '#0ea5e9', to: '#f59e0b', label: 'Beach' },
  mountain: { icon: Mountain, from: '#334155', via: '#4f46e5', to: '#0ea5e9', label: 'Mountain' },
  historical: { icon: Landmark, from: '#b45309', via: '#d97706', to: '#f43f5e', label: 'Historical' },
  religious: { icon: Church, from: '#ea580c', via: '#f59e0b', to: '#fde047', label: 'Religious' },
  adventure: { icon: Tent, from: '#15803d', via: '#0d9488', to: '#38bdf8', label: 'Adventure' },
  wildlife: { icon: PawPrint, from: '#365314', via: '#4d7c0f', to: '#ca8a04', label: 'Wildlife' },
  city: { icon: Building2, from: '#1e293b', via: '#7c3aed', to: '#ec4899', label: 'City' },
  nature: { icon: Trees, from: '#047857', via: '#10b981', to: '#84cc16', label: 'Nature' },
  cultural: { icon: Drama, from: '#9d174d', via: '#c026d3', to: '#f97316', label: 'Cultural' },
}

export const categoryMeta = (c) => CATEGORY[c] || CATEGORY.nature

export const ITEM_STYLE = {
  arrival: { dot: 'bg-sky-500', label: 'Arrival' },
  'check-in': { dot: 'bg-sky-400', label: 'Check-in' },
  'check-out': { dot: 'bg-sky-400', label: 'Check-out' },
  departure: { dot: 'bg-sky-600', label: 'Departure' },
  meal: { dot: 'bg-saffron-500', label: 'Meal' },
  attraction: { dot: 'bg-brand-600', label: 'Sightseeing' },
  activity: { dot: 'bg-violet-500', label: 'Activity' },
  shopping: { dot: 'bg-pink-500', label: 'Shopping' },
  rest: { dot: 'bg-slate-300', label: 'Free time' },
  travel: { dot: 'bg-slate-400', label: 'Travel' },
}

export const DAY_COLORS = ['#05916d', '#7c3aed', '#ea580c', '#0284c7', '#db2777', '#65a30d', '#ca8a04', '#0891b2']
