import { Copy, Eye, Luggage, MoreVertical, Pencil, Share2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import DestinationCover from '../components/DestinationCover'
import { Badge, Button, ConfirmDialog, EmptyState, ErrorState, Field, Modal, PageHeader, Skeleton, Tabs, inputClass } from '../components/ui'
import useApi from '../hooks/useApi'
import { errorMessage, trips } from '../services/api'
import { formatDate, inr } from '../utils/format'
import { copyShareLink } from './TripDetail'

function TripCard({ t, onRename, onDelete, onDuplicate, onShare }) {
  const [menu, setMenu] = useState(false)
  const act = (fn) => () => { setMenu(false); fn(t) }
  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-card">
      <Link to={`/trip/${t.id}`}>
        <DestinationCover destination={t.destination} className="h-32">
          <div className="absolute bottom-3 left-4 text-white"><p className="text-xs text-white/80">{t.destination.name}, {t.destination.state}</p></div>
          <div className="absolute right-3 top-3">{t.is_completed ? <Badge tone="violet">Travelled</Badge> : t.is_saved ? <Badge tone="brand">Saved</Badge> : <Badge>Draft</Badge>}</div>
        </DestinationCover>
      </Link>
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <Link to={`/trip/${t.id}`} className="font-semibold hover:text-brand-700">{t.title}</Link>
          <div className="relative">
            <button onClick={() => setMenu(!menu)} className="rounded-lg p-1 text-slate-500 hover:bg-slate-100" aria-label="Trip actions" aria-expanded={menu}><MoreVertical size={18} /></button>
            {menu && (
              <div className="absolute right-0 z-10 mt-1 w-44 rounded-xl border border-slate-200 bg-white p-1 shadow-lift" onMouseLeave={() => setMenu(false)}>
                {[[Eye, 'View', () => null, `/trip/${t.id}`], [Pencil, 'Rename', act(onRename)], [Copy, 'Duplicate', act(onDuplicate)], [Share2, 'Share link', act(onShare)]].map(([Icon, label, fn, to]) =>
                  to ? <Link key={label} to={to} className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-slate-50"><Icon size={15} />{label}</Link>
                    : <button key={label} onClick={fn} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-slate-50"><Icon size={15} />{label}</button>)}
                <button onClick={act(onDelete)} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-rose-600 hover:bg-rose-50"><Trash2 size={15} />Delete</button>
              </div>
            )}
          </div>
        </div>
        <p className="mt-1 text-sm text-slate-500">{t.start_date ? formatDate(t.start_date) : 'No date set'} · {t.duration_days} days · {t.travelers} traveller{t.travelers > 1 ? 's' : ''}</p>
        <p className="mt-2 text-sm"><span className="font-semibold">{inr(t.budget?.average)}</span> <span className="text-slate-500">estimated</span></p>
      </div>
    </article>
  )
}

export default function SavedTrips() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState('saved')
  const [page, setPage] = useState(1)
  const { data, error, loading, reload, setData } = useApi(() => trips.list({ saved: filter === 'saved' ? true : filter === 'drafts' ? false : undefined, page, page_size: 12 }), [filter, page])
  const [renaming, setRenaming] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)

  const patch = (t) => setData((d) => ({ ...d, items: d.items.map((x) => (x.id === t.id ? { ...x, ...t } : x)) }))
  const rename = async (e) => {
    e.preventDefault()
    setBusy(true)
    try { patch(await trips.update(renaming.id, { title: renaming.title.trim() })); toast.success('Trip renamed'); setRenaming(null) } catch (err) { toast.error(errorMessage(err)) } finally { setBusy(false) }
  }
  const remove = async () => {
    setBusy(true)
    try { await trips.remove(deleting.id); toast.success('Trip deleted'); setDeleting(null); reload() } catch (err) { toast.error(errorMessage(err)) } finally { setBusy(false) }
  }
  const duplicate = async (t) => {
    try { const c = await trips.duplicate(t.id); toast.success('Trip duplicated'); navigate(`/trip/${c.id}`) } catch (err) { toast.error(errorMessage(err)) }
  }
  const pages = data ? Math.ceil(data.total / data.page_size) : 1

  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <PageHeader eyebrow="My trips" title="Saved trips" subtitle="Plans you've generated. Save the ones you like; drafts stay here until you delete them."
        action={<Link to="/plan-trip"><Button>Plan a new trip</Button></Link>} />
      <div className="mb-6"><Tabs tabs={[['saved', 'Saved'], ['drafts', 'Drafts'], ['all', 'All']]} value={filter} onChange={(f) => { setFilter(f); setPage(1) }} /></div>
      {loading ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-64" />)}</div>
      ) : error ? <ErrorState message={error} onRetry={reload} /> : data.items.length === 0 ? (
        <EmptyState icon={Luggage} title={filter === 'saved' ? 'No saved trips yet' : 'Nothing here'} action={<Link to="/plan-trip"><Button>Plan a trip</Button></Link>}>
          {filter === 'saved' ? 'Open a generated plan and press “Save trip” to keep it here.' : 'Generate a trip to see it here.'}
        </EmptyState>
      ) : (
        <>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((t) => <TripCard key={t.id} t={t} onRename={(x) => setRenaming({ id: x.id, title: x.title })} onDelete={setDeleting} onDuplicate={duplicate} onShare={(x) => copyShareLink(x, patch)} />)}
          </div>
          {pages > 1 && (
            <nav className="mt-8 flex items-center justify-center gap-2" aria-label="Pagination">
              <Button size="sm" variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
              <span className="text-sm text-slate-600">Page {page} of {pages}</span>
              <Button size="sm" variant="secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</Button>
            </nav>
          )}
        </>
      )}
      <Modal open={!!renaming} onClose={() => setRenaming(null)} title="Rename trip">
        {renaming && (
          <form onSubmit={rename} className="space-y-4">
            <Field label="Trip name"><input className={inputClass} required maxLength={160} value={renaming.title} onChange={(e) => setRenaming({ ...renaming, title: e.target.value })} /></Field>
            <div className="flex justify-end gap-2"><Button type="button" variant="secondary" onClick={() => setRenaming(null)}>Cancel</Button><Button type="submit" loading={busy}>Save</Button></div>
          </form>
        )}
      </Modal>
      <ConfirmDialog open={!!deleting} title="Delete this trip?" danger loading={busy} confirmLabel="Delete" onConfirm={remove} onClose={() => setDeleting(null)}
        message={`“${deleting?.title}” and its itinerary will be permanently deleted.`} />
    </main>
  )
}
