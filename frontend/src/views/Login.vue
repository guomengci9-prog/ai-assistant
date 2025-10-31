<template>
  <div class="login-page">
    <div class="login-card">
      <h2>登录</h2>
      <el-input v-model="username" placeholder="用户名" />
      <el-input v-model="password" type="password" placeholder="密码" />
      <el-button type="primary" @click="loginHandler" class="btn">登录</el-button>
      <el-button @click="registerHandler" class="btn">注册</el-button>
      <p v-if="error" class="error-msg">{{ error }}</p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, register } from '../api'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')

async function loginHandler() {
  try {
    const res = await login(username.value, password.value)
    if (res.data.success) {
      router.push('/assistants')
    } else {
      error.value = res.data.message
    }
  } catch (e) {
    error.value = '登录失败，请稍后重试'
  }
}

async function registerHandler() {
  try {
    const res = await register(username.value, password.value)
    if (res.data.success) {
      error.value = '注册成功，请登录'
    } else {
      error.value = res.data.message
    }
  } catch (e) {
    error.value = '注册失败'
  }
}
</script>

<style scoped>
/* 整体页面居中 */
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f0f0f0;
}

/* 登录卡片 */
.login-card {
  width: 100%;
  max-width: 360px; /* 模拟手机宽度 */
  padding: 30px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

/* 标题居中 */
.login-card h2 {
  text-align: center;
  margin-bottom: 20px;
}

/* 输入框间距 */
.login-card .el-input {
  margin-bottom: 15px;
}

/* 按钮样式 */
.login-card .btn {
  margin-bottom: 10px;
}

/* 错误提示 */
.error-msg {
  color: red;
  text-align: center;
  margin-top: 10px;
}

/* 响应式调整，小屏幕撑满 */
@media (max-width: 400px) {
  .login-card {
    max-width: 100%;
    border-radius: 0;
    box-shadow: none;
    padding: 20px 10px;
  }
}
</style>
