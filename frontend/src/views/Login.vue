<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2 class="title">登录</h2>

      <el-input
        :key="'account-' + $route.fullPath"
        v-model="account"
        placeholder="用户名/邮箱/手机号"
        autocomplete="off"
        class="input"
      />

      <el-input
        :key="'password-' + $route.fullPath"
        v-model="password"
        type="password"
        placeholder="密码"
        autocomplete="new-password"
        class="input"
      />

      <el-button type="primary" @click="loginHandler" class="btn primary-btn">登录</el-button>

      <p class="switch-link" @click="goRegister">没有账号？去注册</p>
      <p class="switch-link" @click="goForgotPassword">忘记密码？</p>

      <p v-if="error" class="error-msg">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { login, LoginData } from '../api'

const router = useRouter()
const account = ref('')
const password = ref('')
const error = ref('')

onMounted(() => {
  account.value = ''
  password.value = ''
  error.value = ''
})

async function loginHandler() {
  try {
    const data: LoginData = { account: account.value, password: password.value }
    const res = await login(data)
    if (res.data.success) {
      router.push('/assistants')
    } else {
      error.value = res.data.message
    }
  } catch {
    error.value = '登录失败，请稍后重试'
  }
}

const goRegister = () => router.push('/register')
const goForgotPassword = () => router.push('/forgot-password')
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f5f6fa;
}
.auth-card {
  width: 100%;
  max-width: 360px;
  padding: 28px 22px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
}
.title {
  text-align: center;
  margin-bottom: 24px;
  font-weight: 600;
  font-size: 20px;
}
.input {
  margin-bottom: 14px;
}
.btn {
  width: 100%;
  margin-top: 4px;
  padding: 12px;
  font-size: 15px;
  border-radius: 10px;
  transition: .2s;
}
.primary-btn:hover {
  filter: brightness(0.95);
}
.switch-link {
  text-align: center;
  margin-top: 12px;
  color: #409eff;
  cursor: pointer;
  font-size: 14px;
}
.switch-link:hover {
  text-decoration: underline;
}
.error-msg {
  color: red;
  text-align: center;
  margin-top: 10px;
  font-size: 13px;
}
</style>
