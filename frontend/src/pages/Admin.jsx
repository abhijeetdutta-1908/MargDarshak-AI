import { Building, EyeOff, Eye, Hotel, MapPinned, MessageSquareText, Pencil, Plus, Shield, Trash2, Users } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { Badge, Button, Card, ConfirmDialog, EmptyState, ErrorState, Field, Modal, PageHeader, Skeleton, Stars, Stat, Tabs, inputClass } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import useApi from '../hooks/useApi'
import { admin, destinations, errorMessage } from '../services/api'
import { CATEGORY, formatDate, inr, seasonLabel, titleCase } from '../utils/format'
import { HOTEL_TIERS } from '../utils/options'

const csv = (v) => (Array.isArray(v) ? v.join(', ') : v)
const list = (s) => String(s).split(',').map((x) => x.trim()).filter(Boolean)

const EMPTY_DEST = { name: '', state: '', country: 'India', description: '', latitude: '', longitude: '', category: 'nature', tags: '', best_seasons: '10, 11, 12, 1, 2',
  ideal_min_days: 2, ideal_max_days: 4, average_daily_cost: 3000, average_hotel_cost: 2500, average_food_cost: 600, average_transport_cost: 500, popularity_score: 0.5, image_url: '' }

function DestinationForm({ initial, onSaved, onClose }) {
  const [f, setF] = useState(initial ? { ...initial, tags: csv(initial.tags), best_seasons: csv(initial.best_seasons), image_url: initial.image_url || '' } : EMPTY_DEST)
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const num = ['latitude', 'longitude', 'ideal_min_days', 'ideal_max_days', 'average_daily_cost', 'average_hotel_cost', 'average_food_cost', 'average_transport_cost', 'popularity_score']
  const submit = async (e) => {
    e.preventDefault()
    const body = { ...f, tags: list(f.tags), best_seasons: list(f.best_seasons).map(Number), image_url: f.image_url || null }
    num.forEach((k) => { body[k] = Number(f[k]) })
    delete body.id
    setBusy(true)
    try {
      const saved = initial ? await admin.updateDestination(initial.id, body) : await admin.createDestination(body)
      toast.success(initial ? 'Destination updated' : 'Destination added')
      onSaved(saved)
    } catch (err) { toast.error(errorMessage(err)) } finally { setBusy(false) }
  }
  const input = (k, label, props = {}) => <Field label={label}><input className={inputClass} value={f[k]} onChange={set(k)} required {...props} /></Field>
  return (
    <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
      {input('name', 'Name')}{input('state', 'State')}
      <Field label="Category"><select className={inputClass} value={f.category} onChange={set('category')}>{Object.entries(CATEGORY).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</select></Field>
      {input('popularity_score', 'Popularity (0–1)', { type: 'number', step: 0.01, min: 0, max: 1 })}
      <Field label="Description" className="sm:col-span-2"><textarea className={`${inputClass} min-h-24`} value={f.description} onChange={set('description')} required minLength={20} /></Field>
      {input('latitude', 'Latitude', { type: 'number', step: 'any' })}{input('longitude', 'Longitude', { type: 'number', step: 'any' })}
      {input('tags', 'Tags (comma-separated)')}{input('best_seasons', 'Best months (1–12, comma-separated)')}
      {input('ideal_min_days', 'Ideal min days', { type: 'number', min: 1, max: 30 })}{input('ideal_max_days', 'Ideal max days', { type: 'number', min: 1, max: 30 })}
      {input('average_daily_cost', 'Avg daily cost / person (₹)', { type: 'number', min: 0 })}{input('average_hotel_cost', 'Avg standard room / night (₹)', { type: 'number', min: 0 })}
      {input('average_food_cost', 'Avg food / person / day (₹)', { type: 'number', min: 0 })}{input('average_transport_cost', 'Avg local transport / person / day (₹)', { type: 'number', min: 0 })}
      <Field label="Image URL (optional)" className="sm:col-span-2"><input type="url" className={inputClass} value={f.image_url} onChange={set('image_url')} /></Field>
      <div className="flex justify-end gap-2 sm:col-span-2"><Button type="button" variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" loading={busy}>Save destination</Button></div>
    </form>
  )
}

function DestinationsTab() {
  const { data, error, loading, reload } = useApi(() => destinations.list({ page_size: 50 }), [])
  const [editing, setEditing] = useState(null) // null | 'new' | destination
  const [deleting, setDeleting] = useState(null)
  const remove = async () => {
    try { await admin.deleteDestination(deleting.id); toast.success('Destination deleted'); setDeleting(null); reload() } catch (e) { toast.error(errorMessage(e)); setDeleting(null) }
  }
  if (loading) return <Skeleton className="h-64" />
  if (error) return <ErrorState message={error} onRetry={reload} />
  return (
    <Card title={`Destinations (${data.total})`} action={<Button size="sm" onClick={() => setEditing('new')}><Plus size={15} />Add destination</Button>}>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead className="text-left text-xs uppercase text-slate-500"><tr><th className="py-2">Name</th><th>Category</th><th>Best season</th><th>Daily cost</th><th>Popularity</th><th /></tr></thead>
          <tbody className="divide-y divide-slate-100">
            {data.items.map((d) => (
              <tr key={d.id}>
                <td className="py-2.5"><p className="font-medium">{d.name}</p><p className="text-xs text-slate-500">{d.state}</p></td>
                <td>{CATEGORY[d.category]?.label}</td><td>{seasonLabel(d.best_seasons)}</td><td>{inr(d.average_daily_cost)}</td><td>{d.popularity_score}</td>
                <td className="text-right whitespace-nowrap">
                  <button onClick={() => setEditing(d)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100" aria-label={`Edit ${d.name}`}><Pencil size={15} /></button>
                  <button onClick={() => setDeleting(d)} className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-50 hover:text-rose-600" aria-label={`Delete ${d.name}`}><Trash2 size={15} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Modal wide open={!!editing} onClose={() => setEditing(null)} title={editing === 'new' ? 'Add destination' : `Edit ${editing?.name}`}>
        {editing && <DestinationForm initial={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); reload() }} />}
      </Modal>
      <ConfirmDialog open={!!deleting} danger title={`Delete ${deleting?.name}?`} confirmLabel="Delete" onConfirm={remove} onClose={() => setDeleting(null)}
        message="This removes the destination with its hotels, places and reviews. Destinations that users have trips to can't be deleted." />
    </Card>
  )
}

const EMPTY_HOTEL = { name: '', tier: 'standard', rating: 4.0, price_per_night: 2500, address: '', amenities: 'Free Wi-Fi, Air conditioning', latitude: '', longitude: '', image_url: '' }

function HotelsTab() {
  const dests = useApi(() => destinations.list({ page_size: 50 }), [])
  const [destId, setDestId] = useState('')
  const hotels = useApi(() => (destId ? admin.hotels(destId) : Promise.resolve([])), [destId])
  const [form, setForm] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)
  const save = async (e) => {
    e.preventDefault()
    const body = { ...form, destination_id: Number(destId), rating: Number(form.rating), price_per_night: Number(form.price_per_night),
      latitude: Number(form.latitude), longitude: Number(form.longitude), amenities: list(form.amenities), image_url: form.image_url || null }
    delete body.id
    setBusy(true)
    try { form.id ? await admin.updateHotel(form.id, body) : await admin.createHotel(body); toast.success('Hotel saved'); setForm(null); hotels.reload() } catch (err) { toast.error(errorMessage(err)) } finally { setBusy(false) }
  }
  const remove = async () => {
    try { await admin.deleteHotel(deleting.id); toast.success('Hotel deleted'); setDeleting(null); hotels.reload() } catch (e) { toast.error(errorMessage(e)) }
  }
  const dest = dests.data?.items.find((d) => String(d.id) === destId)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  return (
    <Card title="Hotels" action={destId && <Button size="sm" onClick={() => setForm({ ...EMPTY_HOTEL, latitude: dest.latitude, longitude: dest.longitude })}><Plus size={15} />Add hotel</Button>}>
      <select className={`${inputClass} mb-4 max-w-sm`} value={destId} onChange={(e) => setDestId(e.target.value)} aria-label="Destination">
        <option value="">Choose a destination…</option>
        {dests.data?.items.slice().sort((a, b) => a.name.localeCompare(b.name)).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
      </select>
      {!destId ? <EmptyState icon={Hotel} title="Pick a destination to manage its hotels" /> : hotels.loading ? <Skeleton className="h-40" /> : hotels.error ? <ErrorState message={hotels.error} onRetry={hotels.reload} /> : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead className="text-left text-xs uppercase text-slate-500"><tr><th className="py-2">Hotel</th><th>Tier</th><th>Rating</th><th>Per night</th><th /></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {hotels.data.map((h) => (
                <tr key={h.id}>
                  <td className="py-2.5"><p className="font-medium">{h.name}</p><p className="text-xs text-slate-500">{h.address}</p></td>
                  <td>{titleCase(h.tier)}</td><td>{h.rating}</td><td>{inr(h.price_per_night)}</td>
                  <td className="whitespace-nowrap text-right">
                    <button onClick={() => setForm({ ...h, amenities: csv(h.amenities), image_url: h.image_url || '' })} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100" aria-label={`Edit ${h.name}`}><Pencil size={15} /></button>
                    <button onClick={() => setDeleting(h)} className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-50 hover:text-rose-600" aria-label={`Delete ${h.name}`}><Trash2 size={15} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Modal wide open={!!form} onClose={() => setForm(null)} title={form?.id ? `Edit ${form.name}` : `Add hotel in ${dest?.name}`}>
        {form && (
          <form onSubmit={save} className="grid gap-3 sm:grid-cols-2">
            <Field label="Name"><input className={inputClass} value={form.name} onChange={set('name')} required /></Field>
            <Field label="Tier"><select className={inputClass} value={form.tier} onChange={set('tier')}>{HOTEL_TIERS.map((t) => <option key={t} value={t}>{titleCase(t)}</option>)}</select></Field>
            <Field label="Rating (1–5)"><input type="number" step={0.1} min={1} max={5} className={inputClass} value={form.rating} onChange={set('rating')} required /></Field>
            <Field label="Price per night (₹)"><input type="number" min={0} className={inputClass} value={form.price_per_night} onChange={set('price_per_night')} required /></Field>
            <Field label="Address" className="sm:col-span-2"><input className={inputClass} value={form.address} onChange={set('address')} required /></Field>
            <Field label="Latitude"><input type="number" step="any" className={inputClass} value={form.latitude} onChange={set('latitude')} required /></Field>
            <Field label="Longitude"><input type="number" step="any" className={inputClass} value={form.longitude} onChange={set('longitude')} required /></Field>
            <Field label="Amenities (comma-separated)" className="sm:col-span-2"><input className={inputClass} value={form.amenities} onChange={set('amenities')} /></Field>
            <div className="flex justify-end gap-2 sm:col-span-2"><Button type="button" variant="secondary" onClick={() => setForm(null)}>Cancel</Button><Button type="submit" loading={busy}>Save hotel</Button></div>
          </form>
        )}
      </Modal>
      <ConfirmDialog open={!!deleting} danger title={`Delete ${deleting?.name}?`} confirmLabel="Delete" onConfirm={remove} onClose={() => setDeleting(null)} message="Trips that use this hotel keep their plan but lose the hotel link." />
    </Card>
  )
}

function UsersTab() {
  const { user: me } = useAuth()
  const [q, setQ] = useState('')
  const [query, setQuery] = useState('')
  const { data, error, loading, reload } = useApi(() => admin.users({ q: query || undefined, page_size: 50 }), [query])
  const toggle = async (u) => {
    try { await admin.setAdmin(u.id, !u.is_admin); toast.success(u.is_admin ? 'Admin access removed' : 'Admin access granted'); reload() } catch (e) { toast.error(errorMessage(e)) }
  }
  return (
    <Card title={`Users${data ? ` (${data.total})` : ''}`}>
      <form onSubmit={(e) => { e.preventDefault(); setQuery(q.trim()) }} className="mb-4 flex max-w-sm gap-2">
        <input className={inputClass} placeholder="Search name or email" value={q} onChange={(e) => setQ(e.target.value)} />
        <Button type="submit" variant="secondary">Search</Button>
      </form>
      {loading ? <Skeleton className="h-40" /> : error ? <ErrorState message={error} onRetry={reload} /> : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead className="text-left text-xs uppercase text-slate-500"><tr><th className="py-2">User</th><th>Trips</th><th>Reviews</th><th>Role</th><th /></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((u) => (
                <tr key={u.id}>
                  <td className="py-2.5"><p className="font-medium">{u.name}</p><p className="text-xs text-slate-500">{u.email}</p></td>
                  <td>{u.trip_count}</td><td>{u.review_count}</td>
                  <td>{u.is_admin ? <Badge tone="violet"><Shield size={11} />Admin</Badge> : <Badge>User</Badge>}</td>
                  <td className="text-right">{u.id !== me.id && <Button size="sm" variant="ghost" onClick={() => toggle(u)}>{u.is_admin ? 'Remove admin' : 'Make admin'}</Button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

function ReviewsTab() {
  const [hidden, setHidden] = useState('all')
  const { data, error, loading, reload } = useApi(() => admin.reviews({ hidden: hidden === 'all' ? undefined : hidden === 'hidden', page_size: 50 }), [hidden])
  const [deleting, setDeleting] = useState(null)
  const moderate = async (r) => {
    try { await admin.moderate(r.id, !r.is_hidden); toast.success(r.is_hidden ? 'Review restored' : 'Review hidden'); reload() } catch (e) { toast.error(errorMessage(e)) }
  }
  const remove = async () => {
    try { await admin.deleteReview(deleting.id); toast.success('Review deleted'); setDeleting(null); reload() } catch (e) { toast.error(errorMessage(e)) }
  }
  return (
    <Card title="Review moderation" action={<Tabs tabs={[['all', 'All'], ['visible', 'Visible'], ['hidden', 'Hidden']]} value={hidden} onChange={setHidden} />}>
      {loading ? <Skeleton className="h-40" /> : error ? <ErrorState message={error} onRetry={reload} /> : data.items.length === 0 ? <EmptyState icon={MessageSquareText} title="No reviews" /> : (
        <ul className="divide-y divide-slate-100">
          {data.items.map((r) => (
            <li key={r.id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm"><span className="font-semibold">{r.user_name}</span> on <span className="font-semibold">{r.destination_name}</span> {r.is_hidden && <Badge tone="amber">Hidden</Badge>}</p>
                <div className="flex items-center gap-2 text-xs text-slate-500"><Stars value={r.rating} size={12} />{formatDate(r.created_at)}</div>
                {r.comment && <p className="mt-1 text-sm text-slate-700">{r.comment}</p>}
              </div>
              <div className="flex shrink-0 gap-1">
                <Button size="sm" variant="secondary" onClick={() => moderate(r)}>{r.is_hidden ? <><Eye size={14} />Restore</> : <><EyeOff size={14} />Hide</>}</Button>
                <Button size="sm" variant="ghost" className="text-rose-600" onClick={() => setDeleting(r)}><Trash2 size={14} /></Button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <ConfirmDialog open={!!deleting} danger title="Delete review?" confirmLabel="Delete" onConfirm={remove} onClose={() => setDeleting(null)} message="Deleting is permanent. Hiding is reversible." />
    </Card>
  )
}

export default function Admin() {
  const [tab, setTab] = useState('overview')
  const stats = useApi(() => admin.stats(), [tab])
  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <PageHeader eyebrow="Admin" title="Data management" subtitle="Manage the catalogue, users and community reviews. Changes to destinations and hotels apply to recommendations immediately." />
      <div className="mb-6"><Tabs tabs={[['overview', 'Overview'], ['destinations', 'Destinations'], ['hotels', 'Hotels'], ['users', 'Users'], ['reviews', 'Reviews']]} value={tab} onChange={setTab} /></div>
      {tab === 'overview' && (stats.loading ? <Skeleton className="h-32" /> : stats.error ? <ErrorState message={stats.error} onRetry={stats.reload} /> : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat icon={Users} label="Users" value={stats.data.users} />
          <Stat icon={MapPinned} label="Destinations" value={stats.data.destinations} hint={`${stats.data.places} places`} tone="sky" />
          <Stat icon={Building} label="Hotels" value={stats.data.hotels} hint={`${stats.data.trips} trips planned`} tone="saffron" />
          <Stat icon={MessageSquareText} label="Reviews" value={stats.data.reviews} hint={`${stats.data.hidden_reviews} hidden`} tone="violet" />
        </div>
      ))}
      {tab === 'destinations' && <DestinationsTab />}
      {tab === 'hotels' && <HotelsTab />}
      {tab === 'users' && <UsersTab />}
      {tab === 'reviews' && <ReviewsTab />}
    </main>
  )
}
