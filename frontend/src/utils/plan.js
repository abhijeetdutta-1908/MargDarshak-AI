// Trip-planning form: defaults, validation and request building (kept pure for tests).

export const todayISO = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10)

export const EMPTY_PLAN = {
  destination_types: [], interests: [], duration: 4, budget_min: '', budget_max: 20000, travel_date: '',
  travelers: 2, hotel_preference: '', transport_preference: '', starting_location: '', food_preference: '', notes: '',
}

export function planFromPreferences(p) {
  if (!p) return { ...EMPTY_PLAN }
  return {
    ...EMPTY_PLAN,
    destination_types: p.destination_types || [],
    interests: p.interests || [],
    budget_min: p.budget_min ?? '',
    budget_max: p.budget_max ?? EMPTY_PLAN.budget_max,
    travelers: p.travelers ?? EMPTY_PLAN.travelers,
    hotel_preference: p.hotel_preference || '',
    transport_preference: p.transport_preference || '',
    starting_location: p.starting_location || '',
    food_preference: p.food_preference || '',
  }
}

export function validatePlan(f, today = todayISO()) {
  const e = {}
  const duration = Number(f.duration)
  if (!Number.isInteger(duration) || duration < 1 || duration > 30) e.duration = 'Trip length must be 1–30 days'
  const max = Number(f.budget_max)
  if (f.budget_max === '' || !Number.isFinite(max) || max <= 0) e.budget_max = 'Enter your maximum budget'
  else if (max > 10_000_000) e.budget_max = 'That budget is too large'
  if (f.budget_min !== '' && Number(f.budget_min) < 0) e.budget_min = 'Budget cannot be negative'
  else if (f.budget_min !== '' && !e.budget_max && Number(f.budget_min) > max) e.budget_min = 'Minimum cannot exceed maximum'
  const travelers = Number(f.travelers)
  if (!Number.isInteger(travelers) || travelers < 1 || travelers > 50) e.travelers = 'Travellers must be 1–50'
  if (f.travel_date && f.travel_date < today) e.travel_date = 'Travel date cannot be in the past'
  if (f.notes && f.notes.length > 300) e.notes = 'Keep it under 300 characters'
  if (!f.destination_types.length && !f.interests.length && !f.notes?.trim()) {
    e.interests = 'Pick at least one interest or destination type, or describe your ideal trip'
  }
  return e
}

/** Body for POST /api/recommendations and /api/trips/generate. */
export function toRequest(f) {
  const opt = (v) => (v === '' || v == null ? null : v)
  return {
    budget: Number(f.budget_max),
    duration: Number(f.duration),
    travelers: Number(f.travelers),
    destination_types: f.destination_types,
    interests: f.interests,
    travel_date: opt(f.travel_date),
    hotel_preference: opt(f.hotel_preference),
    transport_preference: opt(f.transport_preference),
    food_preference: opt(f.food_preference),
    starting_location: opt(f.starting_location?.trim()),
    notes: opt(f.notes?.trim()),
  }
}
