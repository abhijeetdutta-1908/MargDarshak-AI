import { Compass, LogOut, Menu, User, X } from 'lucide-react'
import { Suspense, useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import ErrorBoundary from '../components/ErrorBoundary'
import Spinner from '../components/Spinner'
import { useAuth } from '../context/AuthContext'

const navClass = ({ isActive }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:text-ink'}`

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white"><Compass size={18} /></span>
      <span className="font-display text-lg font-extrabold tracking-tight">Margdarshak</span>
    </Link>
  )
}

function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:grid-cols-[2fr_1fr_1fr]">
        <div>
          <Logo />
          <p className="mt-3 max-w-sm text-sm text-slate-500">AI-based smart trip &amp; travel planner. Recommendations, hotels, weather, routes, itineraries and budgets in one place.</p>
        </div>
        <div>
          <p className="text-sm font-semibold">Plan</p>
          <ul className="mt-2 space-y-1.5 text-sm text-slate-500">
            <li><Link to="/plan-trip" className="hover:text-ink">Plan a trip</Link></li>
            <li><Link to="/explore" className="hover:text-ink">Explore destinations</Link></li>
            <li><Link to="/saved-trips" className="hover:text-ink">Saved trips</Link></li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold">About the data</p>
          <p className="mt-2 text-sm text-slate-500">Costs are planning estimates. Hotels are sample listings. Weather and places are live only when API keys are configured, and fallbacks are labelled.</p>
        </div>
      </div>
      <p className="border-t border-slate-100 py-4 text-center text-xs text-slate-400">© {new Date().getFullYear()} Margdarshak · B.Tech major project</p>
    </footer>
  )
}

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  useEffect(() => { setOpen(false); window.scrollTo(0, 0) }, [pathname])

  const signOut = async () => {
    await logout()
    toast.success('Signed out')
    navigate('/')
  }

  const links = [['/explore', 'Explore'], ['/plan-trip', 'Plan trip']]
  if (user) links.unshift(['/dashboard', 'Dashboard'])
  if (user) links.push(['/saved-trips', 'My trips'], ['/reviews', 'Reviews'])
  if (user?.is_admin) links.push(['/admin', 'Admin'])

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2">Skip to content</a>
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Logo />
          <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
            {links.map(([to, label]) => <NavLink key={to} to={to} className={navClass}>{label}</NavLink>)}
          </nav>
          <div className="hidden items-center gap-2 md:flex">
            {user ? (
              <>
                <NavLink to="/profile" className={({ isActive }) => `flex items-center gap-2 rounded-full py-1 pl-1 pr-3 text-sm font-medium ${isActive ? 'bg-brand-50 text-brand-700' : 'hover:bg-slate-100'}`}>
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">{user.name[0].toUpperCase()}</span>{user.name.split(' ')[0]}
                </NavLink>
                <button onClick={signOut} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-rose-600" aria-label="Sign out" title="Sign out"><LogOut size={18} /></button>
              </>
            ) : (
              <>
                <NavLink to="/login" className={navClass}>Sign in</NavLink>
                <Link to="/register" className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">Get started</Link>
              </>
            )}
          </div>
          <button className="rounded-lg p-2 text-slate-600 md:hidden" aria-label="Toggle menu" aria-expanded={open} onClick={() => setOpen(!open)}>
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
        {open && (
          <nav className="flex flex-col gap-1 border-t border-slate-200 bg-white px-4 py-3 md:hidden" aria-label="Mobile">
            {links.map(([to, label]) => <NavLink key={to} to={to} className={navClass}>{label}</NavLink>)}
            {user ? (
              <>
                <NavLink to="/profile" className={navClass}><User size={15} className="mr-1 inline" />Profile</NavLink>
                <button onClick={signOut} className="rounded-lg px-3 py-2 text-left text-sm font-medium text-rose-600">Sign out</button>
              </>
            ) : (
              <>
                <NavLink to="/login" className={navClass}>Sign in</NavLink>
                <NavLink to="/register" className={navClass}>Create account</NavLink>
              </>
            )}
          </nav>
        )}
      </header>
      <div id="main" className="flex-1">
        <ErrorBoundary key={pathname}>
          <Suspense fallback={<Spinner full />}><Outlet /></Suspense>
        </ErrorBoundary>
      </div>
      <Footer />
    </div>
  )
}
