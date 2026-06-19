<template>
  <div class="min-h-screen">
    <router-view />
    <PWAInstallPrompt />
  </div>
</template>

<script>
import PWAInstallPrompt from './components/PWAInstallPrompt.vue'
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useHead } from '@vueuse/head'

export default {
  name: 'App',
  components: { PWAInstallPrompt },
  setup() {
    const route = useRoute()
    const site = window.location.origin
    const defaultTitle = '手写文字生成网站 - 在线生成手写图片与 PDF'
    const defaultDesc = '手写文字生成网站，支持多种字体和背景，在线生成高质量手写文字图片与 PDF。'

    const title = computed(() => route.meta?.title || defaultTitle)
    const description = computed(() => route.meta?.description || defaultDesc)
    const robots = computed(() => route.meta?.robots || 'index, follow')
    const canonical = computed(() => site + route.fullPath)

    useHead(() => ({
      title: title.value,
      meta: [
        { name: 'description', content: description.value },
        { name: 'robots', content: robots.value },
        { property: 'og:type', content: 'website' },
        { property: 'og:url', content: canonical.value },
        { property: 'og:title', content: title.value },
        { property: 'og:description', content: description.value },
        { property: 'og:image', content: '/default1.webp' },
      ],
      link: [{ rel: 'canonical', href: canonical.value }]
    }))

    return {}
  }
}
</script>
