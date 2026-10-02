import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 15000 })

export const getHealth = () => api.get('/health').then((r) => r.data)

export default api
