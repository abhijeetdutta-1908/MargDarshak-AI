import axios from 'axios'

const TOKEN_KEY = 'margdarshak_token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

const api = axios.create({ baseURL: '/api', timeout: 20000 })

api.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Expired or revoked session: drop the token and send the user to sign in again.
api.interceptors.response.use(undefined, (err) => {
  const url = err.config?.url || ''
  if (err.response?.status === 401 && tokenStore.get() && !url.startsWith('/auth/')) {
    tokenStore.clear()
    window.location.assign(`/login?expired=1`)
  }
  return Promise.reject(err)
})

// Turn any API failure into one sentence a user can read.
export function errorMessage(err, fallback = 'Something went wrong. Please try again.') {
  if (!err?.response) {
    return err?.code === 'ECONNABORTED' ? 'The server took too long to respond.' : 'Cannot reach the server.'
  }
  if (err.response.status === 429) return 'Too many requests. Please wait a moment and try again.'
  const detail = err.response.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    const d = detail[0]
    const field = d.loc?.slice(1).join('.')
    const msg = d.msg.replace(/^Value error, /, '')
    return field ? `${field.replace(/_/g, ' ')}: ${msg}` : msg
  }
  if (err.response.status >= 500) return 'The server had a problem. Please try again shortly.'
  return fallback
}

const data = (p) => p.then((r) => r.data)

export const getHealth = () => data(api.get('/health'))
export const getConfig = () => data(api.get('/config'))

export const auth = {
  register: (body) => data(api.post('/auth/register', body)),
  login: (body) => data(api.post('/auth/login', body)),
  me: () => data(api.get('/auth/me')),
  logout: () => api.post('/auth/logout'),
}

export const users = {
  update: (body) => data(api.put('/users/me', body)),
  changePassword: (body) => data(api.post('/users/me/password', body)),
  getPreferences: () => data(api.get('/preferences')),
  putPreferences: (body) => data(api.put('/preferences', body)),
}

export const destinations = {
  list: (params) => data(api.get('/destinations', { params })),
  search: (q, params) => data(api.get('/destinations/search', { params: { q, ...params } })),
  get: (id) => data(api.get(`/destinations/${id}`)),
  hotels: (id, params) => data(api.get(`/hotels/${id}`, { params })),
  hotel: (hotelId) => data(api.get(`/hotels/item/${hotelId}`)),
  places: (id, params) => data(api.get(`/places/${id}`, { params })),
  weather: (id) => data(api.get(`/weather/${id}`)),
  reviews: (id, params) => data(api.get(`/destinations/${id}/reviews`, { params })),
}

export const recommend = (body) => data(api.post('/recommendations', body, { timeout: 30000 }))
export const optimizeRoute = (body) => data(api.post('/routes/optimize', body))

export const trips = {
  generate: (body) => data(api.post('/trips/generate', body, { timeout: 60000 })),
  list: (params) => data(api.get('/trips', { params })),
  get: (id) => data(api.get(`/trips/${id}`)),
  update: (id, body) => data(api.put(`/trips/${id}`, body)),
  remove: (id) => api.delete(`/trips/${id}`),
  duplicate: (id) => data(api.post(`/trips/${id}/duplicate`)),
  share: (id) => data(api.post(`/trips/${id}/share`)),
  unshare: (id) => api.delete(`/trips/${id}/share`),
  complete: (id) => data(api.post(`/trips/${id}/complete`)),
  regenerate: (id) => data(api.post(`/trips/${id}/itinerary/regenerate`, null, { timeout: 60000 })),
  shared: (token) => data(api.get(`/shared/${token}`)),
  dashboard: () => data(api.get('/dashboard')),
}

export const reviews = {
  create: (destinationId, body) => data(api.post(`/destinations/${destinationId}/reviews`, body)),
  update: (id, body) => data(api.put(`/reviews/${id}`, body)),
  remove: (id) => api.delete(`/reviews/${id}`),
  mine: () => data(api.get('/reviews/me')),
  recent: (limit = 6) => data(api.get('/reviews/recent', { params: { limit } })),
}

export const admin = {
  stats: () => data(api.get('/admin/stats')),
  createDestination: (body) => data(api.post('/admin/destinations', body)),
  updateDestination: (id, body) => data(api.put(`/admin/destinations/${id}`, body)),
  deleteDestination: (id) => api.delete(`/admin/destinations/${id}`),
  hotels: (destinationId) => data(api.get('/admin/hotels', { params: { destination_id: destinationId } })),
  createHotel: (body) => data(api.post('/admin/hotels', body)),
  updateHotel: (id, body) => data(api.put(`/admin/hotels/${id}`, body)),
  deleteHotel: (id) => api.delete(`/admin/hotels/${id}`),
  users: (params) => data(api.get('/admin/users', { params })),
  setAdmin: (id, isAdmin) => data(api.put(`/admin/users/${id}`, { is_admin: isAdmin })),
  reviews: (params) => data(api.get('/admin/reviews', { params })),
  moderate: (id, hidden) => data(api.put(`/admin/reviews/${id}`, { is_hidden: hidden })),
  deleteReview: (id) => api.delete(`/admin/reviews/${id}`),
}

export default api
