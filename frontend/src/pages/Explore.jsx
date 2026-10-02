import { Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import DestinationCard from '../components/DestinationCard'
import { Button, EmptyState, ErrorState, PageHeader, Skeleton, Tabs, inputClass } from '../components/ui'
import useApi from '../hooks/useApi'
import { destinations } from '../services/api'
import { CATEGORY } from '../utils/format'

const PAGE = 12

export default function Explore() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category') || ''
  const q = params.get('q') || ''
  const page = Number(params.get('page') || 1)
  const [text, setText] = useState(q)
  useEffect(() => setText(q), [q])

  const { data, error, loading, reload } = useApi(
    () => destinations.list({ category: category || undefined, q: q || undefined, page, page_size: PAGE }), [category, q, page])

  const update = (next) => {
    const merged = { category, q, page: 1, ...next }
    setParams(Object.fromEntries(Object.entries(merged).filter(([k, v]) => v !== '' && v != null && !(k === 'page' && v === 1))))
  }
  const pages = data ? Math.ceil(data.total / PAGE) : 1

  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <PageHeader eyebrow="Explore" title="Destinations across India" subtitle={data?.cost_note} />
      <div className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <Tabs tabs={[['', 'All'], ...Object.entries(CATEGORY).map(([k, v]) => [k, v.label])]} value={category} onChange={(c) => update({ category: c })} />
        <form onSubmit={(e) => { e.preventDefault(); update({ q: text.trim() }) }} className="relative w-full lg:w-72">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input className={`${inputClass} pl-9`} placeholder="Search Kerala, trekking, temples…" value={text} onChange={(e) => setText(e.target.value)} maxLength={80} aria-label="Search destinations" />
        </form>
      </div>
      {loading ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-72" />)}</div>
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : data.items.length === 0 ? (
        <EmptyState icon={Search} title="No destinations found" action={<Button variant="secondary" onClick={() => setParams({})}>Clear filters</Button>}>
          Nothing matches “{q}”{category && ` in ${CATEGORY[category]?.label}`}.
        </EmptyState>
      ) : (
        <>
          <p className="mb-4 text-sm text-slate-500">{data.total} destination{data.total === 1 ? '' : 's'}</p>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{data.items.map((d) => <DestinationCard key={d.id} d={d} />)}</div>
          {pages > 1 && (
            <nav className="mt-8 flex items-center justify-center gap-2" aria-label="Pagination">
              <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => update({ page: page - 1 })}>Previous</Button>
              <span className="text-sm text-slate-600">Page {page} of {pages}</span>
              <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => update({ page: page + 1 })}>Next</Button>
            </nav>
          )}
        </>
      )}
    </main>
  )
}
