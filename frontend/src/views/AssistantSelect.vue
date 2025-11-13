<template>
  <div class="app-container assistant-select-page">
    <header class="header">
      <button class="avatar-btn" @click="toggleProfile">
        <img src="https://api.dicebear.com/7.x/initials/svg?seed=AI" alt="avatar" />
      </button>
      <h2 class="title">请选择一个助手</h2>
    </header>

    <div class="search-wrapper">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索助手..."
        size="small"
        clearable
        class="search-box"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div class="assistant-list">
      <div v-if="loading" class="loading">加载中，请稍候...</div>
      <div v-else-if="filteredAssistants.length === 0" class="loading">暂无助手</div>
      <div v-else class="cards">
        <div
          v-for="assistant in filteredAssistants"
          :key="assistant.id"
          class="assistant-card"
          @click="selectAssistant(assistant.id)"
        >
          <img :src="assistant.icon" alt="icon" class="icon" />
          <h3>{{ assistant.name }}</h3>
          <p class="desc">{{ assistant.description }}</p>
        </div>
      </div>
    </div>

    <el-drawer
      v-model="drawerVisible"
      :title="selectedAssistant?.name"
      size="40%"
      destroy-on-close
    >
      <template #default>
        <div v-if="selectedAssistant">
          <el-descriptions border :column="1" class="assistant-descriptions">
            <el-descriptions-item label="简介">
              {{ selectedAssistant.description || '暂无简介' }}
            </el-descriptions-item>
            <el-descriptions-item label="系统提示词">
              <pre class="prompt-block">{{ selectedAssistant.system_prompt || '未设置' }}</pre>
            </el-descriptions-item>
            <el-descriptions-item label="场景提示词">
              <pre class="prompt-block">{{ selectedAssistant.scene_prompt || '未设置' }}</pre>
            </el-descriptions-item>
            <el-descriptions-item label="用户预输入">
              <pre class="prompt-block">{{ selectedAssistant.user_prefill || '未设置' }}</pre>
            </el-descriptions-item>
            <el-descriptions-item label="开场白">
              <pre class="prompt-block">{{ selectedAssistant.opening_message || '未设置' }}</pre>
            </el-descriptions-item>
            <el-descriptions-item label="默认提示词">
              <pre class="prompt-block">{{ defaultPromptText }}</pre>
            </el-descriptions-item>
          </el-descriptions>
</div>
      </template>
    </el-drawer>
    <el-drawer
      v-model="profileDrawer"
      title="账户中心"
      direction="ltr"
      size="280px"
      destroy-on-close
    >
      <div class="profile-panel">
        <div class="profile-header">
          <img src="https://api.dicebear.com/7.x/initials/svg?seed=AI" alt="avatar" />
          <div>
            <div class="profile-name">{{ authStore.account || '未登录' }}</div>
            <div class="profile-desc">AI 多助手平台</div>
          </div>
        </div>
        <el-divider />
        <el-button
          v-if="authStore.isAdmin"
          type="success"
          block
          @click="goAdmin"
        >
          进入后台
        </el-button>
        <el-divider v-if="authStore.isAdmin" />
        <el-button type="primary" plain block @click="goLogin">退出登录</el-button>
        <el-button block @click="switchAccount">切换账号</el-button>
        <el-divider />
        <div class="profile-links">
          <p>帮助中心（待上线）</p>
          <p>关于我们</p>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'

import { getAssistants } from '../api'
import { useAuthStore } from '@/stores/auth'
import type { Assistant } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const assistants = ref<Assistant[]>([])
const loading = ref(true)
const searchKeyword = ref('')

const drawerVisible = ref(false)
const selectedAssistant = ref<Assistant | null>(null)
const profileDrawer = ref(false)

onMounted(async () => {
  try {
    const res = await getAssistants()
    assistants.value = res.data
  } catch (err) {
    console.error('获取助手列表失败', err)
  } finally {
    loading.value = false
  }
})

const filteredAssistants = computed(() => {
  if (!searchKeyword.value) return assistants.value
  const key = searchKeyword.value.toLowerCase()
  return assistants.value.filter(a =>
    (a.name || '').toLowerCase().includes(key) ||
    (a.description || '').toLowerCase().includes(key)
  )
})

const defaultPromptText = computed(() => {
  if (!selectedAssistant.value) return '未设置'
  return (
    selectedAssistant.value.prompt_content ||
    selectedAssistant.value.defaultPrompt ||
    '未设置'
  )
})

function selectAssistant(id: number) {
  router.push(`/chat/${id}`)
}

function goLogin() {
  authStore.clearAuth({ keepAccount: true })
  router.push('/login')
}

function switchAccount() {
  authStore.clearAuth({ keepAccount: false })
  router.push('/login')
}

function toggleProfile() {
  profileDrawer.value = !profileDrawer.value
}

function goAdmin() {
  profileDrawer.value = false
  router.push('/admin')
}

function openDetail(assistant: Assistant) {
  selectedAssistant.value = { ...assistant }
  drawerVisible.value = true
}
</script>

<style scoped>
.app-container.assistant-select-page {
  width: 700px;
  max-width: 90%;
  height: 560px;
  border-radius: 10px;
  box-shadow: 0 0 15px rgba(0,0,0,0.1);
  background: #fff;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  padding: 12px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.header {
  width: 100%;
  padding: 8px 10px;
  position: relative;
  border-bottom: 1px solid #ddd;
  text-align: center;
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.avatar-btn {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: .2s;
  padding: 0;
}

.avatar-btn img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.avatar-btn:hover {
  transform: translateY(-50%) scale(1.05);
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.search-wrapper {
  display: flex;
  justify-content: center;
  margin: 12px 0;
}

.search-box {
  width: 70%;
  max-width: 320px;
}

.assistant-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  justify-content: center;
}

.cards {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  justify-content: center;
}

.assistant-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 200px;
  height: 190px;
  background: #f7f7f7;
  border-radius: 14px;
  cursor: pointer;
  transition: .18s;
  padding: 12px;
  text-align: center;
  position: relative;
}

.assistant-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 14px rgba(0,0,0,0.15);
}

.icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 8px;
}

.assistant-card h3 {
  margin: 4px 0;
  font-size: 15px;
  font-weight: bold;
}

.assistant-card .desc {
  font-size: 12.5px;
  color: #666;
  line-height: 1.3;
  margin: 4px 0 8px;
}

.tag {
  margin-bottom: 6px;
}

.detail-btn {
  margin-top: auto;
}

.loading {
  text-align: center;
  margin-top: 20px;
  color: #999;
}

.assistant-descriptions {
  margin-bottom: 16px;
}

.prompt-block {
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.4;
  margin: 0;
}

@media (max-width: 800px) {
  .app-container.assistant-select-page {
    width: 95%;
    height: 95%;
  }
  .assistant-card {
    width: 46%;
    height: 200px;
  }
}

.profile-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-header {
  display: flex;
  gap: 12px;
  align-items: center;
}

.profile-header img {
  width: 60px;
  height: 60px;
  border-radius: 50%;
}

.profile-name {
  font-weight: 600;
}

.profile-desc {
  font-size: 12px;
  color: #8992a9;
}

.profile-links {
  font-size: 13px;
  color: #8f96ab;
}
</style>
