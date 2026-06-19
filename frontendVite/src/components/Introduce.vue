<template>
  <div class="min-h-screen p-8">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold text-white mb-8 font-headline">功能介绍</h1>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div v-for="feature in features" :key="feature.title" class="bg-black/30 backdrop-blur-md rounded-custom shadow-xl border border-white/10 p-6">
          <div class="text-4xl mb-4">{{ feature.icon }}</div>
          <h3 class="text-xl font-semibold text-white mb-2 font-headline">{{ feature.title }}</h3>
          <p class="text-gray-300">{{ feature.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'IntroduceComponent',
  data() {
    return {
      features: [
        { icon: '✍️', title: '手写文字生成', description: '将您输入的文字转换为逼真的手写效果，支持多种字体风格。' },
        { icon: '📄', title: '多页支持', description: '支持长文本自动分页，可生成多页手写文档。' },
        { icon: '🎨', title: '自定义样式', description: '支持自定义字体、背景图片、纸张模板等，打造个性化手写效果。' },
        { icon: '📥', title: '多种导出', description: '支持导出为 PNG 图片或 PDF 文档，满足不同需求。' }
      ]
    }
  }
}
</script>
