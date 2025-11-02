<template>
  <div class="chat-container">
    <!-- 左侧对话列表 -->
    <aside class="chat-sidebar">
      <div class="sidebar-header">
        <h3>对话列表</h3>
        <el-button type="primary" circle size="small" @click="newChat">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>

      <!-- 搜索框 -->
      <el-input
        v-model="searchKeyword"
        placeholder="搜索聊天..."
        size="small"
        clearable
        class="search-box"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <div class="conversation-list">
        <div
          v-for="conv in filteredConversations"
          :key="conv.id"
          :class="['conversation-item', conv.id === currentConversation ? 'active' : '']"
          @click="selectConversation(conv.id)"
        >
          <div class="conv-name">{{ conv.name }}</div>
          <div class="conv-preview">
            {{ conv.messages.length ? conv.messages[conv.messages.length-1].content : '暂无消息' }}
          </div>

          <!-- 删除按钮 -->
          <el-icon class="delete-icon" @click.stop="confirmDelete(conv.id)">
            <Delete />
          </el-icon>
        </div>
      </div>
    </aside>

    <!-- 右侧聊天区 -->
    <section class="chat-main">
      <header class="chat-header">
        <!-- 返回按钮 -->
        <el-button type="text" class="back-btn" @click="back">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h3>{{ assistantName }}</h3>
      </header>

      <main ref="chatBody" class="chat-body">
        <div
          v-for="(msg, idx) in currentMessages"
          :key="idx"
          :class="['chat-message', msg.role]"
        >
          <div
            v-if="msg.role === 'assistant' && !msg.hideName"
            class="assistant-name"
          >
            {{ assistantName }}
          </div>
          <div class="bubble">{{ msg.content }}</div>
        </div>

        <!-- 流式回复 -->
        <div v-if="streamingReply" class="chat-message assistant">
          <div class="assistant-name">{{ assistantName }}</div>
          <div class="bubble">{{ streamingReply }}</div>
        </div>
      </main>

      <footer class="chat-footer">
        <el-input
          v-model="input"
          placeholder="输入消息..."
          @keyup.enter="send"
          clearable
        />
        <el-button type="primary" @click="send">发送</el-button>
      </footer>
    </section>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, ArrowLeft, Search, Delete } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import type { ChatRecord } from '../types'
import { getHistory, getAssistantById } from '../api'

interface Props { id: number }
const props = defineProps<Props>()
const assistantId = props.id

const router = useRouter()
const assistantName = ref('')
const input = ref('')
const streamingReply = ref('')
const chatBody = ref<HTMLElement | null>(null)
let ws: WebSocket | null = null

const conversations = ref<{ id: number, messages: ChatRecord[], name: string }[]>([])
const currentConversation = ref<number | null>(null)
const searchKeyword = ref('')

const currentMessages = computed(() => {
  const conv = conversations.value.find(c => c.id === currentConversation.value)
  return conv ? conv.messages : []
})

const filteredConversations = computed(() => {
  if (!searchKeyword.value) return conversations.value
  return conversations.value.filter(c =>
    c.name.includes(searchKeyword.value) ||
    c.messages.some(m => m.content.includes(searchKeyword.value))
  )
})

function scrollToBottom() {
  nextTick(() => chatBody.value && (chatBody.value.scrollTop = chatBody.value.scrollHeight))
}

async function loadChat() {
  try {
    const res = await getAssistantById(assistantId)
    assistantName.value = res.data.name

    const firstId = Date.now()
    conversations.value.push({
      id: firstId,
      messages: res.data.defaultPrompt ? [{ role: 'assistant', content: res.data.defaultPrompt }] : [],
      name: `${assistantName.value} - 对话 1`
    })
    currentConversation.value = firstId

    const historyRes = await getHistory(assistantId)
    if (Array.isArray(historyRes.data)) {
      const conv = conversations.value.find(c => c.id === firstId)
      conv?.messages.push(...historyRes.data)
    }
    scrollToBottom()
  } catch (e) {
    console.error('加载聊天失败', e)
  }
}

function connectWS() {
  const token = localStorage.getItem('token') || ''
  ws = new WebSocket(`ws://127.0.0.1:8000/api/ws/chat/${assistantId}?token=${token}`)

  ws.onmessage = (event) => {
    const text = event.data
    if (text === '[END]') {
      if (streamingReply.value && currentConversation.value !== null) {
        const conv = conversations.value.find(c => c.id === currentConversation.value)
        conv?.messages.push({ role: 'assistant', content: streamingReply.value })
        streamingReply.value = ''
      }
      scrollToBottom()
      return
    }
    streamingReply.value += text
    scrollToBottom()
  }

  ws.onclose = () => setTimeout(connectWS, 1500)
}

function send() {
  if (!input.value.trim() || !ws || currentConversation.value === null) return
  const conv = conversations.value.find(c => c.id === currentConversation.value)
  conv?.messages.push({ role: 'user', content: input.value })
  ws.send(JSON.stringify({ message: input.value, conversationId: currentConversation.value }))
  input.value = ''
  scrollToBottom()
}

function newChat() {
  const newId = Date.now()
  conversations.value.push({ id: newId, messages: [], name: `${assistantName.value} - 对话 ${conversations.value.length + 1}` })
  currentConversation.value = newId
  scrollToBottom()
  ws?.send(JSON.stringify({ action: 'new_chat', conversationId: newId }))
}

function deleteConversation(id:number) {
  conversations.value = conversations.value.filter(c => c.id !== id)
  if (currentConversation.value === id) {
    if (conversations.value.length > 0) {
      currentConversation.value = conversations.value[0].id
    } else {
      const newId = Date.now()
      conversations.value.push({ id: newId, messages: [], name: `${assistantName.value} - 对话 1` })
      currentConversation.value = newId
    }
  }
}

/** ✅ 删除前弹窗确认 */
function confirmDelete(id:number) {
  const conv = conversations.value.find(c => c.id === id)
  ElMessageBox.confirm(
    `确定要删除对话「${conv?.name ?? '该会话'}」吗？`,
    '删除确认',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
  ).then(() => {
    deleteConversation(id)
    ElMessage.success('删除成功')
  }).catch(() => {})
}

function selectConversation(id: number) {
  currentConversation.value = id
  scrollToBottom()
}

function back() {
  router.push('/assistants')
}

onMounted(() => { loadChat(); connectWS() })
onBeforeUnmount(() => ws?.close())
</script>

<style scoped>
.chat-container {
  display: flex;
  width: 800px;
  max-width: 90%;
  height: 600px;
  border: 1px solid #ccc;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 0 15px rgba(0,0,0,0.1);
  background: #fff;
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
}

.chat-sidebar {
  width: 240px;
  border-right: 1px solid #ddd;
  flex-direction: column;
  padding: 10px;
  display: flex;
  box-sizing: border-box;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.search-box { margin-bottom: 8px; }

.conversation-list { flex: 1; overflow-y: auto; }

.conversation-item {
  padding: 6px 10px;
  border-radius: 12px;
  cursor: pointer;
  margin-bottom: 6px;
  background-color: #e8f0fe;
  color: #333;
  transition: 0.2s;
  position: relative;
  display: flex;
  flex-direction: column;
}

.conversation-item:hover { background-color: #d0e1fd; }
.conversation-item.active { background-color: #98c7f4; color: #fff; }

.delete-icon {
  position: absolute;
  right: 8px;
  top: 8px;
  font-size: 14px;
  cursor: pointer;
  color: #666;
}
.delete-icon:hover { color: #ff4d4f; }

.conv-name { font-weight: bold; }
.conv-preview { font-size: 12px; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.chat-main { flex: 1; display: flex; flex-direction: column; }

.chat-header {
  padding: 10px;
  border-bottom: 1px solid #ddd;
  text-align: center;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.back-btn { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); }

.chat-body { flex: 1; padding: 10px; overflow-y: auto; }

.chat-message { margin: 6px 0; display: flex; flex-direction: column; }
.chat-message.user { align-items: flex-end; }
.chat-message.assistant { align-items: flex-start; }

.assistant-name {
  text-align: center;
  font-size: 12px;
  margin-bottom: 2px;
  color: #888;
}

.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 16px;
  word-break: break-word;
}
.chat-message.user .bubble { background-color: #78baf7; color: #fff; }
.chat-message.assistant .bubble { background-color: #f0f0f0; color: #333; }

.chat-footer { display: flex; padding: 10px; border-top: 1px solid #ddd; }
.chat-footer .el-input { flex: 1; margin-right: 10px; }
</style>
