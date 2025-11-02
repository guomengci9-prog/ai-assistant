<template>
  <div class="app-container assistant-select-page">
    <header class="header">
      <button class="back-circle-btn" @click="back">
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <h2 class="title">请选择一个助手</h2>
    </header>

    <!-- 搜索框 -->
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
          <p>{{ assistant.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getAssistants } from '../api'
import { ArrowLeft, Search } from '@element-plus/icons-vue'

interface Assistant { id: number; name: string; icon: string; description: string }

const router = useRouter()
const assistants = ref<Assistant[]>([])
const loading = ref(true)
const searchKeyword = ref('')

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

const filteredAssistants = computed(() => {
  if (!searchKeyword.value) return assistants.value
  return assistants.value.filter(a =>
    a.name.includes(searchKeyword.value) || a.description.includes(searchKeyword.value)
  )
})

function selectAssistant(id: number) {
  router.push(`/chat/${id}`)
}

function back() {
  router.push('/login')
}
</script>

<style scoped>
/* 主容器 */
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

/* 头部 */
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

/* 圆形返回按钮，保持和聊天页面一致 */
.back-circle-btn {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #f2f2f2;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: .2s;
}

.back-circle-btn:hover {
  background: #e8e8e8;
  transform: translateY(-50%) scale(1.05);
}

.back-circle-btn:active {
  transform: translateY(-50%) scale(0.95);
}

/* 搜索框 */
.search-wrapper {
  display: flex;
  justify-content: center;
  margin: 12px 0;
}

.search-box {
  width: 70%;
  max-width: 320px;
}

/* 列表滚动区域 */
.assistant-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  justify-content: center;
}

/* 网格布局居中 */
.cards {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  justify-content: center;
}

/* 助手卡片：圆角正方形 */
.assistant-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 165px;
  height: 165px;
  background: #f7f7f7;
  border-radius: 14px;
  cursor: pointer;
  transition: .18s;
  padding: 10px;
  text-align: center;
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

.assistant-card p {
  font-size: 12.5px;
  color: #666;
  line-height: 1.25;
  margin: 0;
}

/* 加载提示 */
.loading {
  text-align: center;
  margin-top: 20px;
  color: #999;
}

/* 移动端适配 */
@media (max-width: 800px) {
  .app-container.assistant-select-page {
    width: 95%;
    height: 95%;
  }
  .assistant-card {
    width: 44%;
    height: 140px;
  }
}
</style>
