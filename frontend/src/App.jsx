import { Link, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import SystemStatus from './components/SystemStatus'
import AppLayout from './layouts/AppLayout'
import Login from './pages/Login'
import Profile from './pages/Profile'
import Register from './pages/Register'

function Home() {
  return (
    <main className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl flex-col items-center justify-center gap-10 px-4 py-16 text-center">
      <div>
        <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-brand-600">Margdarshak</p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">Plan Smarter. Travel Better.</h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          Margdarshak uses AI to create personalized travel plans based on your interests, budget, duration and
          preferences.
        </p>
      </div>
      <SystemStatus />
    </main>
  )
}

function NotFound() {
  return (
    <main className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center gap-4 px-4">
      <h1 className="text-5xl font-bold">404</h1>
      <p className="text-slate-600">This page took a wrong turn.</p>
      <Link to="/" className="rounded-lg bg-brand-600 px-4 py-2 text-white hover:bg-brand-700">
        Back home
      </Link>
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<AppLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
