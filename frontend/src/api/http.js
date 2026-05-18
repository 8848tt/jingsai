import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

api.defaults.xsrfCookieName = 'csrftoken'
api.defaults.xsrfHeaderName = 'X-CSRFToken'

export async function initCsrf() {
  await api.get('/auth/csrf/')
}

api.interceptors.request.use((config) => {
  const m = document.cookie.match(/csrftoken=([^;]+)/)
  if (
    m &&
    ['post', 'put', 'patch', 'delete'].includes((config.method || '').toLowerCase())
  ) {
    config.headers['X-CSRFToken'] = decodeURIComponent(m[1])
  }
  return config
})

export function getErrorMessage(e, fallback) {
  const d = e?.response?.data
  if (!d) return fallback || '请求失败'
  if (typeof d === 'string') {
    if (d.startsWith('<!') || d.startsWith('<html')) return fallback || '请求失败'
    return d
  }
  if (d.detail) return typeof d.detail === 'string' ? d.detail : String(d.detail)
  const keys = Object.keys(d)
  if (keys.length) {
    const v = d[keys[0]]
    return Array.isArray(v) ? `${keys[0]}: ${v[0]}` : String(v)
  }
  return fallback || '请求失败'
}

export default api
