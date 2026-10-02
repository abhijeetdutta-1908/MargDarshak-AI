import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuth } from '../context/AuthContext'

const navClass = ({ isActive }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:text-slate-900'}`

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const signOut = async () => {
    await logout()
    toast.success('Signed out')
    navigate('/')
  }

  const links = user ? [['/profile', 'Profile']] : []

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="text-lg font-bold tracking-tight text-brand-700">Margdarshak</Link>
          <nav className="hidden items-center gap-1 sm:flex">
            {links.map(([to, label]) => <NavLink key={to} to={to} className={navClass}>{label}</NavLink>)}
            {user ? (
              <button onClick={signOut} className="ml-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:text-rose-600">Sign out</button>
            ) : (
              <>
                <NavLink to="/login" className={navClass}>Sign in</NavLink>
                <Link to="/register" className="ml-1 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">Get started</Link>
              </>
            )}
          </nav>
          <button className="rounded-lg p-2 text-slate-600 sm:hidden" aria-label="Toggle menu" aria-expanded={open} onClick={() => setOpen(!open)}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d={open ? 'M6 6l12 12M18 6L6 18' : 'M4 7h16M4 12h16M4 17h16'} /></svg>
          </button>
        </div>
        {open && (
          <nav className="flex flex-col gap-1 border-t border-slate-200 px-4 py-3 sm:hidden" onClick={() => setOpen(false)}>
            {links.map(([to, label]) => <NavLink key={to} to={to} className={navClass}>{label}</NavLink>)}
            {user ? (
              <button onClick={signOut} className="rounded-lg px-3 py-2 text-left text-sm font-medium text-rose-600">Sign out</button>
            ) : (
              <>
                <NavLink to="/login" className={navClass}>Sign in</NavLink>
                <NavLink to="/register" className={navClass}>Create account</NavLink>
              </>
            )}
          </nav>
        )}
      </header>
      <Outlet />
    </div>
  )
}
