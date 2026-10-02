import { Sparkles } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import TripView from '../components/TripView'
import { Button, ErrorState, Skeleton } from '../components/ui'
import useApi from '../hooks/useApi'
import { trips } from '../services/api'

export default function SharedTrip() {
  const { token } = useParams()
  const { data, error, loading, reload } = useApi(() => trips.shared(token), [token])
  if (loading) return <main className="mx-auto max-w-6xl px-4 py-10"><Skeleton className="h-96" /></main>
  if (error) return <main className="mx-auto max-w-3xl px-4 py-16"><ErrorState message={error} onRetry={reload} /></main>
  return (
    <TripView trip={data} readOnly actions={
      <div className="flex w-full items-center justify-between gap-3">
        <span className="text-sm text-slate-600">Shared from Margdarshak · read-only</span>
        <Link to="/plan-trip"><Button size="sm"><Sparkles size={15} />Plan your own trip</Button></Link>
      </div>
    } />
  )
}
