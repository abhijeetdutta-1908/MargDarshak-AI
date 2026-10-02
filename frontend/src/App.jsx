import { Compass } from 'lucide-react'
import { Suspense, lazy } from 'react'
import { Link, Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Spinner from './components/Spinner'
import AppLayout from './layouts/AppLayout'
import Landing from './pages/Landing'

// Route-level code splitting: each page loads on first visit.
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const PlanTrip = lazy(() => import('./pages/PlanTrip'))
const Recommendations = lazy(() => import('./pages/Recommendations'))
const Explore = lazy(() => import('./pages/Explore'))
const DestinationDetail = lazy(() => import('./pages/DestinationDetail'))
const HotelDetail = lazy(() => import('./pages/HotelDetail'))
const TripDetail = lazy(() => import('./pages/TripDetail'))
const Itinerary = lazy(() => import('./pages/Itinerary'))
const SavedTrips = lazy(() => import('./pages/SavedTrips'))
const SharedTrip = lazy(() => import('./pages/SharedTrip'))
const Profile = lazy(() => import('./pages/Profile'))
const Reviews = lazy(() => import('./pages/Reviews'))
const Admin = lazy(() => import('./pages/Admin'))

function NotFound() {
  return (
    <main className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-4 text-center">
      <Compass size={48} className="text-brand-600" />
      <h1 className="text-5xl font-bold">404</h1>
      <p className="text-slate-600">This page took a wrong turn.</p>
      <Link to="/" className="rounded-xl bg-brand-600 px-4 py-2 font-semibold text-white hover:bg-brand-700">Back home</Link>
    </main>
  )
}

const authed = (el, admin = false) => <ProtectedRoute admin={admin}>{el}</ProtectedRoute>

export default function App() {
  return (
    <Suspense fallback={<Spinner full />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<AppLayout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/landing" element={<Navigate to="/" replace />} />
          <Route path="/explore" element={<Explore />} />
          <Route path="/plan-trip" element={<PlanTrip />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/destination/:id" element={<DestinationDetail />} />
          <Route path="/hotel/:id" element={<HotelDetail />} />
          <Route path="/shared/:token" element={<SharedTrip />} />
          <Route path="/dashboard" element={authed(<Dashboard />)} />
          <Route path="/trip/:id" element={authed(<TripDetail />)} />
          <Route path="/itinerary/:id" element={authed(<Itinerary />)} />
          <Route path="/saved-trips" element={authed(<SavedTrips />)} />
          <Route path="/profile" element={authed(<Profile />)} />
          <Route path="/reviews" element={authed(<Reviews />)} />
          <Route path="/admin" element={authed(<Admin />, true)} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
