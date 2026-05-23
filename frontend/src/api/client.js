import axios from 'axios'

const RAW_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
export const API_BASE_URL = RAW_BASE_URL.replace(/\/+$/, '')

const API = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  withCredentials: false,
})

function clearAuthAndRedirect() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')

  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')

    if (!config.headers) {
      config.headers = {}
    }

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

API.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const detail = error?.response?.data?.detail

    const detailText = typeof detail === 'string' ? detail.toLowerCase() : ''

    const isAuthFailure =
      status === 401 ||
      detailText.includes('token') ||
      detailText.includes('authentication credentials were not provided') ||
      detailText.includes('given token not valid')

    if (isAuthFailure) {
      clearAuthAndRedirect()
    }

    return Promise.reject(error)
  }
)

export default API