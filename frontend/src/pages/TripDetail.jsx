import { Bookmark, BookmarkCheck, CheckCircle2, Copy, Link2, Pencil, RefreshCw, Share2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'
import TripView from '../components/TripView'
import { Button, ConfirmDialog, ErrorState, Field, Modal, Skeleton, inputClass } from '../components/ui'
import useApi from '../hooks/useApi'
import { errorMessage, trips } from '../services/api'

export function shareUrl(token) {
  return `${window.location.origin}/shared/${token}`
}

export async function copyShareLink(trip, onUpdate) {
  try {
    const { share_token } = await trips.share(trip.id)
    onUpdate?.({ ...trip, share_token })
    const url = shareUrl(share_token)
    if (navigator.share) await navigator.share({ title: trip.title, url }).catch(() => navigator.clipboard?.writeText(url))
    else await navigator.clipboard?.writeText(url)
    toast.success('Share link copied', { description: url })
  } catch (e) {
    toast.error(errorMessage(e))
  }
}

export default function TripDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: trip, error, loading, reload, setData } = useApi(() => trips.get(id), [id])
  const [busy, setBusy] = useState(null)
  const [renaming, setRenaming] = useState(false)
  const [title, setTitle] = useState('')
  const [confirm, setConfirm] = useState(null)

  const run = async (key, fn, success) => {
    setBusy(key)
    try {
      const result = await fn()
      if (success) toast.success(success)
      return result
    } catch (e) {
      toast.error(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <main className="mx-auto max-w-6xl px-4 py-10"><Skeleton className="h-64" /><Skeleton className="mt-6 h-96" /></main>
  if (error) return <main className="mx-auto max-w-3xl px-4 py-16"><ErrorState message={error} onRetry={reload} /></main>

  const toggleSave = () => run('save', async () => setData(await trips.update(trip.id, { is_saved: !trip.is_saved })),
    trip.is_saved ? 'Removed from saved trips' : 'Trip saved')
  const regenerate = () => run('regen', async () => { setData(await trips.regenerate(trip.id)); setConfirm(null) }, 'New itinerary generated')
  const duplicate = () => run('dup', async () => { const c = await trips.duplicate(trip.id); navigate(`/trip/${c.id}`) }, 'Trip duplicated')
  const complete = () => run('done', async () => { setData(await trips.complete(trip.id)); setConfirm(null) }, 'Added to your travel history')
  const remove = () => run('del', async () => { await trips.remove(trip.id); navigate('/saved-trips') }, 'Trip deleted')
  const rename = (e) => {
    e.preventDefault()
    if (!title.trim()) return
    run('rename', async () => { setData(await trips.update(trip.id, { title: title.trim() })); setRenaming(false) }, 'Trip renamed')
  }

  const actions = (
    <>
      <Button size="sm" variant={trip.is_saved ? 'secondary' : 'primary'} loading={busy === 'save'} onClick={toggleSave}>
        {trip.is_saved ? <><BookmarkCheck size={15} />Saved</> : <><Bookmark size={15} />Save trip</>}
      </Button>
      <Button size="sm" variant="secondary" loading={busy === 'regen'} onClick={() => setConfirm('regen')}><RefreshCw size={15} />Regenerate itinerary</Button>
      <Button size="sm" variant="secondary" onClick={() => copyShareLink(trip, setData)}><Share2 size={15} />Share</Button>
      {trip.share_token && <Button size="sm" variant="ghost" onClick={() => run('unshare', async () => { await trips.unshare(trip.id); setData({ ...trip, share_token: null }) }, 'Share link revoked')}><Link2 size={15} />Revoke link</Button>}
      <Button size="sm" variant="ghost" onClick={() => { setTitle(trip.title); setRenaming(true) }}><Pencil size={15} />Rename</Button>
      <Button size="sm" variant="ghost" loading={busy === 'dup'} onClick={duplicate}><Copy size={15} />Duplicate</Button>
      {!trip.is_completed && <Button size="sm" variant="ghost" onClick={() => setConfirm('done')}><CheckCircle2 size={15} />Mark as travelled</Button>}
      <Button size="sm" variant="ghost" className="text-rose-600 hover:bg-rose-50 sm:ml-auto" onClick={() => setConfirm('del')}><Trash2 size={15} />Delete</Button>
    </>
  )

  return (
    <>
      <TripView trip={trip} actions={actions} />
      <Modal open={renaming} onClose={() => setRenaming(false)} title="Rename trip">
        <form onSubmit={rename} className="space-y-4">
          <Field label="Trip name"><input className={inputClass} value={title} maxLength={160} onChange={(e) => setTitle(e.target.value)} required /></Field>
          <div className="flex justify-end gap-2"><Button type="button" variant="secondary" onClick={() => setRenaming(false)}>Cancel</Button><Button type="submit" loading={busy === 'rename'}>Save</Button></div>
        </form>
      </Modal>
      <ConfirmDialog open={confirm === 'regen'} title="Regenerate itinerary?" loading={busy === 'regen'} confirmLabel="Regenerate" onConfirm={regenerate} onClose={() => setConfirm(null)}
        message="We'll rebuild the day plan with fresh weather and alternative picks. Your destination and hotel stay the same. The current itinerary will be replaced." />
      <ConfirmDialog open={confirm === 'done'} title="Mark this trip as travelled?" loading={busy === 'done'} confirmLabel="Mark as travelled" onConfirm={complete} onClose={() => setConfirm(null)}
        message="It will be added to your travel history on the dashboard." />
      <ConfirmDialog open={confirm === 'del'} title="Delete this trip?" danger loading={busy === 'del'} confirmLabel="Delete trip" onConfirm={remove} onClose={() => setConfirm(null)}
        message="The trip and its itinerary will be permanently deleted, and any share link will stop working." />
    </>
  )
}
