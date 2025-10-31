<template>
  <div class="chat-page">
    <header class="chat-header">
      <el-button @click="back" size="small">返回助手列表</el-button>
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
const messages = ref<ChatRecord[]>([])
const input = ref('')
const chatBody = ref<HTMLElement | null>(null)
const loading = ref(true)
const error = ref('')
const streamingReply = ref('')

let ws: WebSocket | null = null

function scrollToBottom() {
  nextTick(() => {
    chatBody.value && (chatBody.value.scrollTop = chatBody.value.scrollHeight)
  })
}

function connectWS() {
  ws = new WebSocket(`ws://127.0.0.1:8000/api/ws/chat/${assistantId}`)

  ws.onmessage = (event) => {
    const text = event.data

    if (text === "[END]") {
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

async function loadChat() {
  loading.value = true
  try {
    const res = await getAssistantById(assistantId)
    assistantName.value = res.data.name

    // ✅ 读取默认提示词
    const defaultPrompt = res.data.defaultPrompt
    if (defaultPrompt) {
      messages.value.push({ role: 'assistant', content: defaultPrompt })
    }

    // ✅ 加载历史记录
    const historyRes = await getHistory(assistantId)
    if (Array.isArray(historyRes.data)) {
      messages.value.push(...historyRes.data)
    }

    scrollToBottom()
  } catch (e) {
    console.error('加载聊天失败', e)
    error.value = '加载聊天失败，请刷新页面'
    messages.value = []
  } finally {
    loading.value = false
  }
}


function send() {
  if (!input.value.trim() || !ws) return

  const msg = input.value
  if (Array.isArray(messages.value)) {
    messages.value.push({ role: 'user', content: msg })
  } else {
    messages.value = [{ role: 'user', content: msg }]
  }
  scrollToBottom()

  ws.send(JSON.stringify({ message: msg }))

  input.value = ''
}

function back() {
  router.push('/assistants')
}

onMounted(() => {
  loadChat()
  connectWS()
})
onBeforeUnmount(() => ws?.close())
</script>

<style scoped>
/* === 整体页面 === */
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;

  /* 模拟手机屏幕居中显示 */
  max-width: 400px;
  margin: 0 auto;
  border-left: 1px solid #ccc;
  border-right: 1px solid #ccc;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  background: #f0f0f0;
}

/* === 头部 === */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 10px;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
  font-size: 16px;
}

/* === 聊天内容区 === */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: #eaeaea;
}

/* 聊天消息 */
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
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 16px;
  background: #fff;
  word-break: break-word;
}

.chat-message.user .bubble {
  background: #1890ff;
  color: #fff;
}

/* === 底部输入区 === */
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

/* === 响应式调整 === */
@media (max-width: 500px) {
  .chat-page {
    max-width: 100%;
    border-left: none;
    border-right: none;
    box-shadow: none;
  }
}
</style>