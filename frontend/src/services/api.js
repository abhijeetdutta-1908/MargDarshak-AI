import axios from 'axios'

const TOKEN_KEY = 'margdarshak_token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

const api = axios.create({ baseURL: '/api', timeout: 15000 })

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
  const detail = err.response.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    const d = detail[0]
    const field = d.loc?.slice(1).join('.')
    return field ? `${field}: ${d.msg.replace(/^Value error, /, '')}` : d.msg
  }
  return fallback
}

export const getHealth = () => api.get('/health').then((r) => r.data)

export const auth = {
  register: (body) => api.post('/auth/register', body).then((r) => r.data),
  login: (body) => api.post('/auth/login', body).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
  logout: () => api.post('/auth/logout'),
}

export const users = {
  update: (body) => api.put('/users/me', body).then((r) => r.data),
  changePassword: (body) => api.post('/users/me/password', body).then((r) => r.data),
  getPreferences: () => api.get('/preferences').then((r) => r.data),
  putPreferences: (body) => api.put('/preferences', body).then((r) => r.data),
}

export default api
