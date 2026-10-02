import { CheckCircle2, Info, TriangleAlert } from 'lucide-react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { inr, titleCase } from '../utils/format'

const COLORS = { accommodation: '#05916d', transportation: '#0284c7', food: '#fb8f1f', activities: '#7c3aed', miscellaneous: '#94a3b8' }

export default function BudgetBreakdown({ budget, compact = false }) {
  if (!budget?.components) return null
  const rows = Object.entries(budget.components).map(([k, v]) => ({ key: k, name: titleCase(k), value: v.average, ...v }))
  const over = budget.requested && budget.average > budget.requested
  return (
    <div className="@container">
      <div className="grid items-center gap-6 @md:grid-cols-[180px_1fr]">
        <div className="relative mx-auto h-44 w-44">
          <ResponsiveContainer>
            <PieChart>
              <Pie data={rows} dataKey="value" nameKey="name" innerRadius={52} outerRadius={80} paddingAngle={2} stroke="none">
                {rows.map((r) => <Cell key={r.key} fill={COLORS[r.key]} />)}
              </Pie>
              <Tooltip formatter={(v) => inr(v)} />
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-[11px] text-slate-500">Estimated</span>
            <span className="font-display text-lg font-bold">{inr(budget.average)}</span>
          </div>
        </div>
        <table className="w-full text-sm">
          <tbody>
            {rows.map((r) => (
              <tr key={r.key} className="border-b border-slate-100 last:border-0">
                <td className="py-2"><span className="mr-2 inline-block h-2.5 w-2.5 rounded-full" style={{ background: COLORS[r.key] }} />{r.name}</td>
                <td className="py-2 text-right font-medium">{inr(r.average)}</td>
                {!compact && <td className="hidden py-2 pl-3 text-right text-xs text-slate-400 @lg:table-cell">{inr(r.min)}–{inr(r.max)}</td>}
              </tr>
            ))}
            <tr><td className="pt-3 font-semibold">Estimated total</td><td className="pt-3 text-right font-display text-base font-bold">{inr(budget.average)}</td></tr>
          </tbody>
        </table>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-2 text-center">
        {[['Minimum', budget.minimum], ['Average', budget.average], ['Maximum', budget.maximum]].map(([l, v]) => (
          <div key={l} className="rounded-xl bg-slate-50 p-3">
            <p className="text-xs text-slate-500">{l}</p>
            <p className="font-semibold">{inr(v)}</p>
          </div>
        ))}
      </div>
      <p className="mt-2 text-center text-xs text-slate-500">{inr(budget.per_person)} per person · {budget.travelers} traveller{budget.travelers > 1 ? 's' : ''} · {budget.duration_days} days</p>

      {budget.requested && (
        <div className={`mt-4 flex items-center gap-2 rounded-xl p-3 text-sm ${over ? 'bg-amber-50 text-amber-800' : 'bg-brand-50 text-brand-800'}`}>
          {over ? <TriangleAlert size={16} /> : <CheckCircle2 size={16} />}
          {over ? `About ${inr(budget.average - budget.requested)} over your ${inr(budget.requested)} budget.` : `Within your ${inr(budget.requested)} budget.`}
        </div>
      )}
      {!compact && budget.assumptions && (
        <details className="mt-4 text-sm">
          <summary className="flex cursor-pointer items-center gap-1.5 text-slate-600"><Info size={14} />How this was calculated</summary>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-600">
            {budget.assumptions.map((a) => <li key={a}>{a}</li>)}
            <li className="text-slate-500">{budget.note}</li>
          </ul>
        </details>
      )}
    </div>
  )
}
