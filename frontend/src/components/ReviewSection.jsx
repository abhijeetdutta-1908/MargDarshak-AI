import { MessageSquareText, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuth } from '../context/AuthContext'
import useApi from '../hooks/useApi'
import { destinations, errorMessage, reviews } from '../services/api'
import { formatDate } from '../utils/format'
import { Button, ConfirmDialog, EmptyState, ErrorState, Skeleton, Stars, inputClass } from './ui'

export function ReviewForm({ initial, onSubmit, onCancel, submitLabel = 'Post review' }) {
  const [rating, setRating] = useState(initial?.rating || 0)
  const [comment, setComment] = useState(initial?.comment || '')
  const [busy, setBusy] = useState(false)
  const submit = async (e) => {
    e.preventDefault()
    if (!rating) return toast.error('Choose a star rating')
    setBusy(true)
    try {
      await onSubmit({ rating, comment })
    } finally {
      setBusy(false)
    }
  }
  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="flex items-center gap-2"><span className="text-sm text-slate-600">Your rating</span><Stars value={rating} size={22} onChange={setRating} /></div>
      <textarea className={`${inputClass} min-h-24`} maxLength={2000} placeholder="What stood out? Tips for other travellers?" value={comment} onChange={(e) => setComment(e.target.value)} />
      <div className="flex gap-2">
        <Button type="submit" loading={busy}>{submitLabel}</Button>
        {onCancel && <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>}
      </div>
    </form>
  )
}

export default function ReviewSection({ destinationId }) {
  const { user } = useAuth()
  const { data, error, loading, reload } = useApi(() => destinations.reviews(destinationId, { page_size: 20 }), [destinationId])
  const [editing, setEditing] = useState(false)
  const [toDelete, setToDelete] = useState(null)

  if (loading) return <Skeleton className="h-40" />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const mine = user && data.items.find((r) => r.user_id === user.id)
  const create = async (body) => {
    try {
      await reviews.create(destinationId, body)
      toast.success('Thanks for your review!')
      reload()
    } catch (e) { toast.error(errorMessage(e)) }
  }
  const update = async (body) => {
    try {
      await reviews.update(mine.id, body)
      toast.success('Review updated')
      setEditing(false)
      reload()
    } catch (e) { toast.error(errorMessage(e)) }
  }
  const remove = async () => {
    try {
      await reviews.remove(toDelete.id)
      toast.success('Review deleted')
      setToDelete(null)
      reload()
    } catch (e) { toast.error(errorMessage(e)) }
  }

  return (
    <div className="grid *:min-w-0 gap-6 lg:grid-cols-[220px_1fr]">
      <div>
        <p className="font-display text-5xl font-bold">{data.average_rating ?? '—'}</p>
        <Stars value={data.average_rating || 0} size={16} />
        <p className="mt-1 text-sm text-slate-500">{data.review_count} review{data.review_count === 1 ? '' : 's'}</p>
        <div className="mt-4 space-y-1">
          {[5, 4, 3, 2, 1].map((n) => {
            const c = data.distribution[n] || 0
            return (
              <div key={n} className="flex items-center gap-2 text-xs text-slate-500">
                <span className="w-3">{n}</span>
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-saffron-400" style={{ width: `${data.review_count ? (c / data.review_count) * 100 : 0}%` }} /></div>
                <span className="w-4 text-right">{c}</span>
              </div>
            )
          })}
        </div>
      </div>
      <div className="space-y-4">
        {!user && <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600"><Link to="/login" className="font-semibold text-brand-700">Sign in</Link> to share your experience.</p>}
        {user && !mine && <div className="rounded-xl border border-slate-200 p-4"><p className="mb-3 font-semibold">Write a review</p><ReviewForm onSubmit={create} /></div>}
        {data.items.length === 0 ? (
          <EmptyState icon={MessageSquareText} title="No reviews yet">Be the first to review this destination.</EmptyState>
        ) : data.items.map((r) => (
          <article key={r.id} className="rounded-xl border border-slate-200 p-4">
            {editing && mine?.id === r.id ? (
              <ReviewForm initial={r} onSubmit={update} onCancel={() => setEditing(false)} submitLabel="Save changes" />
            ) : (
              <>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold">{r.user_name}{mine?.id === r.id && <span className="ml-2 text-xs font-normal text-brand-700">(you)</span>}</p>
                    <div className="flex items-center gap-2 text-xs text-slate-500"><Stars value={r.rating} size={12} />{formatDate(r.updated_at)}</div>
                  </div>
                  {mine?.id === r.id && (
                    <div className="flex gap-1">
                      <button className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100" onClick={() => setEditing(true)} aria-label="Edit review"><Pencil size={15} /></button>
                      <button className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-50 hover:text-rose-600" onClick={() => setToDelete(r)} aria-label="Delete review"><Trash2 size={15} /></button>
                    </div>
                  )}
                </div>
                {r.comment && <p className="mt-2 text-sm text-slate-700">{r.comment}</p>}
              </>
            )}
          </article>
        ))}
      </div>
      <ConfirmDialog open={!!toDelete} title="Delete your review?" message="This can't be undone." confirmLabel="Delete" danger onConfirm={remove} onClose={() => setToDelete(null)} />
    </div>
  )
}
