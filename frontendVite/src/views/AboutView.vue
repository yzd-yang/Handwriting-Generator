<template>
  <div class="min-h-screen p-8">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold text-white mb-8 font-headline">关于手写文字生成网站</h1>
      <div class="bg-black/30 backdrop-blur-md rounded-custom shadow-xl border border-white/10 p-6 space-y-6">
        <div>
          <h2 class="text-xl font-semibold text-white mb-3 font-headline">项目简介</h2>
          <p class="text-gray-300">这是一个在线手写文字生成工具，可以将您输入的文字转换为逼真的手写效果图片或 PDF。</p>
        </div>
        <div>
          <h2 class="text-xl font-semibold text-white mb-3 font-headline">主要功能</h2>
          <ul class="list-disc list-inside text-gray-300 space-y-2">
            <li>支持多种字体选择</li>
            <li>自定义背景图片</li>
            <li>调节字体大小、行间距、边距等参数</li>
            <li>段落排版（对齐、缩进、段间距）</li>
            <li>纸张模板（空白、单线、方格、点阵）</li>
            <li>多页预览</li>
            <li>导出为图片或 PDF</li>
          </ul>
        </div>
        <div>
          <h2 class="text-xl font-semibold text-white mb-3 font-headline">隐私说明</h2>
          <ul class="list-disc list-inside text-gray-300 space-y-2">
            <li>您上传的文件仅用于生成手写效果，不会被存储或分享</li>
            <li>生成的结果在下载后会被自动删除</li>
            <li>我们不会收集您的个人信息</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default { name: 'AboutView' }
</script>
