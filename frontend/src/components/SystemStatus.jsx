import { useEffect, useState } from 'react'
import { getHealth } from '../services/api'

const Dot = ({ ok }) => (
  <span className={`inline-block h-2.5 w-2.5 rounded-full ${ok === null ? 'bg-slate-300 animate-pulse' : ok ? 'bg-emerald-500' : 'bg-rose-500'}`} />
)

export default function SystemStatus() {
  const [state, setState] = useState({ backend: null, database: null, error: null })

  const check = () => {
    setState({ backend: null, database: null, error: null })
    getHealth()
      .then((h) => setState({ backend: true, database: h.database === 'ok', error: null }))
      .catch((e) => {
        const body = e.response?.data
        // 503 = backend up, database down
        setState({
          backend: !!e.response,
          database: false,
          error: body ? 'Database unreachable' : 'Backend unreachable',
        })
      })
  }

  useEffect(check, [])

  const rows = [
    ['Frontend', true],
    ['Backend API', state.backend],
    ['PostgreSQL', state.database],
  ]

  return (
    <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">System status</h2>
        <button onClick={check} className="text-xs font-medium text-brand-600 hover:text-brand-700">
          Retry
        </button>
      </div>
      <ul className="space-y-2">
        {rows.map(([label, ok]) => (
          <li key={label} className="flex items-center justify-between text-sm">
            <span className="text-slate-600">{label}</span>
            <Dot ok={ok} />
          </li>
        ))}
      </ul>
      {state.error && <p className="mt-3 text-xs text-rose-600">{state.error}</p>}
    </div>
  )
}
