<template>
  <div class="flex w-full h-screen p-4 gap-4 overflow-hidden">
    <!-- Left Column - Configuration Form -->
    <div class="w-full md:w-1/2 lg:w-5/12 xl:w-1/3 h-full flex flex-col bg-black/30 backdrop-blur-md rounded-custom shadow-xl border border-white/10 overflow-hidden" data-purpose="config-panel">
      <div class="flex-1 overflow-y-auto p-3 custom-scrollbar">
        <!-- Text & File Input Section -->
        <section class="card-section">
          <h3 class="text-sm font-semibold mb-3 text-white border-b border-white/10 pb-2 font-headline">文本内容</h3>
          <div class="mb-3">
            <label class="block text-sm text-gray-200 mb-1">文字：</label>
            <div class="w-full border border-white/20 rounded-custom overflow-hidden flex flex-col bg-black/30 shadow-sm">
              <TiptapEditor v-model="text" class="max-h-60 overflow-y-auto" />
            </div>
          </div>
          <div class="text-center text-sm text-gray-300 mb-3">或者上传一个文档文件：</div>
          <div class="flex justify-center mb-3">
            <button class="btn-primary py-1 px-3" @click="triggerTextFileInput">选择文件</button>
            <input ref="textFileInput" type="file" accept=".doc,.docx,.pdf,.txt,.rtf" class="hidden" @change="uploadTextFile" />
          </div>
          <div class="mb-3 flex items-center justify-between">
            <label class="input-label">字体文件：</label>
            <div class="flex gap-2 w-full justify-end">
              <button class="btn-primary py-1 px-3 whitespace-nowrap" @click="triggerFontFileInput">选择文件</button>
              <input ref="fontFileInput" type="file" class="hidden" @change="onFontChange" />
              <select v-model="selectedOption" class="border-white/20 rounded-custom focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-sm flex-1 text-white appearance-none text-center bg-white/5 border">
                <option v-for="option in options" :key="option.value" :value="option.value">{{ option.text }}</option>
              </select>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <label class="input-label">背景图片文件：</label>
            <div class="flex gap-2 items-center">
              <button :class="isDimensionSpecified ? 'bg-black/20 text-gray-400 cursor-not-allowed' : 'btn-primary'" :disabled="isDimensionSpecified" class="py-1 px-3" @click="triggerImageFileInput">选择文件</button>
              <input ref="imageFileInput" type="file" class="hidden" @change="onBackgroundImageChange" />
              <span v-if="selectedImageFileName" class="text-xs text-gray-300 max-w-[100px] truncate">{{ selectedImageFileName }}</span>
            </div>
          </div>
        </section>

        <!-- Page Layout Section -->
        <section class="card-section">
          <h3 class="text-sm font-semibold mb-3 text-white border-b border-white/10 pb-2 font-headline">页面布局</h3>
          <div class="flex gap-3 mb-3">
            <div class="flex-1 flex items-center justify-between">
              <label class="input-label">宽度：</label>
              <input v-model="width" type="number" class="input-field w-16 bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]" :disabled="isBackgroundImageSpecified">
            </div>
            <div class="flex-1 flex items-center justify-between">
              <label class="input-label">高度：</label>
              <input v-model="height" type="number" class="input-field w-16 bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]" :disabled="isBackgroundImageSpecified">
            </div>
            <button class="bg-black/20 border border-white/10 rounded px-2 hover:bg-white/10 text-white text-sm" @click="clearDimensions">×</button>
          </div>
          <div class="input-group">
            <label class="input-label">模板：</label>
            <div class="flex gap-1 border border-white/20 rounded-custom overflow-hidden bg-black/30">
              <button
v-for="pt in paperTypes" :key="pt.value" :class="paperType === pt.value ? 'bg-white/10 text-white border border-[#CFE3E8]/50 shadow-sm' : 'text-gray-300 hover:bg-white/10'"
                class="px-2 py-0.5 text-xs rounded m-0.5"
                @click="paperType = pt.value">{{ pt.label }}</button>
            </div>
          </div>
          <div class="input-group">
            <label class="input-label">颜色：</label>
            <div class="flex gap-2 items-center flex-wrap">
              <button
v-for="c in colorPresets" :key="c" :class="paperColor === c ? 'ring-2 ring-[#CFE3E8] ring-offset-1 ring-offset-black/50 scale-110' : 'border-white/20 hover:scale-105'"
                class="w-7 h-7 rounded-md border transition-all"
                :style="{ backgroundColor: c }" @click="paperColor = c"></button>
              <input v-model="paperColor" type="color" class="w-7 h-7 cursor-pointer rounded-md border border-white/20" title="自定义颜色">
            </div>
          </div>
          <div class="input-group">
            <label class="input-label">纸张：</label>
            <div class="flex gap-1 border border-white/20 rounded-custom p-0.5 bg-black/30">
              <button
v-for="p in paperPresets" :key="p.name" :class="width === p.width && height === p.height ? 'bg-white/10 text-white shadow-sm border border-white/10' : 'text-gray-300 hover:bg-white/10'"
                class="px-2 py-0.5 text-xs rounded"
                @click="applyPaperPreset(p)">{{ p.name }}</button>
            </div>
          </div>
          <div class="flex items-center justify-end mb-3">
            <input v-model="enableEnglishSpacing" type="checkbox" class="rounded text-[#CFE3E8] focus:ring-[#CFE3E8] mr-2 border-white/20 bg-black/30">
            <label class="text-xs text-gray-200 cursor-pointer">增大英文单词间距</label>
          </div>
          <div class="grid grid-cols-2 gap-x-3 gap-y-2">
            <div class="flex items-center justify-between col-span-2">
              <label class="input-label">首行缩进（字）：</label>
              <input v-model="firstLineIndent" type="number" class="input-field w-14 bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between col-span-2">
              <label class="input-label">段间距（行）：</label>
              <input v-model="paragraphSpacing" type="number" class="input-field w-14 bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">字体大小：</label>
              <input v-model="fontSize" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">行间距：</label>
              <input v-model="lineSpacing" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">上边距：</label>
              <input v-model="marginTop" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">下边距：</label>
              <input v-model="marginBottom" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">左边距：</label>
              <input v-model="marginLeft" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">右边距：</label>
              <input v-model="marginRight" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
          </div>
        </section>

        <!-- Advanced Perturbations Section -->
        <section class="card-section border-white/10 bg-white/5">
          <div class="flex justify-center mb-3">
            <button class="bg-white/10 text-white px-4 py-1 rounded-custom text-xs hover:bg-white/20 shadow-sm border border-white/10" @click="isExpanded = !isExpanded">
              {{ isExpanded ? '收起' : '更多内容' }}
            </button>
          </div>
          <div v-if="isExpanded" class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">行间距扰动：</label>
              <input v-model="lineSpacingSigma" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">字体大小扰动：</label>
              <input v-model="fontSizeSigma" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">字间距扰动：</label>
              <input v-model="wordSpacingSigma" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">笔画横向偏移：</label>
              <input v-model="perturbXSigma" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">笔画纵向偏移：</label>
              <input v-model="perturbYSigma" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">笔画旋转偏移：</label>
              <input v-model="perturbThetaSigma" type="number" step="0.01" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">字间距：</label>
              <input v-model="wordSpacing" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="border-t border-white/10 pt-2 mt-2">
              <div class="flex items-center justify-between mb-2">
                <label class="input-label text-xs text-gray-400">涂改线长度的标准差：</label>
                <input v-model="strikethrough_length_sigma" type="number" class="input-field w-12 h-6 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
              </div>
              <div class="flex items-center justify-between mb-2">
                <label class="input-label text-xs text-gray-400">涂改线角度的标准差：</label>
                <input v-model="strikethrough_angle_sigma" type="number" class="input-field w-12 h-6 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
              </div>
              <div class="flex items-center justify-between mb-2">
                <label class="input-label text-xs text-gray-400">涂改线宽度的标准差：</label>
                <input v-model="strikethrough_width_sigma" type="number" class="input-field w-12 h-6 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
              </div>
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">涂改出现的几率：</label>
              <input v-model="strikethrough_probability" type="number" step="0.001" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">涂改线宽度：</label>
              <input v-model="strikethrough_width" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
            <div class="flex items-center justify-between">
              <label class="input-label text-xs">墨汁深度标准差：</label>
              <input v-model="ink_depth_sigma" type="number" class="input-field w-14 text-xs bg-white/5 border-white/10 focus:ring-1 focus:ring-[#CFE3E8] focus:border-[#CFE3E8] text-[#f7fdff]">
            </div>
          </div>
        </section>
      </div>

      <!-- Action Buttons -->
      <div class="p-2 bg-black/20 border-t border-white/10 shrink-0">
        <div class="flex flex-wrap gap-1.5 justify-center">
          <button class="px-3 py-1.5 rounded-lg bg-white/10 backdrop-blur-sm border border-white/10 text-white text-xs font-medium transition-all hover:bg-white/20" @click="loadPreset">载入</button>
          <button class="px-3 py-1.5 rounded-lg bg-white/10 backdrop-blur-sm border border-white/10 text-white text-xs font-medium transition-all hover:bg-white/20" @click="savePreset">保存</button>
          <button class="px-3 py-1.5 rounded-lg bg-white/10 backdrop-blur-sm border border-white/10 text-white text-xs font-medium transition-all hover:bg-white/20" @click="resetSettings">重置</button>
          <button :disabled="shouldDisableButtons" class="px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#9E94B2] to-[#CFE3E8] text-[#000D19] text-xs font-bold shadow-lg transition-all hover:opacity-90 disabled:opacity-50" @click="generateHandwriting(true)">
            {{ buttonText || '预览' }}
          </button>
          <button :disabled="shouldDisableButtons" class="px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#9E94B2] to-[#CFE3E8] text-[#000D19] text-xs font-bold shadow-lg transition-all hover:opacity-90 disabled:opacity-50" @click="generateHandwriting(false)">
            {{ buttonText || '生成图片' }}
          </button>
          <button :disabled="shouldDisableButtons" class="px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#9E94B2] to-[#CFE3E8] text-[#000D19] text-xs font-bold shadow-lg transition-all hover:opacity-90 disabled:opacity-50" @click="generateHandwriting(false, true)">
            {{ buttonText || '生成PDF' }}
          </button>
          <div class="relative group">
            <button class="px-3 py-1.5 rounded-lg bg-black/40 backdrop-blur-sm border border-white/20 text-white text-xs font-medium transition-all hover:bg-black/60 text-center">支持</button>
            <div class="absolute right-0 bottom-full mb-1 w-44 rounded-lg bg-black/80 backdrop-blur-md border border-white/20 shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 z-50 overflow-hidden">
              <a href="https://github.com/yzd-yang/Handwriting-Generator" target="_blank" rel="noopener noreferrer" class="block px-4 py-2 text-xs text-white hover:bg-white/10 transition-colors">GitHub  (国外访问)</a>
              <a href="https://gitee.com/yzd01234657980/Handwriting-Generator" target="_blank" rel="noopener noreferrer" class="block px-4 py-2 text-xs text-white hover:bg-white/10 transition-colors">Gitee   (国内访问)</a>
              <div class="border-t border-white/10"></div>
              <p class="px-4 py-2 text-xs text-gray-400 leading-relaxed">本工具完全免费，如有付费请退款</p>
            </div>
          </div>
          <p class="text-center text-gray-400 text-xs mt-3">本工具完全免费，如有付费请退款</p>
        </div>
      </div>
    </div>

    <!-- Right Column - Live Preview -->
    <div class="hidden md:flex flex-1 flex-col bg-black/30 backdrop-blur-md rounded-custom shadow-xl border border-white/10 p-4" data-purpose="preview-panel">
      <div class="text-center mb-4">
        <h2 class="text-xl font-bold text-white tracking-wide font-headline drop-shadow-md">预览</h2>
      </div>
      <div class="flex-1 flex items-center justify-center bg-black/20 rounded-lg border-2 border-dashed border-white/20 overflow-hidden relative backdrop-blur-sm">
        <div v-if="previewImages && previewImages.length > 0" class="w-full max-w-lg aspect-[3/4] bg-white flex items-center justify-center shadow-2xl relative rounded-sm">
          <img :src="previewImages[currentPreviewIndex]" alt="Handwriting Preview" class="object-contain w-full h-full p-4 mix-blend-multiply opacity-80">
        </div>
        <div v-else class="w-full max-w-lg aspect-[3/4] bg-white flex items-center justify-center shadow-2xl relative rounded-sm">
          <div class="absolute inset-0 flex items-center justify-center opacity-40 pointer-events-none">
            <svg class="text-gray-800" fill="none" height="200" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1" viewBox="0 0 24 24" width="200" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 20h9"></path>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
            </svg>
          </div>
        </div>
      </div>
      <div v-if="previewImages && previewImages.length > 1" class="flex justify-center items-center gap-3 mt-3">
        <button :disabled="currentPreviewIndex === 0" class="btn-outline text-xs py-1 px-2 disabled:opacity-50" @click="prevPage">上一页</button>
        <span class="text-xs text-gray-300">{{ currentPreviewIndex + 1 }} / {{ previewImages.length }}</span>
        <button :disabled="currentPreviewIndex === previewImages.length - 1" class="btn-outline text-xs py-1 px-2 disabled:opacity-50" @click="nextPage">下一页</button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import TiptapEditor from '../components/TiptapEditor.vue'
import Swal from 'sweetalert2'
import http from '../utils/http'

export default {
  components: { TiptapEditor },
  data() {
    return {
      text: '', fontFile: null, backgroundImage: null, fontSize: 124, lineSpacing: 200,
      fill: '(0, 0, 0, 255)', width: 2481, height: 3507, marginTop: 50, marginBottom: 50,
      marginLeft: 50, marginRight: 50, previewImage: null, previewImages: [],
      currentPreviewIndex: 0, preview: false, lineSpacingSigma: 0, fontSizeSigma: 2,
      wordSpacingSigma: 2, perturbXSigma: 3, perturbYSigma: 3, perturbThetaSigma: 0.05,
      wordSpacing: 1, endChars: '', errorMessage: '', message: '', uploadMessage: '',
      selectedFontFileName: '', selectedImageFileName: '', selectedOption: '1', options: [],
      isLoading: false, strikethrough_length_sigma: 2, strikethrough_angle_sigma: 2,
      strikethrough_width_sigma: 2, strikethrough_probability: 0.005, strikethrough_width: 8,
      ink_depth_sigma: 30, isUnderlined: true, enableEnglishSpacing: false,
      paragraphLayout: 'default', firstLineIndent: 2, paragraphSpacing: 0,
      paperType: 'blank', paperColor: '#FFFFFF',
      paperTypes: [
        { value: 'blank', label: '空白' }, { value: 'lines', label: '单线' },
        { value: 'grid', label: '方格' }, { value: 'dots', label: '点阵' }
      ],
      paperPresets: [
        { name: 'A4', width: 2481, height: 3507 }, { name: 'A5', width: 1754, height: 2480 },
        { name: 'B5', width: 2953, height: 4169 }, { name: 'Letter', width: 2550, height: 3300 }
      ],
      colorPresets: ['#FFFFFF', '#F5F0E1', '#E3EDF7', '#CCCCCC', '#000000', '#E8DAEF'],
      isExpanded: false, isGenerating: false, lastGenerateTime: 0, generateCooldown: 3000,
      cooldownTimer: null, remainingCooldown: 0, isInCooldownPeriod: false,
      queueFullCountdown: 0, queueFullTotal: 0, queueFullTimer: null,
      localStorageItems: ['text', 'fontSize', 'lineSpacing', 'fill', 'width', 'height',
        'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'selectedFontFileName',
        'selectedOption', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma',
        'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing',
        'strikethrough_length_sigma', 'strikethrough_angle_sigma', 'strikethrough_width_sigma',
        'strikethrough_probability', 'strikethrough_width', 'ink_depth_sigma', 'isUnderlined',
        'enableEnglishSpacing', 'paragraphLayout', 'firstLineIndent', 'paragraphSpacing',
        'paperType', 'paperColor']
    }
  },
  created() {
    this.localStorageItems.forEach(item => {
      const value = localStorage.getItem(item)
      if (value !== null && value !== 'undefined') {
        try { this[item] = JSON.parse(value) } catch (error) { console.error('解析localStorage失败:', item, error) }
      }
    })
    http.get('/api/fonts_info').then(response => {
      this.options = response.data.map((font, index) => ({ value: String(index + 1), text: font }))
    }).catch(error => { if (error.response?.data) this.errorMessage = error.response.data.error })
  },
  computed: {
    isDimensionSpecified() { return !!(this.width || this.height) },
    isBackgroundImageSpecified() { return !!this.backgroundImage },
    shouldDisableButtons() { return this.isGenerating || this.isInCooldownPeriod || this.queueFullCountdown > 0 },
    buttonText() {
      if (this.isGenerating) return '生成中...'
      if (this.isInCooldownPeriod) return `${this.remainingCooldown}s`
      return null
    },
    ...mapState(['login_delete_message'])
  },
  watch: {
    text(newVal) { localStorage.setItem('text', JSON.stringify(newVal)) },
    paperType(newVal) { localStorage.setItem('paperType', JSON.stringify(newVal)); this.isUnderlined = (newVal === 'lines' || newVal === 'grid') },
    paperColor(newVal) { localStorage.setItem('paperColor', JSON.stringify(newVal)) }
  },
  beforeUnmount() { if (this.cooldownTimer) clearInterval(this.cooldownTimer); if (this.queueFullTimer) clearInterval(this.queueFullTimer) },
  methods: {
    prevPage() { if (this.currentPreviewIndex > 0) this.currentPreviewIndex-- },
    nextPage() { if (this.currentPreviewIndex < this.previewImages.length - 1) this.currentPreviewIndex++ },
    triggerTextFileInput() { this.$refs.textFileInput.click() },
    triggerFontFileInput() { this.$refs.fontFileInput.click() },
    triggerImageFileInput() { if (!this.isDimensionSpecified) this.$refs.imageFileInput.click() },
    uploadTextFile(e) {
      const file = e.target.files[0]; if (!file) return
      const formData = new FormData(); formData.append('file', file)
      http.post('/api/textfileprocess', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
        .then(response => { this.text = response.data.text }).catch(error => console.error(error))
    },
    onFontChange(e) {
      const file = e.target.files[0]; if (!file) return
      this.selectedFontFileName = file.name; this.fontFile = file
      const newOption = { value: String(this.options.length + 1), text: this.selectedFontFileName }
      this.options.push(newOption); this.selectedOption = newOption.value
    },
    onBackgroundImageChange(e) {
      const file = e.target.files[0]; if (!file) return
      this.selectedImageFileName = file.name; this.backgroundImage = file
    },
    clearDimensions() { this.width = null; this.height = null },
    applyPaperPreset(preset) { this.width = preset.width; this.height = preset.height },
    loadPreset() {
      try {
        const dataString = localStorage.getItem('myPreset')
        if (!dataString) { Swal.fire({ icon: 'info', title: '没有找到保存的预设设置' }); return }
        Object.keys(JSON.parse(dataString)).forEach(item => { this[item] = JSON.parse(dataString)[item] })
        Swal.fire({ icon: 'success', title: '加载成功', timer: 1500, showConfirmButton: false })
      } catch (error) { Swal.fire({ icon: 'error', title: '加载失败' }) }
    },
    savePreset() {
      try {
        const data = {}; this.localStorageItems.forEach(item => { data[item] = this[item] })
        localStorage.setItem('myPreset', JSON.stringify(data))
        Swal.fire({ icon: 'success', title: '保存成功', timer: 1500, showConfirmButton: false })
      } catch (error) { Swal.fire({ icon: 'error', title: '保存失败' }) }
    },
    resetSettings() {
      this.text = ''; this.fontFile = null; this.backgroundImage = null; this.fontSize = 124; this.lineSpacing = 200
      this.fill = '(0, 0, 0, 255)'; this.width = 2481; this.height = 3507; this.marginTop = 50
      this.marginBottom = 50; this.marginLeft = 50; this.marginRight = 50; this.lineSpacingSigma = 0
      this.fontSizeSigma = 2; this.wordSpacingSigma = 2; this.perturbXSigma = 3; this.perturbYSigma = 3
      this.perturbThetaSigma = 0.05; this.wordSpacing = 1; this.strikethrough_length_sigma = 2
      this.strikethrough_angle_sigma = 2; this.strikethrough_width_sigma = 2
      this.strikethrough_probability = 0.005; this.strikethrough_width = 8; this.ink_depth_sigma = 30
      this.isUnderlined = true; this.enableEnglishSpacing = false; this.paragraphLayout = 'default'
      this.firstLineIndent = 2; this.paragraphSpacing = 0; this.errorMessage = ''; this.message = ''
      this.uploadMessage = ''; this.selectedFontFileName = ''; this.selectedImageFileName = ''
      this.selectedOption = '1'; this.paperType = 'blank'; this.paperColor = '#FFFFFF'
    },
    htmlToPlainText(html) {
      if (!html) return ''
      // 用 DOMParser 替代 innerHTML，避免 XSS（不执行 script）
      const doc = new DOMParser().parseFromString(html, 'text/html')
      doc.querySelectorAll('br').forEach(br => br.replaceWith('\n'))
      doc.querySelectorAll('p').forEach(el => {
        el.insertAdjacentText('afterend', '\n\n')
      })
      doc.querySelectorAll('div, li').forEach(el => {
        el.insertAdjacentText('afterend', '\n')
      })
      let text = doc.body?.textContent || ''
      text = text.replace(/\n{3,}/g, '\n\n')
      return text.trim()
    },
    extractAlignmentFromHtml(html) {
      if (!html) return 'default'
      // 用 DOMParser 替代 innerHTML，避免 XSS
      const doc = new DOMParser().parseFromString(html, 'text/html')
      const firstP = doc.querySelector('p')
      if (!firstP) return 'default'
      const style = firstP.getAttribute('style') || ''
      const alignMatch = style.match(/text-align:\s*(left|center|right|justify)/)
      if (alignMatch) {
        const align = alignMatch[1]
        if (align === 'center') return 'center'
        if (align === 'right') return 'right'
      }
      return 'default'
    },
    async generateHandwriting(preview = false, pdf_save = false) {
      if (this.isGenerating) { Swal.fire({ icon: 'warning', title: '生成中...', showConfirmButton: false, timer: 1500 }); return }
      const currentTime = Date.now()
      if (currentTime - this.lastGenerateTime < this.generateCooldown) {
        const remainingTime = Math.ceil((this.generateCooldown - (currentTime - this.lastGenerateTime)) / 1000)
        Swal.fire({ icon: 'warning', title: `请等待 ${remainingTime}s`, showConfirmButton: false, timer: 1500 }); return
      }
      this.isGenerating = true; this.lastGenerateTime = currentTime
      try {
        const formData = new FormData()
        formData.append('text', this.htmlToPlainText(this.text)); if (this.fontFile) formData.append('font_file', this.fontFile)
        if (this.backgroundImage) formData.append('background_image', this.backgroundImage)
        formData.append('font_size', String(this.fontSize)); formData.append('line_spacing', String(this.lineSpacing))
        formData.append('fill', this.fill); if (this.width) formData.append('width', String(this.width))
        if (this.height) formData.append('height', String(this.height))
        formData.append('top_margin', String(this.marginTop)); formData.append('bottom_margin', String(this.marginBottom))
        formData.append('left_margin', String(this.marginLeft)); formData.append('right_margin', String(this.marginRight))
        formData.append('line_spacing_sigma', String(this.lineSpacingSigma))
        formData.append('font_size_sigma', String(this.fontSizeSigma))
        formData.append('word_spacing_sigma', String(this.wordSpacingSigma))
        formData.append('end_chars', this.endChars); formData.append('perturb_x_sigma', String(this.perturbXSigma))
        formData.append('perturb_y_sigma', String(this.perturbYSigma))
        formData.append('perturb_theta_sigma', String(this.perturbThetaSigma))
        formData.append('word_spacing', String(this.wordSpacing)); formData.append('preview', String(preview))
        if (this.options[this.selectedOption - 1]) formData.append('font_option', this.options[this.selectedOption - 1].text)
        formData.append('strikethrough_length_sigma', String(this.strikethrough_length_sigma))
        formData.append('strikethrough_angle_sigma', String(this.strikethrough_angle_sigma))
        formData.append('strikethrough_width_sigma', String(this.strikethrough_width_sigma))
        formData.append('strikethrough_probability', String(this.strikethrough_probability))
        formData.append('strikethrough_width', String(this.strikethrough_width))
        formData.append('ink_depth_sigma', String(this.ink_depth_sigma))
        formData.append('pdf_save', String(pdf_save)); formData.append('isUnderlined', String(this.isUnderlined))
        formData.append('enableEnglishSpacing', String(this.enableEnglishSpacing))
        formData.append('paper_type', this.paperType); formData.append('paper_color', this.paperColor)
        formData.append('paragraph_layout', this.extractAlignmentFromHtml(this.text))
        formData.append('first_line_indent', String(this.firstLineIndent))
        formData.append('paragraph_spacing', String(this.paragraphSpacing))
        formData.append('full_preview', 'false')
        const taskCreateResponse = await http.post('/api/generate_handwriting', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }, withCredentials: true
        })
        const taskId = taskCreateResponse.data?.task_id; if (!taskId) throw new Error('未获取到任务ID')
        this.uploadMessage = `任务已提交（Task ID: ${taskId}）…`
        try { await this.waitForTaskViaWebSocket(taskId) }
        catch (wsError) { await this.pollGenerationTask(taskId) }
        const resultResponse = await http.get(`/api/generate_handwriting/task/${taskId}/result`, {
          responseType: 'blob', withCredentials: true
        })
        this.handleGenerationResultResponse(resultResponse, preview)
      } catch (error) {
        if (error.response?.status === 503 && error.response?.data?.status === 'queue_full') {
          this.startQueueFullCountdown(error.response.data.estimated_wait_seconds || 30)
        } else { this.errorMessage = error.message || '生成失败' }
      } finally { this.isGenerating = false }
    },
    async waitForTaskViaWebSocket(taskId, timeoutMs = 5 * 60 * 1000) {
      return new Promise((resolve, reject) => {
        let isSettled = false
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
        const socket = new WebSocket(`${protocol}://${window.location.host}/api/generate_handwriting/ws/${taskId}`)
        const timeoutId = setTimeout(() => { if (isSettled) return; isSettled = true; socket.close(); reject(new Error('WebSocket超时')) }, timeoutMs)
        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data?.status === 'error') { if (isSettled) return; isSettled = true; clearTimeout(timeoutId); socket.close(); reject(new Error(data?.message)); return }
            this.updateTaskUploadMessage(data, taskId)
            if (data?.task_status === 'completed') { if (isSettled) return; isSettled = true; clearTimeout(timeoutId); socket.close(); resolve() }
            else if (data?.task_status === 'failed') { if (isSettled) return; isSettled = true; clearTimeout(timeoutId); socket.close(); reject(new Error(data?.error_message || '任务失败')) }
          } catch (e) { console.error('[HomeView] WebSocket 消息解析失败:', e, 'raw=', event.data) }
        }
        socket.onerror = () => { if (isSettled) return; isSettled = true; clearTimeout(timeoutId); reject(new Error('WebSocket连接失败')) }
        socket.onclose = () => { if (isSettled) return; isSettled = true; clearTimeout(timeoutId); reject(new Error('WebSocket已关闭')) }
      })
    },
    async pollGenerationTask(taskId, timeoutMs = 5 * 60 * 1000, intervalMs = 1500) {
      const start = Date.now()
      while (Date.now() - start < timeoutMs) {
        const statusResponse = await http.get(`/api/generate_handwriting/task/${taskId}`)
        const taskStatus = statusResponse.data?.task_status
        this.updateTaskUploadMessage(statusResponse.data, taskId)
        if (taskStatus === 'completed') return
        if (taskStatus === 'failed') throw new Error(statusResponse.data?.error_message || '任务失败')
        await new Promise(resolve => setTimeout(resolve, intervalMs))
      }
      throw new Error('任务超时')
    },
    updateTaskUploadMessage(taskData, taskId) {
      const taskMessage = taskData?.task_message || '任务处理中'
      const taskProgress = taskData?.task_progress
      const queueAheadCount = taskData?.queue_ahead_count
      if (typeof queueAheadCount === 'number') this.uploadMessage = `${taskMessage}（前方排队 ${queueAheadCount} 人） Task ID: ${taskId}`
      else if (typeof taskProgress === 'number') this.uploadMessage = `${taskMessage}（${taskProgress}%） Task ID: ${taskId}`
      else this.uploadMessage = `${taskMessage} Task ID: ${taskId}`
    },
    handleGenerationResultResponse(response, preview) {
      const contentType = response.headers['content-type'] || ''
      if (contentType.includes('image/png')) {
        const blobUrl = URL.createObjectURL(response.data); this.previewImage = blobUrl; this.previewImages = [blobUrl]
        this.message = '预览已加载'; this.uploadMessage = ''; this.errorMessage = ''
      } else if (contentType.includes('application/zip')) {
        const url = window.URL.createObjectURL(response.data)
        const link = document.createElement('a'); link.href = url; link.setAttribute('download', 'images.zip')
        document.body.appendChild(link); link.click(); document.body.removeChild(link)
        this.message = '文件已下载'; this.uploadMessage = ''; this.errorMessage = ''
      } else if (contentType.includes('application/pdf')) {
        const url = window.URL.createObjectURL(response.data)
        const link = document.createElement('a'); link.href = url; link.setAttribute('download', 'handwriting.pdf')
        document.body.appendChild(link); link.click(); document.body.removeChild(link)
        this.message = '文件已下载'; this.uploadMessage = ''; this.errorMessage = ''
      }
    },
    startQueueFullCountdown(seconds) {
      if (this.queueFullTimer) clearInterval(this.queueFullTimer)
      this.queueFullTotal = seconds; this.queueFullCountdown = seconds
      this.queueFullTimer = setInterval(() => { this.queueFullCountdown -= 1; if (this.queueFullCountdown <= 0) { this.queueFullCountdown = 0; clearInterval(this.queueFullTimer); this.queueFullTimer = null } }, 1000)
    }
  }
}
</script>
