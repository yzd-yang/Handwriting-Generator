import './style.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import i18n from './i18n'
import Swal from 'sweetalert2'
import { createHead } from '@vueuse/head'
import * as Sentry from '@sentry/vue'
import http from './utils/http'

const app = createApp(App)
const head = createHead()

// Sentry 错误监控：仅当配置了 DSN 时启用
const sentry_dsn = import.meta.env.VITE_SENTRY_DSN || ''
if (sentry_dsn) {
  Sentry.init({
    app,
    dsn: sentry_dsn,
    integrations: [
      Sentry.browserTracingIntegration({
        tracePropagationTargets: ['localhost', /^https:\/\/yourserver\.io\/api/]
      }),
      Sentry.replayIntegration()
    ],
    tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || 0.1),
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0
  })
} else {
  console.warn('Sentry DSN 未配置，错误上报已禁用')
}

app.use(store)
app.use(router)
app.use(i18n)
app.use(head)

app.config.globalProperties.$http = http
app.config.globalProperties.$swal = Swal

app.mount('#app')

// Google Analytics（仅生产环境 + 配置了 ID 时注入）
const isProd = import.meta.env.PROD
const gaId = import.meta.env.VITE_GA_ID || ''
if (isProd && gaId) {
  const gaScript = document.createElement('script')
  gaScript.async = true
  gaScript.src = `https://www.googletagmanager.com/gtag/js?id=${gaId}`
  document.head.appendChild(gaScript)
  gaScript.onload = () => {
    window.dataLayer = window.dataLayer || []
    function gtag() { window.dataLayer.push(arguments) }
    gtag('js', new Date())
    gtag('config', gaId)
  }
}

// Microsoft Clarity（仅生产环境 + 配置了 ID 时注入）
const clarityId = import.meta.env.VITE_CLARITY_ID || ''
if (isProd && clarityId) {
  const clarityScript = document.createElement('script')
  clarityScript.async = true
  clarityScript.src = `https://www.clarity.ms/tag/${clarityId}`
  document.head.appendChild(clarityScript)
}

// Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      const registrations = await navigator.serviceWorker.getRegistrations()
      for (const reg of registrations) {
        if (reg.active?.scriptURL?.includes('sw.js')) await reg.unregister()
      }
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        window.location.reload()
      })
    } catch (error) {
      console.error('[SW] 初始化失败:', error)
    }
  })
}
