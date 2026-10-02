import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import GenerationProgress from '../components/GenerationProgress'
import { useAuth } from '../context/AuthContext'
import { errorMessage, trips } from '../services/api'

/** generate(request) -> runs POST /trips/generate with the progress overlay, then opens the trip. */
export default function useGenerateTrip() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [state, setState] = useState({ busy: false, done: false })

  const generate = async (request) => {
    if (!user) {
      toast.info('Sign in to build and save a full trip plan')
      navigate('/login', { state: { from: location.pathname } })
      return
    }
    setState({ busy: true, done: false })
    try {
      const trip = await trips.generate(request)
      setState({ busy: true, done: true })
      setTimeout(() => navigate(`/trip/${trip.id}`), 700)
    } catch (e) {
      toast.error(errorMessage(e))
      setState({ busy: false, done: false })
    }
  }

  const overlay = state.busy ? <GenerationProgress done={state.done} /> : null
  return { generate, overlay, busy: state.busy }
}
