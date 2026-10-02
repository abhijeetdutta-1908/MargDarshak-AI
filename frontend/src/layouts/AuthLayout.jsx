import { Link } from 'react-router-dom'

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <aside className="relative hidden overflow-hidden bg-gradient-to-br from-brand-700 via-brand-600 to-emerald-400 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <Link to="/" className="text-lg font-bold tracking-tight">Margdarshak</Link>
        <div>
          <h2 className="text-4xl font-bold leading-tight">Plan Smarter.<br />Travel Better.</h2>
          <p className="mt-4 max-w-md text-white/80">
            Personalised destinations, hotels, weather-aware itineraries and budgets — planned together in one place.
          </p>
        </div>
        <p className="text-sm text-white/60">AI-Based Smart Trip &amp; Travel Planner</p>
        <div className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-white/10 blur-2xl" />
      </aside>
      <main className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm">
          <Link to="/" className="mb-8 block text-lg font-bold text-brand-700 lg:hidden">Margdarshak</Link>
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
          <div className="mt-8">{children}</div>
          {footer && <p className="mt-6 text-center text-sm text-slate-600">{footer}</p>}
        </div>
      </main>
    </div>
  )
}
