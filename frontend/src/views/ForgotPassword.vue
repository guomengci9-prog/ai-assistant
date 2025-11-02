<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2 class="title">忘记密码</h2>

      <!-- 邮箱/手机号输入 + 发送验证码按钮 -->
      <el-input
        :key="'account-' + $route.fullPath"
        v-model="account"
        placeholder="邮箱或手机号"
        class="input"
        autocomplete="off"
      >
        <template #append>
          <el-button
            type="primary"
            :disabled="timerCount > 0 || !account"
            @click="sendCode"
          >
            {{ timerCount > 0 ? `${timerCount}s` : '发送验证码' }}
          </el-button>
        </template>
      </el-input>

      <!-- 验证码输入 -->
      <el-input
        v-model="code"
        placeholder="输入验证码"
        class="input"
        autocomplete="off"
      />

      <!-- 新密码输入 -->
      <el-input
        v-model="newPassword"
        type="password"
        placeholder="新密码（6-18位，字母+数字）"
        class="input"
        autocomplete="new-password"
      />

      <!-- 再次输入新密码 -->
      <el-input
        v-model="confirmPassword"
        type="password"
        placeholder="再次输入新密码"
        class="input"
        autocomplete="new-password"
      />

      <!-- 重置密码按钮 -->
      <el-button
        type="primary"
        @click="resetHandler"
        class="btn primary-btn"
      >
        重置密码
      </el-button>

      <p class="switch-link" @click="goLogin">返回登录</p>

      <p v-if="error" class="error-msg">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { forgotPassword, resetPassword } from '../api'

const router = useRouter()

// ------------------ 变量 ------------------
const account = ref<string>('')
const code = ref<string>('')
const newPassword = ref<string>('')
const confirmPassword = ref<string>('')
const error = ref<string>('')
const timerCount = ref<number>(0)
let timer: number | undefined

// 密码正则：6-18位，包含字母和数字
const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,18}$/

// ------------------ 发送验证码 ------------------
const sendCode = async () => {
  if (!account.value.trim()) {
    error.value = '请输入邮箱或手机号'
    return
  }

  try {
    const res = await forgotPassword({ account: account.value })
    if (res.data.success) {
      error.value = '验证码已发送'
      timerCount.value = 60
      timer = window.setInterval(() => {
        timerCount.value--
        if (timerCount.value <= 0 && timer) {
          clearInterval(timer)
          timer = undefined
        }
      }, 1000)
    } else {
      error.value = res.data.message
    }
  } catch {
    error.value = '发送验证码失败，请稍后重试'
  }
}

// ------------------ 重置密码 ------------------
const resetHandler = async () => {
  if (!code.value.trim()) {
    error.value = '请输入验证码'
    return
  }
  if (!passwordRegex.test(newPassword.value)) {
    error.value = '密码必须6-18位，包含字母和数字'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }

  try {
    const res = await resetPassword({
      account: account.value,
      code: code.value,
      new_password: newPassword.value
    })
    if (res.data.success) {
      error.value = '✅ 密码重置成功，正在跳转登录'
      setTimeout(() => router.push('/login'), 800)
    } else {
      error.value = res.data.message
    }
  } catch {
    error.value = '重置失败，请稍后再试'
  }
}

// ------------------ 跳转登录 ------------------
const goLogin = () => router.push('/login')
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
