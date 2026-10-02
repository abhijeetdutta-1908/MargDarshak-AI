// Must match the Literal types in backend/app/schemas/preferences.py.
export const DESTINATION_TYPES = ['beach', 'mountain', 'historical', 'religious', 'adventure', 'wildlife', 'city', 'nature', 'cultural']
export const INTERESTS = ['trekking', 'photography', 'food', 'shopping', 'adventure', 'nature', 'history', 'culture', 'nightlife', 'relaxation', 'wildlife']
export const HOTEL_TIERS = ['budget', 'standard', 'premium', 'luxury']
export const TRANSPORT = [
  ['public', 'Public transport'],
  ['car', 'Car'],
  ['bike', 'Bike'],
  ['taxi', 'Taxi'],
  ['mixed', 'Mixed'],
]
export const FOOD = [
  ['veg', 'Vegetarian'],
  ['non-veg', 'Non-vegetarian'],
  ['both', 'Both'],
]

export const passwordProblem = (pw) => {
  if (pw.length < 8) return 'At least 8 characters'
  if (/^[a-z]+$/i.test(pw) || /^\d+$/.test(pw)) return 'Mix letters with a number or symbol'
  return null
}
