<template>
  <div v-if="showInstallPrompt" class="fixed bottom-5 left-5 right-5 bg-black/80 backdrop-blur-md rounded-custom shadow-xl border border-white/10 z-50 animate-slideUp">
    <div class="flex items-center p-4 gap-3">
      <div class="flex-shrink-0">
        <img src="/favicon-96x96.png" alt="App Icon" class="w-12 h-12 rounded-lg">
      </div>
      <div class="flex-1">
        <h3 class="text-base font-semibold text-white mb-1">安装手写生成器</h3>
        <p class="text-sm text-gray-300">将此应用添加到主屏幕，获得更好的使用体验</p>
      </div>
      <div class="flex gap-2">
        <button class="btn-primary px-4 py-2" @click="installApp">安装</button>
        <button class="btn-secondary px-4 py-2" @click="dismissPrompt">稍后</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PWAInstallPrompt',
  data() {
    return { showInstallPrompt: false, deferredPrompt: null }
  },
  mounted() {
    const dismissed = this.getCookie('pwa-install-dismissed') === '1'
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      if (dismissed) return
      this.deferredPrompt = e
      this.showInstallPrompt = true
    })
    window.addEventListener('appinstalled', () => {
      this.showInstallPrompt = false
      this.deferredPrompt = null
    })
  },
  methods: {
    async installApp() {
      if (!this.deferredPrompt) return
      this.deferredPrompt.prompt()
      const { outcome } = await this.deferredPrompt.userChoice
      if (outcome === 'dismissed') this.setCookie('pwa-install-dismissed', '1', 3650)
      this.deferredPrompt = null
      this.showInstallPrompt = false
    },
    dismissPrompt() {
      this.showInstallPrompt = false
      this.setCookie('pwa-install-dismissed', '1', 3650)
    },
    setCookie(name, value, days) {
      const expires = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString()
      document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`
    },
    getCookie(name) {
      const target = `${name}=`
      const cookies = document.cookie ? document.cookie.split('; ') : []
      for (const item of cookies) {
        if (item.startsWith(target)) return decodeURIComponent(item.substring(target.length))
      }
      return null
    }
  }
}
</script>

<style scoped>
@keyframes slideUp {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.animate-slideUp { animation: slideUp 0.3s ease-out; }
</style>
