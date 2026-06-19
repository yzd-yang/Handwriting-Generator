<template>
  <div class="min-h-screen p-8">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold text-white mb-8 font-headline">用户反馈</h1>
      <div class="bg-black/30 backdrop-blur-md rounded-custom shadow-xl border border-white/10 p-6">
        <form @submit.prevent="handleSubmit">
          <div class="mb-4">
            <label class="block text-sm text-gray-200 mb-2">邮箱（可选）</label>
            <input v-model="email" type="email" placeholder="请输入您的邮箱"
              class="w-full bg-black/30 border border-white/20 rounded-custom px-4 py-2 text-white focus:ring-[#CFE3E8] focus:border-[#CFE3E8]">
          </div>
          <div class="mb-4">
            <label class="block text-sm text-gray-200 mb-2">反馈内容</label>
            <textarea v-model="feedback" rows="6" placeholder="请输入您的反馈内容" required
              class="w-full bg-black/30 border border-white/20 rounded-custom px-4 py-2 text-white focus:ring-[#CFE3E8] focus:border-[#CFE3E8] resize-none"></textarea>
          </div>
          <button type="submit" :disabled="isLoading" class="btn-primary w-full py-3 disabled:opacity-50 disabled:cursor-not-allowed">
            {{ isLoading ? '提交中...' : '提交反馈' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import http from '../utils/http'
import Swal from 'sweetalert2'

export default {
  name: 'UserFeedback',
  data() { return { email: '', feedback: '', isLoading: false } },
  methods: {
    async handleSubmit() {
      if (!this.feedback) { Swal.fire({ icon: 'warning', title: '请填写反馈内容' }); return }
      this.isLoading = true
      try {
        const response = await http.post('/api/feedback', { email: this.email, feedback: this.feedback })
        if (response.data.success) {
          Swal.fire({ icon: 'success', title: '反馈提交成功', timer: 1500, showConfirmButton: false })
          this.email = ''; this.feedback = ''
        } else { Swal.fire({ icon: 'error', title: '提交失败', text: response.data.message }) }
      } catch (error) { Swal.fire({ icon: 'error', title: '提交失败', text: error.response?.data?.message || '网络错误' }) }
      finally { this.isLoading = false }
    }
  }
}
</script>
