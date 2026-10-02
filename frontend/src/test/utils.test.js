import { describe, expect, it } from 'vitest'
import { errorMessage } from '../services/api'
import { inr, minutesLabel, seasonLabel } from '../utils/format'
import { EMPTY_PLAN, planFromPreferences, toRequest, validatePlan } from '../utils/plan'

describe('validatePlan', () => {
  const valid = { ...EMPTY_PLAN, interests: ['trekking'] }

  it('accepts a sensible plan', () => {
    expect(validatePlan(valid, '2026-10-01')).toEqual({})
  })

  it('flags each invalid field', () => {
    const e = validatePlan({ ...EMPTY_PLAN, duration: 0, budget_max: '', travelers: 0, travel_date: '2026-01-01' }, '2026-10-01')
    expect(Object.keys(e).sort()).toEqual(['budget_max', 'duration', 'interests', 'travel_date', 'travelers'])
  })

  it('rejects min budget above max and over-long notes', () => {
    const e = validatePlan({ ...valid, budget_min: 50000, budget_max: 10000, notes: 'x'.repeat(301) }, '2026-10-01')
    expect(e.budget_min).toMatch(/cannot exceed/)
    expect(e.notes).toBeTruthy()
  })

  it('accepts free-text notes instead of chips', () => {
    expect(validatePlan({ ...EMPTY_PLAN, notes: 'quiet beaches' }, '2026-10-01')).toEqual({})
  })
})

describe('toRequest / planFromPreferences', () => {
  it('builds an API body with numbers and nulls', () => {
    const body = toRequest({ ...EMPTY_PLAN, interests: ['food'], duration: '3', budget_max: '15000', travelers: '2', starting_location: '  Puri ' })
    expect(body).toMatchObject({ budget: 15000, duration: 3, travelers: 2, interests: ['food'], hotel_preference: null, starting_location: 'Puri', travel_date: null })
  })

  it('prefills from saved preferences', () => {
    const f = planFromPreferences({ interests: ['history'], hotel_preference: 'luxury', budget_max: 90000, travelers: null })
    expect(f).toMatchObject({ interests: ['history'], hotel_preference: 'luxury', budget_max: 90000, travelers: 2 })
  })
})

describe('format helpers', () => {
  it('formats rupees in Indian grouping', () => {
    expect(inr(1234567)).toBe('₹12,34,567')
    expect(inr(null)).toBe('—')
  })

  it('summarises seasons, including ranges that wrap the year', () => {
    expect(seasonLabel([10, 11, 12, 1, 2, 3])).toBe('Oct–Mar')
    expect(seasonLabel([3, 4, 5, 6, 10, 11, 12])).toBe('Mar–Jun, Oct–Dec')
    expect(seasonLabel([5])).toBe('May')
    expect(seasonLabel([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])).toBe('Year-round')
  })

  it('labels durations', () => {
    expect(minutesLabel(45)).toBe('45 min')
    expect(minutesLabel(125)).toBe('2 h 5 min')
    expect(minutesLabel(120)).toBe('2 h')
  })
})

describe('errorMessage', () => {
  it('handles network failures and timeouts', () => {
    expect(errorMessage({})).toMatch(/reach the server/)
    expect(errorMessage({ code: 'ECONNABORTED' })).toMatch(/too long/)
  })

  it('reads FastAPI string and validation errors', () => {
    expect(errorMessage({ response: { status: 409, data: { detail: 'Email taken' } } })).toBe('Email taken')
    const v = { response: { status: 422, data: { detail: [{ loc: ['body', 'budget_min'], msg: 'Value error, budget_min cannot exceed budget_max' }] } } }
    expect(errorMessage(v)).toBe('budget min: budget_min cannot exceed budget_max')
  })

  it('hides server internals', () => {
    expect(errorMessage({ response: { status: 500, data: '<html>Traceback</html>' } })).toMatch(/server had a problem/)
    expect(errorMessage({ response: { status: 429, data: {} } })).toMatch(/Too many requests/)
  })
})
