import { MessageSquareText, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { ReviewForm } from '../components/ReviewSection'
import { Card, ConfirmDialog, EmptyState, ErrorState, Field, PageHeader, Skeleton, Stars, inputClass } from '../components/ui'
import useApi from '../hooks/useApi'
import { destinations, errorMessage, reviews } from '../services/api'
import { formatDate } from '../utils/format'

export default function Reviews() {
  const mine = useApi(() => reviews.mine(), [])
  const all = useApi(() => destinations.list({ page_size: 50 }), [])
  const [destId, setDestId] = useState('')
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const reviewed = new Set(mine.data?.map((r) => r.destination_id))
  const choices = all.data?.items.filter((d) => !reviewed.has(d.id)).sort((a, b) => a.name.localeCompare(b.name)) || []

  const create = async (body) => {
    try { await reviews.create(Number(destId), body); toast.success('Review posted'); setDestId(''); mine.reload() } catch (e) { toast.error(errorMessage(e)) }
  }
  const update = async (body) => {
    try { await reviews.update(editing, body); toast.success('Review updated'); setEditing(null); mine.reload() } catch (e) { toast.error(errorMessage(e)) }
  }
  const remove = async () => {
    try { await reviews.remove(deleting.id); toast.success('Review deleted'); setDeleting(null); mine.reload() } catch (e) { toast.error(errorMessage(e)) }
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <PageHeader eyebrow="Reviews" title="Your reviews" subtitle="Help other travellers by sharing what you loved (or didn't)." />
      <Card title="Write a review" className="mb-6">
        <Field label="Destination" className="mb-4">
          <select className={inputClass} value={destId} onChange={(e) => setDestId(e.target.value)} disabled={all.loading}>
            <option value="">Choose a destination…</option>
            {choices.map((d) => <option key={d.id} value={d.id}>{d.name}, {d.state}</option>)}
          </select>
        </Field>
        {destId && <ReviewForm key={destId} onSubmit={create} />}
      </Card>
      {mine.loading ? <Skeleton className="h-40" /> : mine.error ? <ErrorState message={mine.error} onRetry={mine.reload} /> : mine.data.length === 0 ? (
        <EmptyState icon={MessageSquareText} title="You haven't reviewed anywhere yet">Pick a destination above to write your first review.</EmptyState>
      ) : (
        <div className="space-y-4">
          {mine.data.map((r) => (
            <Card key={r.id}>
              {editing === r.id ? <ReviewForm initial={r} submitLabel="Save changes" onSubmit={update} onCancel={() => setEditing(null)} /> : (
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <Link to={`/destination/${r.destination_id}`} className="font-semibold hover:text-brand-700">{r.destination_name}</Link>
                    <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500"><Stars value={r.rating} size={13} />{formatDate(r.updated_at)}{r.is_hidden && <span className="text-amber-700">· Hidden by a moderator</span>}</div>
                    {r.comment && <p className="mt-2 text-sm text-slate-700">{r.comment}</p>}
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => setEditing(r.id)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100" aria-label="Edit"><Pencil size={15} /></button>
                    <button onClick={() => setDeleting(r)} className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-50 hover:text-rose-600" aria-label="Delete"><Trash2 size={15} /></button>
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
      <ConfirmDialog open={!!deleting} title="Delete this review?" danger confirmLabel="Delete" onConfirm={remove} onClose={() => setDeleting(null)} message={`Your review of ${deleting?.destination_name} will be removed.`} />
    </main>
  )
}
