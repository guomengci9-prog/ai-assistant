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
          :class="['conversation-item', conv.id === chatStore.currentConversationId ? 'active' : '']"
          @click="selectConversation(conv.id)"
        >
          <div class="conv-name">{{ conv.assistantName }}</div>
          <div class="conv-preview">
            {{ conv.messages.length ? conv.messages[conv.messages.length-1].content : '暂无消息' }}
          </div>

          <el-icon class="delete-icon" @click.stop="confirmDelete(conv.id)">
            <Delete />
          </el-icon>
        </div>
      </div>
    </aside>

    <!-- 右侧聊天 -->
    <section class="chat-main">
      <header class="chat-header">
        <el-button type="text" class="back-btn" @click="back">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h3>{{ assistantName }}</h3>
      </header>

      <main ref="chatBody" class="chat-body">
        <div
          v-for="(msg, idx) in chatStore.currentMessages"
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

        <!-- 流式回复显示 -->
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import { getAssistantById, getHistory } from '@/api/chat'
import type { ChatRecord } from '../types'

const props = defineProps<{ id: number }>()
const assistantId = props.id
const router = useRouter()
const chatStore = useChatStore()

const assistantName = ref('')
const input = ref('')
const streamingReply = ref('')
const chatBody = ref<HTMLElement | null>(null)
const searchKeyword = ref('') // 搜索关键字

let ws: WebSocket | null = null

/** 滚到底部 */
function scrollToBottom() {
  nextTick(() => {
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
  })
}

/** 过滤当前助手的会话列表 */
const filteredConversations = computed(() => {
  const convs = chatStore.currentAssistantConversations
  if (!convs || convs.length === 0) return []

  if (!searchKeyword.value.trim()) return convs

  const keyword = searchKeyword.value.toLowerCase()
  return convs.filter(c => {
    const lastMessage = c.messages[c.messages.length - 1]?.content || ''
    return c.assistantName.toLowerCase().includes(keyword)
      || lastMessage.toLowerCase().includes(keyword)
  })
})

/** 加载助手信息 + 当前会话历史消息 */
async function loadConversation(convId?: string) {
  const res = await getAssistantById(assistantId)
  assistantName.value = res.data.name

  let currentConvId = convId

  if (!currentConvId) {
    // 新建会话
    const conv = await chatStore.addConversation(assistantId, assistantName.value)
    if (!conv) return
    currentConvId = conv.id
  }

  // 设置当前助手/会话
  chatStore.setCurrent(currentConvId, assistantId)

  // 拉取历史消息
  const historyRes = await getHistory(assistantId, currentConvId)
  if (Array.isArray(historyRes.data.data)) {
    historyRes.data.data.forEach((msg: ChatRecord) => {
      chatStore.addMessage(currentConvId!, msg, assistantId)
    })
  }

  scrollToBottom()
}

/** 建立 WebSocket */
function connectWS() {
  if (ws) return // 已连接就不重复创建

  ws = new WebSocket(`ws://127.0.0.1:8000/ws/chat/${assistantId}`)

  ws.onopen = () => console.log('✅ WebSocket connected')

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'chunk') {
      streamingReply.value += data.content
      scrollToBottom()
    }
    if (data.type === 'end') {
      if (streamingReply.value && chatStore.currentConversationId) {
        chatStore.addMessage(chatStore.currentConversationId, { role: 'assistant', content: streamingReply.value }, assistantId)
        streamingReply.value = ''
        scrollToBottom()
      }
    }
    if (data.type === 'error') {
      ElMessage.error(data.content)
    }
  }

  ws.onclose = () => console.log('⚠️ WebSocket disconnected')
  ws.onerror = (err) => console.error('WebSocket error:', err)
}

/** 发送消息 */
function send() {
  if (!input.value.trim() || !ws || !chatStore.currentConversationId) return

  chatStore.addMessage(chatStore.currentConversationId, { role: 'user', content: input.value }, assistantId)

  ws.send(JSON.stringify({
    conversation_id: chatStore.currentConversationId,
    message: input.value
  }))

  input.value = ''
  streamingReply.value = ''
  scrollToBottom()
}

/** 新建会话 */
async function newChat() {
  await loadConversation()
}

/** 删除会话 */
async function confirmDelete(convId: string) {
  const conv = chatStore.currentAssistantConversations.find(c => c.id === convId)
  if (!conv) return

  await ElMessageBox.confirm(`确定删除「${conv.assistantName}」吗？`, '删除确认', {
    type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
  }).then(async () => {
    await chatStore.deleteConversation(convId, assistantId)

    const nextConv = chatStore.currentAssistantConversations[0]
    if (nextConv) await loadConversation(nextConv.id)
    else await newChat()

    ElMessage.success('删除成功')
  }).catch(() => {})
}

/** 切换会话 */
async function selectConversation(convId: string) {
  if (convId === chatStore.currentConversationId) return
  await loadConversation(convId)
}

function back() {
  router.push('/assistants')
}

onMounted(async () => {
  await loadConversation()
  connectWS()
})
onBeforeUnmount(() => ws?.close())
</script>

<style scoped>
/* 原样保持布局和样式 */
.chat-container { display: flex; width: 800px; max-width: 90%; height: 600px; border: 1px solid #ccc; border-radius: 10px; overflow: hidden; box-shadow: 0 0 15px rgba(0,0,0,0.1); background: #fff; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
.chat-sidebar { width: 240px; border-right: 1px solid #ddd; flex-direction: column; padding: 10px; display: flex; box-sizing: border-box; }
.sidebar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.search-box { margin-bottom: 8px; }
.conversation-list { flex: 1; overflow-y: auto; }
.conversation-item { padding: 6px 10px; border-radius: 12px; cursor: pointer; margin-bottom: 6px; background-color: #e8f0fe; color: #333; transition: 0.2s; position: relative; display: flex; flex-direction: column; }
.conversation-item:hover { background-color: #d0e1fd; }
.conversation-item.active { background-color: #98c7f4; color: #fff; }
.delete-icon { position: absolute; right: 8px; top: 8px; font-size: 14px; cursor: pointer; color: #666; }
.delete-icon:hover { color: #ff4d4f; }
.conv-name { font-weight: bold; }
.conv-preview { font-size: 12px; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.chat-main { flex: 1; display: flex; flex-direction: column; }
.chat-header { padding: 10px; border-bottom: 1px solid #ddd; text-align: center; position: relative; display: flex; justify-content: center; align-items: center; }
.back-btn { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); }
.chat-body { flex: 1; padding: 10px; overflow-y: auto; }
.chat-message { margin: 6px 0; display: flex; flex-direction: column; }
.chat-message.user { align-items: flex-end; }
.chat-message.assistant { align-items: flex-start; }
.assistant-name { text-align: center; font-size: 12px; margin-bottom: 2px; color: #888; }
.bubble { max-width: 70%; padding: 10px 14px; border-radius: 16px; word-break: break-word; }
.chat-message.user .bubble { background-color: #78baf7; color: #fff; }
.chat-message.assistant .bubble { background-color: #f0f0f0; color: #333; }
.chat-footer { display: flex; padding: 10px; border-top: 1px solid #ddd; }
.chat-footer .el-input { flex: 1; margin-right: 10px; }
</style>
