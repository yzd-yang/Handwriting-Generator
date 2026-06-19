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

Sentry.init({
  app,
  dsn: 'https://507b601bbd374cf58b7c5468cb434578@o4505255803551744.ingest.sentry.io/4505485557891072',
  integrations: [
    Sentry.browserTracingIntegration({
      tracePropagationTargets: ['localhost', /^https:\/\/yourserver\.io\/api/]
    }),
    Sentry.replayIntegration()
  ],
  tracesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0
})

app.use(store)
app.use(router)
app.use(i18n)
app.use(head)

app.config.globalProperties.$http = http
app.config.globalProperties.$swal = Swal

app.mount('#app')

// Google Analytics
const gaScript = document.createElement('script')
gaScript.async = true
gaScript.src = 'https://www.googletagmanager.com/gtag/js?id=G-GB1XG89B6Z'
document.head.appendChild(gaScript)

gaScript.onload = () => {
  window.dataLayer = window.dataLayer || []
  function gtag() { window.dataLayer.push(arguments) }
  gtag('js', new Date())
  gtag('config', 'G-GB1XG89B6Z')
}

// Microsoft Clarity
const clarityScript = document.createElement('script')
clarityScript.async = true
clarityScript.src = 'https://www.clarity.ms/tag/ounxp8da5s'
document.head.appendChild(clarityScript)

// Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      const registrations = await navigator.serviceWorker.getRegistrations()
      for (const reg of registrations) {
        if (reg.active?.scriptURL?.includes('sw.js')) await reg.unregister()
      }
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (confirm('网站已更新到新版本，点击确定刷新页面以加载最新内容。')) window.location.reload()
      })
    } catch (error) {
      console.error('[SW] 初始化失败:', error)
    }
  })
}
