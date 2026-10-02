import { CloudRain, Droplets, Sun, Thermometer, Wind } from 'lucide-react'
import useApi from '../hooks/useApi'
import { destinations } from '../services/api'
import { formatDate } from '../utils/format'
import { Card, ErrorState, Skeleton, SourceBadge } from './ui'

const icon = (code) => `https://openweathermap.org/img/wn/${code}@2x.png`

export function WeatherView({ w }) {
  if (w.source !== 'live') {
    const s = w.seasonal
    return (
      <div className="space-y-3">
        <div className={`flex items-start gap-3 rounded-xl p-4 ${s.rain_likely ? 'bg-sky-50' : 'bg-brand-50'}`}>
          {s.rain_likely ? <CloudRain className="mt-0.5 text-sky-600" /> : <Sun className="mt-0.5 text-saffron-500" />}
          <div>
            <p className="font-semibold">{s.summary}</p>
            <p className="text-xs text-slate-600">{s.in_best_season ? 'This month is within the best season.' : 'This month is outside the best season.'}</p>
          </div>
        </div>
        <p className="text-xs text-slate-500">{w.note}</p>
      </div>
    )
  }
  const c = w.current
  return (
    <div>
      <div className="flex items-center gap-4">
        <img src={icon(c.icon)} alt={c.description} className="h-16 w-16 -my-2" />
        <div>
          <p className="font-display text-4xl font-bold">{Math.round(c.temperature)}°C</p>
          <p className="text-sm capitalize text-slate-600">{c.description}</p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-slate-600">
        <span className="flex items-center gap-1"><Thermometer size={14} />Feels {Math.round(c.feels_like)}°</span>
        <span className="flex items-center gap-1"><Droplets size={14} />{c.humidity}% humid</span>
        <span className="flex items-center gap-1"><Wind size={14} />{c.wind_speed ?? '—'} m/s</span>
      </div>
      {w.forecast?.length > 0 && (
        <div className="mt-5 grid grid-cols-5 gap-1.5">
          {w.forecast.slice(0, 5).map((f) => (
            <div key={f.date} className={`rounded-xl p-2 text-center ${f.rain_likely ? 'bg-sky-50' : 'bg-slate-50'}`}>
              <p className="text-[11px] font-medium text-slate-500">{formatDate(f.date, { weekday: 'short' })}</p>
              <img src={icon(f.icon)} alt={f.condition} className="mx-auto h-9 w-9" />
              <p className="text-xs font-semibold">{Math.round(f.temp_max)}°<span className="font-normal text-slate-400"> {Math.round(f.temp_min)}°</span></p>
              {f.rain_probability > 0 && <p className="text-[10px] text-sky-600">{Math.round(f.rain_probability * 100)}%</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function WeatherCard({ destinationId, initial }) {
  const { data, error, loading, reload } = useApi(
    () => (initial ? Promise.resolve(initial) : destinations.weather(destinationId)), [destinationId, initial])
  return (
    <Card title="Weather" action={data && <SourceBadge source={data.source} note={data.note} />}>
      {loading ? <Skeleton className="h-28" /> : error ? <ErrorState message={error} onRetry={reload} /> : <WeatherView w={data} />}
    </Card>
  )
}
