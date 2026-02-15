import axios from 'axios'

// 开发时：VITE_API_BASE 留空或未设则用 /api/（走 Vite 代理到后端）；设则直连后端
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aircomp_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('aircomp_token')
      localStorage.removeItem('aircomp_user')
      const url = err.config?.url ?? ''
      const isAuthPage = url.includes('auth/') && (url.includes('auth/sms/') || url.includes('auth/login') || url.includes('auth/register') || url.includes('auth/me'))
      if (!isAuthPage) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api
