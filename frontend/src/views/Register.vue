<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2 class="title">注册</h2>

      <el-input
        v-model="username"
        placeholder="用户名"
        autocomplete="off"
        class="input"
      />

      <el-input
        v-model="password"
        type="password"
        placeholder="密码（6-18位，字母+数字）"
        autocomplete="new-password"
        class="input"
      />

      <el-input
        v-model="email"
        placeholder="邮箱（可选）"
        autocomplete="off"
        class="input"
      />

      <el-input
        v-model="phone"
        placeholder="手机号（可选）"
        autocomplete="off"
        class="input"
      />

      <el-button type="primary" @click="registerHandler" class="btn primary-btn">
        注册
      </el-button>

      <p class="switch-link" @click="goLogin">已有账号？去登录</p>

      <p v-if="error" class="error-msg">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { register, RegisterData } from '../api'

const router = useRouter()
const username = ref('')
const password = ref('')
const email = ref('')
const phone = ref('')
const error = ref('')

onMounted(() => {
  username.value = ''
  password.value = ''
  email.value = ''
  phone.value = ''
  error.value = ''
})

// 密码正则：6-18位，包含字母和数字
const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,18}$/

// 邮箱正则
const emailRegex = /^[\w.-]+@[\w.-]+\.\w{2,}$/

// 手机正则（简单匹配 11 位数字）
const phoneRegex = /^\d{11}$/

async function registerHandler() {
  if (!username.value.trim()) {
    error.value = '用户名不能为空'
    return
  }
  if (!passwordRegex.test(password.value)) {
    error.value = '密码必须6-18位，包含字母和数字'
    return
  }
  if (email.value && !emailRegex.test(email.value)) {
    error.value = '邮箱格式不正确'
    return
  }
  if (phone.value && !phoneRegex.test(phone.value)) {
    error.value = '手机号格式不正确'
    return
  }

  try {
    const data: RegisterData = {
      username: username.value,
      password: password.value,
      email: email.value || undefined,
      phone: phone.value || undefined
    }

    const res = await register(data)
    if (res.data.success) {
      error.value = '✅ 注册成功，正在跳转...'
      setTimeout(() => router.push('/login'), 800)
    } else {
      error.value = res.data.message
    }
  } catch {
    error.value = '注册失败，请稍后再试'
  }
}

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
