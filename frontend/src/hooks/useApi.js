import { useCallback, useEffect, useState } from 'react'
import { errorMessage } from '../services/api'

/** Load data on mount / when deps change. Returns { data, error, loading, reload, setData }. */
export default function useApi(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const load = useCallback(fn, deps)

  const reload = useCallback(() => {
    let alive = true
    setState((s) => ({ ...s, loading: true, error: null }))
    load()
      .then((data) => alive && setState({ data, error: null, loading: false }))
      .catch((e) => alive && setState({ data: null, error: errorMessage(e), loading: false }))
    return () => { alive = false }
  }, [load])

  useEffect(reload, [reload])

  const setData = useCallback((updater) => setState((s) => ({ ...s, data: typeof updater === 'function' ? updater(s.data) : updater })), [])
  return { ...state, reload, setData }
}
