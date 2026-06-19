<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-black/30 backdrop-blur-md rounded-custom shadow-xl border border-white/10 p-6">
      <h2 class="text-2xl font-bold text-white mb-6 text-center font-headline">注册</h2>
      <form @submit.prevent="handleRegister">
        <div class="mb-4">
          <label class="block text-sm text-gray-200 mb-2">用户名</label>
          <input v-model="username" type="text" placeholder="请输入用户名" required
            class="w-full bg-black/30 border border-white/20 rounded-custom px-4 py-2 text-white focus:ring-[#CFE3E8] focus:border-[#CFE3E8]">
        </div>
        <div class="mb-4">
          <label class="block text-sm text-gray-200 mb-2">密码</label>
          <input v-model="password" type="password" placeholder="请输入密码" required
            class="w-full bg-black/30 border border-white/20 rounded-custom px-4 py-2 text-white focus:ring-[#CFE3E8] focus:border-[#CFE3E8]">
        </div>
        <div class="mb-6">
          <label class="block text-sm text-gray-200 mb-2">确认密码</label>
          <input v-model="confirmPassword" type="password" placeholder="请再次输入密码" required
            class="w-full bg-black/30 border border-white/20 rounded-custom px-4 py-2 text-white focus:ring-[#CFE3E8] focus:border-[#CFE3E8]">
        </div>
        <button type="submit" :disabled="isLoading" class="btn-primary w-full py-3 disabled:opacity-50 disabled:cursor-not-allowed">
          {{ isLoading ? '注册中...' : '注册' }}
        </button>
      </form>
      <div class="mt-4 text-center text-sm text-gray-300">
        已有账号？<router-link to="/Login" class="text-[#CFE3E8] hover:underline">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import http from '../utils/http'
import Swal from 'sweetalert2'

export default {
  name: 'UserRegister',
  data() { return { username: '', password: '', confirmPassword: '', isLoading: false } },
  methods: {
    async handleRegister() {
      if (!this.username || !this.password || !this.confirmPassword) { Swal.fire({ icon: 'warning', title: '请填写所有字段' }); return }
      if (this.password !== this.confirmPassword) { Swal.fire({ icon: 'error', title: '注册失败', text: '两次输入的密码不一致' }); return }
      if (this.password.length < 6) { Swal.fire({ icon: 'error', title: '注册失败', text: '密码长度不能少于6位' }); return }
      this.isLoading = true
      try {
        const response = await http.post('/api/register', { username: this.username, password: this.password })
        if (response.data.success) {
          Swal.fire({ icon: 'success', title: '注册成功', timer: 1500, showConfirmButton: false })
          this.$router.push('/Login')
        } else { Swal.fire({ icon: 'error', title: '注册失败', text: response.data.message }) }
      } catch (error) { Swal.fire({ icon: 'error', title: '注册失败', text: error.response?.data?.message || '网络错误' }) }
      finally { this.isLoading = false }
    }
  }
}
</script>
