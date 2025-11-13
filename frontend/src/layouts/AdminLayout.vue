<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="logo">
        <span>AI 后台</span>
      </div>
      <nav class="menu">
        <RouterLink
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="menu-item"
          :class="{ active: route.path.startsWith(item.path) }"
        >
          <el-icon :size="16"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-footer">
        <el-button text @click="goToApp">
          返回用户端
        </el-button>
        <el-button text type="danger" @click="logout">
          退出登录
        </el-button>
      </div>
    </aside>

    <main class="content">
      <header class="content-header">
        <h1>{{ currentTitle }}</h1>
        <p>管理助手、知识库与其他后台资源</p>
      </header>
      <section class="content-body">
        <RouterView />
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter, RouterLink, RouterView } from 'vue-router'
import { Collection, Document, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const menuItems = [
  { path: '/admin/assistants', label: '助手管理', icon: Collection },
  { path: '/admin/docs', label: '知识库管理', icon: Document },
  { path: '/admin/users', label: '用户管理', icon: User },
]

const currentTitle = computed(() => {
  const match = menuItems.find(item => route.path.startsWith(item.path))
  return match ? match.label : '后台管理'
})

function goToApp() {
  router.push('/assistants')
}

function logout() {
  authStore.clearAuth({ keepAccount: true })
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  display: flex;
  background: #f5f6fa;
}

.sidebar {
  width: 220px;
  background: #0f172a;
  color: #fff;
  display: flex;
  flex-direction: column;
  padding: 24px 16px;
  box-sizing: border-box;
}

.logo {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 24px;
}

.menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: #d1d5db;
  text-decoration: none;
  transition: background 0.2s;
}

.menu-item.active,
.menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.content {
  flex: 1;
  padding: 24px;
}

.content-header h1 {
  margin: 0;
  font-size: 24px;
  color: #111827;
}

.content-header p {
  margin: 6px 0 0;
  color: #6b7280;
}

.content-body {
  margin-top: 18px;
}

@media (max-width: 900px) {
  .sidebar {
    width: 180px;
  }
}
</style>
