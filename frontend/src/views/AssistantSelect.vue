<template>
  <div class="app-container assistant-select-page">
    <header class="header">
      <el-button type="text" @click="back" size="small" class="back-btn">返回登录</el-button>
      <h2 class="title">请选择一个助手</h2>
    </header>

    <div class="assistant-list">
      <div v-if="loading" class="loading">加载中，请稍候...</div>
      <div v-else-if="assistants.length === 0" class="loading">暂无助手</div>
      <div v-else class="cards">
        <div
          v-for="assistant in assistants"
          :key="assistant.id"
          class="assistant-card"
          @click="selectAssistant(assistant.id)"
        >
          <img :src="assistant.icon" alt="icon" class="icon" />
          <h3>{{ assistant.name }}</h3>
          <p>{{ assistant.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAssistants } from '../api'

interface Assistant { id: number; name: string; icon: string; description: string }

const router = useRouter()
const assistants = ref<Assistant[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getAssistants()
    assistants.value = res.data
  } catch (e) {
    console.error('获取助手列表失败', e)
  } finally {
    loading.value = false
  }
})

function selectAssistant(id: number) {
  router.push(`/chat/${id}`)
}

function back() {
  router.push('/login')
}
</script>

<style scoped>
.assistant-select-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100vh;
  background: #f0f0f0;

  /* 模拟手机竖屏宽度 */
  max-width: 400px;
  margin: 0 auto;
  border-left: 1px solid #ccc;
  border-right: 1px solid #ccc;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

/* 头部 */
.header {
  width: 100%;
  padding: 10px;
  position: relative;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
  text-align: center;
}

.header .title {
  margin: 0;
  font-size: 18px;
}

/* 返回按钮放在左上角，不遮挡标题 */
.back-btn {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
}

/* 助手列表 */
.assistant-list {
  flex: 1;
  width: 100%;
  padding: 10px;
  overflow-y: auto;
}

/* 卡片容器 */
.cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 助手卡片 */
.assistant-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.assistant-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

.assistant-card .icon {
  width: 60px;
  height: 60px;
  object-fit: cover;
  margin-bottom: 10px;
  border-radius: 50%;
}

.assistant-card h3 {
  margin: 5px 0;
  font-size: 16px;
  text-align: center;
}

.assistant-card p {
  font-size: 14px;
  color: #666;
  text-align: center;
  margin: 0;
}

/* 加载或暂无助手 */
.loading {
  text-align: center;
  margin-top: 20px;
  color: #999;
}

/* 响应式 */
@media (max-width: 500px) {
  .assistant-select-page {
    max-width: 100%;
    border-left: none;
    border-right: none;
    box-shadow: none;
  }
}
</style>
