<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2 class="title">登录</h2>

      <div class="input-with-action">
        <el-input
          :key="'account-' + $route.fullPath"
          v-model="account"
          placeholder="用户名/邮箱/手机号"
          autocomplete="off"
          class="input"
        />
        <el-button
          v-if="hasLastAccount"
          text
          class="clear-account-btn"
          @click="clearAccount"
        >
          切换账号
        </el-button>
      </div>

      <el-input
        :key="'password-' + $route.fullPath"
        v-model="password"
        type="password"
        placeholder="密码"
        autocomplete="new-password"
        class="input"
      />

      <el-button type="primary" @click="loginHandler" class="btn primary-btn">登录</el-button>

      <div class="link-group">
        <span @click="goRegister">没有账号？去注册</span>
        <span @click="goForgotPassword">忘记密码</span>
      </div>

      <p v-if="error" class="error-msg">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, type LoginData } from '../api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const account = ref(authStore.account || '')
const password = ref('')
const error = ref('')

const isLoggedIn = computed(() => authStore.isLoggedIn)
const hasLastAccount = computed(() => Boolean(authStore.account))

onMounted(() => {
  if (isLoggedIn.value) {
    router.replace('/assistants')
  }
})

async function loginHandler() {
  if (!account.value.trim() || !password.value) {
    error.value = '请输入账号和密码'
    return
  }
  try {
    const data: LoginData = { account: account.value.trim(), password: password.value }
    const res = await login(data)
    if (res.data.success) {
      authStore.setAuth({
        token: res.data.token || '',
        account: account.value.trim(),
        role: res.data.role || 'user',
      })
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

function clearAccount() {
  authStore.clearAuth({ keepAccount: false })
  account.value = ''
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f6fa;
  padding: 16px;
}

.auth-card {
  width: 100%;
  max-width: 320px;
  padding: 24px 18px;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
}

.title {
  text-align: center;
  margin-bottom: 18px;
  font-weight: 600;
  font-size: 20px;
}

.input {
  margin-bottom: 12px;
}

.input-with-action {
  position: relative;
}

.clear-account-btn {
  position: absolute;
  right: 4px;
  top: 12px;
  padding: 0 6px;
  font-size: 12px;
  color: #409eff;
}

.btn {
  width: 100%;
  margin-top: 4px;
  padding: 12px;
  font-size: 15px;
  border-radius: 10px;
}

.link-group {
  display: flex;
  justify-content: space-between;
  margin-top: 14px;
  font-size: 13px;
  color: #409eff;
  cursor: pointer;
}

.link-group span:hover {
  text-decoration: underline;
}

.error-msg {
  color: #ff4d4f;
  text-align: center;
  margin-top: 10px;
  font-size: 13px;
}
</style>
