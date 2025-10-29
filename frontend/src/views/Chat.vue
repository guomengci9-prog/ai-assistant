<template>
  <div class="chat-page">
    <header class="chat-header">
      <el-button @click="back">返回助手列表</el-button>
      <h3>{{ assistantName }}</h3>
    </header>

    <div class="chat-body" ref="chatBody">
      <div v-for="(msg, idx) in messages" :key="idx" :class="['chat-message', msg.role]">
        <div class="bubble">{{ msg.content }}</div>
      </div>

      <!-- 流式正在输出的消息 -->
      <div v-if="streamingReply" class="chat-message assistant">
        <div class="bubble">{{ streamingReply }}</div>
      </div>
    </div>

    <footer class="chat-footer">
      <el-input
        v-model="input"
        placeholder="输入消息..."
        @keyup.enter="send"
        clearable
      />
      <el-button type="primary" @click="send">发送</el-button>
    </footer>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import type { ChatRecord } from '../types'
import { getHistory, getAssistantById } from '../api'

interface Props { id: number }
const props = defineProps<Props>()
const assistantId = props.id

const router = useRouter()
const assistantName = ref('')
const messages = ref<ChatRecord[]>([])  // 必须是数组
const input = ref('')
const chatBody = ref<HTMLElement | null>(null)
const loading = ref(true)
const error = ref('')
const streamingReply = ref('')  // 临时流式文本

let ws: WebSocket | null = null

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    chatBody.value && (chatBody.value.scrollTop = chatBody.value.scrollHeight)
  })
}

// 连接 WebSocket
function connectWS() {
  ws = new WebSocket(`ws://127.0.0.1:8000/api/ws/chat/${assistantId}`)

  ws.onmessage = (event) => {
    const text = event.data

    if (text === "[END]") {
      // 流结束，保存到历史
      if (streamingReply.value) {
        messages.value.push({ role: "assistant", content: streamingReply.value })
        streamingReply.value = ""
      }
      scrollToBottom()
      return
    }

    streamingReply.value += text
    scrollToBottom()
  }

  ws.onclose = () => {
    console.warn("WebSocket closed, reconnecting...")
    setTimeout(connectWS, 1500)
  }
}

// 加载助手信息和历史聊天
async function loadChat() {
  loading.value = true
  try {
    const res = await getAssistantById(assistantId)
    assistantName.value = res.data.name

    const historyRes = await getHistory(assistantId)
    // 确保 messages.value 是数组
    messages.value = Array.isArray(historyRes.data) ? historyRes.data : []
    scrollToBottom()
  } catch (e) {
    console.error('加载聊天失败', e)
    error.value = '加载聊天失败，请刷新页面'
    messages.value = []  // 避免 undefined
  } finally {
    loading.value = false
  }
}

// 发送消息
function send() {
  if (!input.value.trim() || !ws) return

  const msg = input.value
  // push 安全
  if (Array.isArray(messages.value)) {
    messages.value.push({ role: 'user', content: msg })
  } else {
    messages.value = [{ role: 'user', content: msg }]
  }
  scrollToBottom()

  ws.send(JSON.stringify({ message: msg }))

  input.value = ''
}

// 返回助手选择页
function back() {
  router.push('/assistants')
}

// 生命周期
onMounted(() => {
  loadChat()
  connectWS()
})
onBeforeUnmount(() => ws?.close())
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: #eaeaea;
}

.chat-message {
  margin: 5px 0;
  display: flex;
}

.chat-message.user {
  justify-content: flex-end;
}

.chat-message.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 60%;
  padding: 10px;
  border-radius: 10px;
  background: #fff;
}

.chat-message.user .bubble {
  background: #1890ff;
  color: #fff;
}

.chat-footer {
  display: flex;
  padding: 10px;
  background: #f5f5f5;
  border-top: 1px solid #ddd;
}

.chat-footer .el-input {
  flex: 1;
  margin-right: 10px;
}
</style>
