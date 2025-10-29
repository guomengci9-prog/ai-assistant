<template>
  <div class="login-page">
    <h2>登录</h2>
    <el-input v-model="username" placeholder="用户名" />
    <el-input v-model="password" type="password" placeholder="密码" />
    <el-button type="primary" @click="loginHandler">登录</el-button>
    <el-button @click="registerHandler">注册</el-button>
    <p v-if="error" style="color:red">{{ error }}</p>
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
