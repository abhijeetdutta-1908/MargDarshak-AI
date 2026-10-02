import { fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import BudgetBreakdown from '../components/BudgetBreakdown'
import GenerationProgress, { TRIP_STEPS } from '../components/GenerationProgress'
import { ChipGroup, ConfirmDialog, ScoreRing, SourceBadge, Stars } from '../components/ui'

function Chips() {
  const [v, setV] = useState(['beach'])
  return <ChipGroup options={['beach', 'mountain']} value={v} onChange={setV} />
}

describe('ChipGroup', () => {
  it('toggles selection and exposes aria-pressed', () => {
    render(<Chips />)
    const beach = screen.getByRole('button', { name: 'beach' })
    const mountain = screen.getByRole('button', { name: 'mountain' })
    expect(beach).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(mountain)
    fireEvent.click(beach)
    expect(mountain).toHaveAttribute('aria-pressed', 'true')
    expect(beach).toHaveAttribute('aria-pressed', 'false')
  })
})

describe('ConfirmDialog', () => {
  it('confirms, cancels and closes on Escape', () => {
    const onConfirm = vi.fn()
    const onClose = vi.fn()
    render(<ConfirmDialog open title="Delete trip?" message="Gone forever" confirmLabel="Delete" onConfirm={onConfirm} onClose={onClose} />)
    expect(screen.getByRole('dialog', { name: 'Delete trip?' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))
    expect(onConfirm).toHaveBeenCalledOnce()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })

  it('renders nothing when closed', () => {
    render(<ConfirmDialog open={false} title="x" message="y" onConfirm={() => {}} onClose={() => {}} />)
    expect(screen.queryByRole('dialog')).toBeNull()
  })
})

describe('Stars / ScoreRing / SourceBadge', () => {
  it('lets the user pick a rating', () => {
    const onChange = vi.fn()
    render(<Stars value={2} onChange={onChange} />)
    fireEvent.click(screen.getByRole('button', { name: '4 stars' }))
    expect(onChange).toHaveBeenCalledWith(4)
  })

  it('shows the rounded score', () => {
    render(<ScoreRing score={91.6} />)
    expect(screen.getByLabelText('Match score 91.6 out of 100')).toHaveTextContent('92')
  })

  it('labels fallback data so it is never shown as live', () => {
    const { rerender } = render(<SourceBadge source="fallback" />)
    expect(screen.getByText('Seasonal guidance')).toBeInTheDocument()
    rerender(<SourceBadge source="live" />)
    expect(screen.getByText('Live')).toBeInTheDocument()
  })
})

const budget = {
  components: {
    accommodation: { min: 6000, average: 6000, max: 6000 },
    transportation: { min: 3400, average: 4000, max: 5200 },
    food: { min: 3000, average: 3500, max: 4500 },
    activities: { min: 1600, average: 2000, max: 2800 },
    miscellaneous: { min: 1000, average: 1000, max: 1200 },
  },
  minimum: 15000, average: 16500, maximum: 19700, per_person: 8250, travelers: 2, duration_days: 3,
  requested: 15000, assumptions: ['2 nights × 1 room'], note: 'Estimates',
}

describe('BudgetBreakdown', () => {
  it('shows components, range and an over-budget warning', () => {
    render(<BudgetBreakdown budget={budget} />)
    expect(screen.getByText('Accommodation')).toBeInTheDocument()
    expect(screen.getAllByText('₹16,500').length).toBeGreaterThan(0)
    expect(screen.getByText('₹19,700')).toBeInTheDocument()
    expect(screen.getByText(/₹1,500 over your ₹15,000 budget/)).toBeInTheDocument()
  })

  it('confirms when within budget', () => {
    render(<BudgetBreakdown budget={{ ...budget, requested: 20000 }} />)
    expect(screen.getByText(/Within your ₹20,000 budget/)).toBeInTheDocument()
  })
})

describe('GenerationProgress', () => {
  it('lists every pipeline step and the final message when done', () => {
    render(<GenerationProgress done />)
    TRIP_STEPS.forEach((s) => expect(screen.getByText(s)).toBeInTheDocument())
    expect(screen.getByText('Your personalized trip is ready!')).toBeInTheDocument()
  })
})
