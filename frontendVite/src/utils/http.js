import axios from 'axios'
import axiosRetry from 'axios-retry'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

axiosRetry(http, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: error => {
    if (error.response?.status === 503 && error.response?.data?.status === 'queue_full') {
      return false
    }
    return axiosRetry.isNetworkError(error) || axiosRetry.isRetryableError(error)
  },
  onRetry: (retryCount, error) => {
    console.warn(`请求重试第 ${retryCount} 次，原因：${error.message}`)
  }
})

export default http
