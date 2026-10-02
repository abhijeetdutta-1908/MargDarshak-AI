import L from 'leaflet'
import { useEffect, useRef, useState } from 'react'
import { useConfig } from '../context/ConfigContext'

/**
 * markers: [{ lat, lng, label, kind: 'destination'|'hotel'|'attraction'|'restaurant'|'stop', order?, color? }]
 * routes:  [{ points: [[lat, lng], ...], color, label }]
 * Uses Google Maps when a browser key is configured, otherwise OpenStreetMap via Leaflet.
 */
export default function MapView({ markers = [], routes = [], className = 'h-80', zoom = 12 }) {
  const { maps } = useConfig()
  return maps.provider === 'google' && maps.browser_key
    ? <GoogleMap apiKey={maps.browser_key} markers={markers} routes={routes} className={className} zoom={zoom} />
    : <LeafletMap markers={markers} routes={routes} className={className} zoom={zoom} />
}

const KIND_COLOR = { destination: '#0b1324', hotel: '#0284c7', attraction: '#05916d', restaurant: '#fb8f1f', stop: '#05916d', activity: '#7c3aed', shopping: '#db2777' }

function pinHtml(m) {
  const color = m.color || KIND_COLOR[m.kind] || '#05916d'
  const inner = m.order != null ? m.order : m.kind === 'hotel' ? 'H' : ''
  return `<div style="background:${color};width:26px;height:26px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,.3)"><span style="transform:rotate(45deg);color:white;font:700 11px Inter,sans-serif">${inner}</span></div>`
}

function LeafletMap({ markers, routes, className, zoom }) {
  const el = useRef(null)
  const map = useRef(null)
  const layer = useRef(null)

  useEffect(() => {
    map.current = L.map(el.current, { scrollWheelZoom: false, zoomControl: true })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map.current)
    layer.current = L.layerGroup().addTo(map.current)
    return () => map.current.remove()
  }, [])

  useEffect(() => {
    const g = layer.current
    g.clearLayers()
    const pts = []
    routes.forEach((r) => {
      if (r.points.length > 1) L.polyline(r.points, { color: r.color || '#05916d', weight: 4, opacity: 0.8, dashArray: '6 6' }).bindTooltip(r.label || '').addTo(g)
    })
    markers.forEach((m) => {
      const icon = L.divIcon({ html: pinHtml(m), className: '', iconSize: [26, 26], iconAnchor: [13, 26] })
      L.marker([m.lat, m.lng], { icon, title: m.label }).bindPopup(`<strong>${escapeHtml(m.label)}</strong>${m.sub ? `<br/><span style="color:#64748b">${escapeHtml(m.sub)}</span>` : ''}`).addTo(g)
      pts.push([m.lat, m.lng])
    })
    if (pts.length > 1) map.current.fitBounds(pts, { padding: [30, 30], maxZoom: 14 })
    else if (pts.length === 1) map.current.setView(pts[0], zoom)
  }, [markers, routes, zoom])

  return (
    <div className="relative">
      <div ref={el} className={`${className} w-full overflow-hidden rounded-2xl`} role="region" aria-label="Map" />
      {routes.length > 0 && <p className="mt-1 text-[11px] text-slate-500">Dashed lines connect stops in visiting order (not road paths).</p>}
    </div>
  )
}

const escapeHtml = (s = '') => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])

let googleLoader
function loadGoogle(key) {
  if (window.google?.maps) return Promise.resolve(window.google.maps)
  googleLoader ||= new Promise((resolve, reject) => {
    const s = document.createElement('script')
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&v=weekly`
    s.async = true
    s.onload = () => resolve(window.google.maps)
    s.onerror = () => reject(new Error('Google Maps failed to load'))
    document.head.appendChild(s)
  })
  return googleLoader
}

function GoogleMap({ apiKey, markers, routes, className, zoom }) {
  const el = useRef(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    let cancelled = false
    loadGoogle(apiKey).then((gm) => {
      if (cancelled) return
      const map = new gm.Map(el.current, { zoom, center: markers[0] ? { lat: markers[0].lat, lng: markers[0].lng } : { lat: 22.5, lng: 79 }, mapTypeControl: false, streetViewControl: false })
      const bounds = new gm.LatLngBounds()
      markers.forEach((m) => {
        const pos = { lat: m.lat, lng: m.lng }
        bounds.extend(pos)
        const marker = new gm.Marker({ position: pos, map, title: m.label, label: m.order != null ? String(m.order) : m.kind === 'hotel' ? 'H' : undefined })
        const info = new gm.InfoWindow({ content: `<strong>${escapeHtml(m.label)}</strong>${m.sub ? `<br/>${escapeHtml(m.sub)}` : ''}` })
        marker.addListener('click', () => info.open({ map, anchor: marker }))
      })
      routes.forEach((r) => new gm.Polyline({ path: r.points.map(([lat, lng]) => ({ lat, lng })), map, strokeColor: r.color || '#05916d', strokeWeight: 4, strokeOpacity: 0.8 }))
      if (markers.length > 1) map.fitBounds(bounds, 40)
    }).catch(() => setFailed(true))
    return () => { cancelled = true }
  }, [apiKey, markers, routes, zoom])
  if (failed) return <LeafletMap markers={markers} routes={routes} className={className} zoom={zoom} />
  return <div ref={el} className={`${className} w-full overflow-hidden rounded-2xl bg-slate-100`} role="region" aria-label="Map" />
}
