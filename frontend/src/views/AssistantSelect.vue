<template>
  <div class="assistant-select-page">
    <header class="header"><h2>请选择一个助手</h2></header>

    <div class="assistant-list">
      <div v-if="loading">加载中，请稍候...</div>
      <div v-else-if="assistants.length === 0">暂无助手</div>
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
</script>
