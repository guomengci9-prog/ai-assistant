<template>
  <div class="chat-container" :class="{ 'sidebar-open': isDesktop || showSidebar }">
    <div
      v-if="!isDesktop"
      class="sidebar-overlay"
      :class="{ show: showSidebar }"
      @click="closeSidebar"
    />

    <!-- 对话列表 -->
    <aside
      class="chat-sidebar"
      :class="{
        mobile: !isDesktop,
        visible: isDesktop || showSidebar
      }"
    >
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

    <section class="chat-main">
      <header class="chat-header">
        <div class="header-left">
          <el-button type="text" class="header-btn" @click="back">
            <el-icon><ArrowLeft /></el-icon>
          </el-button>
          <el-button
            v-if="!isDesktop"
            class="header-btn hamburger-trigger"
            circle
            size="small"
            @click="toggleSidebar"
            aria-label="展开对话列表"
          >
            <span class="hamburger-icon" aria-hidden="true">
              <span class="hamburger-line" />
              <span class="hamburger-line short" />
              <span class="hamburger-line" />
            </span>
            <span class="sr-only">展开对话列表</span>
          </el-button>
        </div>
        <h3 class="header-title">{{ assistantName }}</h3>
        <div class="header-right">
          <el-button
            type="primary"
            circle
            size="small"
            class="new-chat-btn"
            @click="newChat"
          >
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>
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
          <div class="bubble">
            <template v-if="msg.message_type === 'attachment' && msg.attachments?.length">
              <div
                v-for="file in msg.attachments"
                :key="file.id"
                class="attachment-preview"
              >
                <div v-if="isImageAttachment(file)" class="attachment-image">
                  <img :src="resolveFileUrl(file.url)" :alt="file.filename" />
                </div>
                <div class="attachment-meta">
                  <el-icon><Paperclip /></el-icon>
                  <a
                    :href="resolveFileUrl(file.url)"
                    target="_blank"
                    rel="noopener"
                    class="attachment-link"
                  >
                    {{ file.filename }}
                  </a>
                  <span class="attachment-size">{{ formatFileSize(file.size) }}</span>
                </div>
              </div>
            </template>
            <div v-else class="message-content" v-html="renderMarkdown(msg.content)"></div>
          </div>
        </div>

        <!-- 娴佸紡鍥炲鏄剧ず -->
        <div v-if="streamingReply" class="chat-message assistant">
          <div class="assistant-name">{{ assistantName }}</div>
          <div class="bubble">
            <div class="message-content" v-html="renderMarkdown(streamingReply)"></div>
          </div>
        </div>
      </main>

      <footer class="chat-footer">
        <input
          ref="attachmentInputRef"
          class="sr-only"
          type="file"
          multiple
          :accept="attachmentAccept"
          @change="handleAttachmentChange"
        />
        <div v-if="hasPendingAttachments" class="pending-attachments">
          <div
            v-for="item in pendingAttachments"
            :key="item.id"
            class="pending-attachment-chip"
          >
            <el-icon><Paperclip /></el-icon>
            <div class="chip-info">
              <span class="chip-name">{{ item.file.name }}</span>
              <span class="chip-size">{{ formatFileSize(item.file.size) }}</span>
            </div>
            <el-icon class="chip-remove" @click="removePendingAttachment(item.id)">
              <Close />
            </el-icon>
          </div>
        </div>
        <el-button
          class="attachment-btn"
          circle
          :loading="attachmentUploading"
          @click="triggerAttachment"
        >
          <el-icon><Paperclip /></el-icon>
        </el-button>
        <el-input
          ref="messageInputRef"
          v-model="input"
          placeholder="输入消息..."
          @keyup.enter="send"
          clearable
        />
        <el-button
          type="primary"
          :loading="attachmentUploading"
          @click="send"
        >
          发送
        </el-button>
      </footer>
    </section>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Delete, Plus, Search, Paperclip, Close } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useChatStore } from '@/stores/chat'
import chatApi, { getAssistantById, getHistory, uploadAttachment } from '@/api/chat'
import type { ChatAttachment, ChatRecord } from '../types'
import type { InputInstance } from 'element-plus'

const props = defineProps<{ id: number }>()
const router = useRouter()
const chatStore = useChatStore()

const assistantName = ref('')
const input = ref('')
const streamingReply = ref('')
const chatBody = ref<HTMLElement | null>(null)
const searchKeyword = ref('') // 搜索关键词
const messageInputRef = ref<InputInstance | null>(null)
const attachmentInputRef = ref<HTMLInputElement | null>(null)
const isDesktop = ref(false)
const showSidebar = ref(false)
const assistantId = ref(props.id)
interface PendingAttachmentItem {
  id: string
  file: File
}
const pendingAttachments = ref<PendingAttachmentItem[]>([])
const attachmentUploading = ref(false)
const attachmentAccept =
  'image/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.rar,.csv,.json'
const fileHost =
  (chatApi.defaults.baseURL || '').replace(/\/api\/?$/, '') || 'http://127.0.0.1:8000'
const hasPendingAttachments = computed(() => pendingAttachments.value.length > 0)

marked.setOptions({ breaks: true })

function renderMarkdown(content?: string) {
  const html = marked.parse(content || '')
  return DOMPurify.sanitize(html)
}

let ws: WebSocket | null = null
const pendingWsMessages: Array<{ conversationId: string; message: string }> = []

function ensureWsState(): boolean {
  return !!ws && ws.readyState === WebSocket.OPEN
}

function flushPendingMessages() {
  if (!ensureWsState()) return
  while (pendingWsMessages.length) {
    const payload = pendingWsMessages.shift()
    if (!payload) break
    ws?.send(JSON.stringify({
      conversation_id: payload.conversationId,
      message: payload.message,
    }))
  }
}

/** 婊氬埌搴曢儴 */
function scrollToBottom() {
  nextTick(() => {
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
  })
}

function focusInput() {
  nextTick(() => messageInputRef.value?.focus())
}

function triggerAttachment() {
  attachmentInputRef.value?.click()
}

function handleAttachmentChange(event: Event) {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return

  const newItems = Array.from(files).map(file => ({
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    file,
  }))
  pendingAttachments.value.push(...newItems)
  target.value = ''
}

function removePendingAttachment(id: string) {
  pendingAttachments.value = pendingAttachments.value.filter(item => item.id !== id)
}

function updateIsDesktop() {
  if (typeof window === 'undefined') return
  isDesktop.value = window.innerWidth >= 900
  showSidebar.value = isDesktop.value
}

function toggleSidebar() {
  if (isDesktop.value) return
  showSidebar.value = !showSidebar.value
}

function closeSidebar() {
  if (!isDesktop.value) {
    showSidebar.value = false
  }
}

async function uploadAttachmentFile(file: File, conversationId: string) {
  const id = assistantId.value
  const { data } = await uploadAttachment(id, conversationId, file)
  const targetConversation = data.conversation_id || conversationId

  await chatStore.addConversation(id, assistantName.value, targetConversation)
  chatStore.setCurrent(targetConversation, id)

  const conversation = chatStore.currentAssistantConversations.find(c => c.id === targetConversation)
  if (data.opening_message && conversation && conversation.messages.length === 0) {
    chatStore.addMessage(
      targetConversation,
      {
        role: 'assistant',
        content: data.opening_message,
        hideName: true,
        message_type: 'opening',
      },
      id,
    )
  }

  chatStore.addMessage(targetConversation, data.message as ChatRecord, id)
  scrollToBottom()
}

function resolveFileUrl(url?: string) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  return `${fileHost}${url}`
}

function isImageAttachment(file?: ChatAttachment) {
  if (!file) return false
  const contentType = (file.content_type || '').toLowerCase()
  if (contentType.startsWith('image/')) return true
  const name = (file.filename || '').toLowerCase()
  return ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'].some(ext => name.endsWith(ext))
}

function formatFileSize(size?: number) {
  if (!size || size <= 0) return ''
  const units = ['B', 'KB', 'MB', 'GB']
  let value = size
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  const digits = value >= 10 || unitIndex === 0 ? 0 : 1
  return `${value.toFixed(digits)}${units[unitIndex]}`
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
async function loadConversation(convId?: string, options?: { forceNew?: boolean }) {
  const id = assistantId.value
  const res = await getAssistantById(id)
  assistantName.value = res.data.name

  let currentConvId = options?.forceNew ? undefined : convId

  if (!currentConvId && !options?.forceNew) {
    const convList = chatStore.getConversationsByAssistant(id)
    if (convList.length) {
      currentConvId = convList[0].id
    }
  }

  if (!currentConvId) {
    // 新建会话
    const conv = await chatStore.addConversation(id, assistantName.value)
    if (!conv) return
    currentConvId = conv.id
  }

  // 设置当前助手/会话
  chatStore.setCurrent(currentConvId, id)

  // 拉取历史消息
  const historyRes = await getHistory(id, currentConvId)
  if (Array.isArray(historyRes.data.data) && historyRes.data.data.length) {
    chatStore.setConversationMessages(currentConvId!, id, historyRes.data.data as ChatRecord[])
  }

  scrollToBottom()
  focusInput()
}

async function selectConversation(convId: string) {
  await loadConversation(convId)
  if (!isDesktop.value) {
    closeSidebar()
  }
  focusInput()
}

/** 建立 WebSocket */
function connectWS(force = false) {
  if (ws && !force) {
    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
      return
    }
  }

  if (ws) {
    try {
      ws.close()
    } catch {}
  }

  ws = new WebSocket(`ws://127.0.0.1:8000/ws/chat/${assistantId.value}`)

  ws.onopen = () => {
    console.log('[WS] connected')
    flushPendingMessages()
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'chunk') {
      streamingReply.value += data.content
      scrollToBottom()
    }
    if (data.type === 'end') {
      if (streamingReply.value && chatStore.currentConversationId) {
        chatStore.addMessage(
          chatStore.currentConversationId,
          { role: 'assistant', content: streamingReply.value },
          assistantId.value,
        )
        streamingReply.value = ''
        scrollToBottom()
      }
    }
    if (data.type === 'error') {
      ElMessage.error(data.content)
    }
  }

  ws.onclose = () => {
    console.log('[WS] disconnected')
    ws = null
    setTimeout(() => connectWS(), 1200)
  }
}

/** 发送消息（统一触发附件上传）*/
async function send() {
  const text = input.value.trim()
  const hasText = text.length > 0
  const filesToSend = [...pendingAttachments.value]

  if (!hasText && filesToSend.length === 0) return

  if (!chatStore.currentConversationId) {
    await loadConversation()
  }
  if (!chatStore.currentConversationId) {
    ElMessage.error('暂时无法创建对话，请稍后重试')
    return
  }

  if (!ensureWsState()) {
    connectWS(true)
    ElMessage.warning('聊天连接正在重新建立，请稍后再发送')
    return
  }

  const conversationId = chatStore.currentConversationId

  if (filesToSend.length) {
    attachmentUploading.value = true
    try {
      for (const item of filesToSend) {
        try {
          await uploadAttachmentFile(item.file, conversationId)
        } catch (error) {
          console.error('附件上传失败:', error)
          ElMessage.error('附件上传失败')
        }
      }
      pendingAttachments.value = []
    } finally {
      attachmentUploading.value = false
    }
  }

  if (hasText) {
      chatStore.addMessage(
        conversationId,
        { role: 'user', content: text },
        assistantId.value,
      )

    const payload = { conversationId, message: text }
    if (ensureWsState()) {
    ws?.send(JSON.stringify({
      conversation_id: conversationId,
      message: text,
    }))
    } else {
      pendingWsMessages.push(payload)
      connectWS(true)
    }

    input.value = ''
    streamingReply.value = ''
  }

  scrollToBottom()
  focusInput()
}

/** 新建会话 */
async function newChat() {
  const currentConv = chatStore.currentConversation
  const hasUserContent = currentConv?.messages.some(
    msg => msg.role === 'user' || msg.message_type === 'attachment',
  )
  if (currentConv && !hasUserContent) {
    ElMessage.info('当前已经是最新对话')
    return
  }

  await loadConversation(undefined, { forceNew: true })
  if (!isDesktop.value) {
    closeSidebar()
  }
  focusInput()
}

/** 删除会话 */
async function confirmDelete(convId: string) {
  const conv = chatStore.currentAssistantConversations.find(c => c.id === convId)
  if (!conv) return

  await ElMessageBox.confirm(
    '确定删除该对话吗？',
    '删除确认',
    {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    },
  )
    .then(async () => {
      await chatStore.deleteConversation(convId, assistantId.value)

      const nextConv = chatStore.currentAssistantConversations[0]
      if (nextConv) await loadConversation(nextConv.id)
      else await newChat()

      ElMessage.success('删除成功')
    })
    .catch(() => {})
}
function back() {
  router.push('/assistants')
}

watch(
  () => chatStore.currentConversationId,
  () => {
    pendingAttachments.value = []
  },
)

onMounted(async () => {
  updateIsDesktop()
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', updateIsDesktop)
  }
  await loadConversation()
  connectWS()
})
onBeforeUnmount(() => {
  ws?.close()
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateIsDesktop)
  }
})

watch(
  () => props.id,
  async (newId, oldId) => {
    if (newId === oldId) return
    assistantId.value = newId
    pendingAttachments.value = []
    streamingReply.value = ''
    await loadConversation()
    connectWS(true)
  },
)
</script>

<style scoped>
.chat-container {
  width: 960px;
  max-width: 94%;
  min-height: 720px;
  height: clamp(760px, 92vh, 1000px);
  margin: 0 auto;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  box-sizing: border-box;
  background: #fff;
  border-radius: 22px;
  box-shadow: 0 15px 45px rgba(15, 23, 42, 0.2);
  align-items: stretch;
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  z-index: 15;
}
.sidebar-overlay.show {
  opacity: 1;
  pointer-events: auto;
}

.chat-sidebar {
  width: 280px;
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 12px 32px rgba(15, 23, 95, 0.15);
  background: #fff;
  padding: 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  z-index: 20;
  flex-shrink: 0;
}
.chat-sidebar.mobile {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  transform: translateX(-100%);
  transition: transform 0.25s ease;
  border-radius: 0 18px 18px 0;
  max-width: 82%;
}
.chat-sidebar.mobile.visible {
  transform: translateX(0);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.search-box {
  margin-bottom: 12px;
}
.conversation-list {
  flex: 1;
  overflow-y: auto;
}
.conversation-item {
  padding: 10px 12px;
  border-radius: 14px;
  cursor: pointer;
  margin-bottom: 10px;
  background: linear-gradient(145deg, #edf3ff, #ffffff);
  color: #333;
  transition: 0.18s;
  position: relative;
  display: flex;
  flex-direction: column;
  box-shadow: 0 6px 18px rgba(64, 145, 255, 0.12);
}
.conversation-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(64, 158, 255, 0.18);
}
.conversation-item.active {
  background: linear-gradient(135deg, #7aa8ff, #819cff);
  color: #fff;
  box-shadow: none;
}
.delete-icon {
  position: absolute;
  right: 8px;
  top: 8px;
  font-size: 14px;
  cursor: pointer;
  color: #666;
}
.delete-icon:hover {
  color: #ff4d4f;
}
.conv-name {
  font-weight: 600;
}
.conv-preview {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-top: 0;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(12px);
  box-shadow: 0 20px 42px rgba(37, 55, 118, 0.18);
  min-height: 520px;
}

.chat-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(221, 221, 221, 0.6);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}
.header-btn {
  color: #64748b;
  border-radius: 16px;
  padding: 6px;
  transition: background-color 0.2s, color 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.header-btn:hover {
  background: rgba(100, 116, 139, 0.15);
}
.header-btn.hamburger-trigger {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(15, 23, 42, 0.05);
  color: #0f172a;
  border: 1px solid rgba(15, 23, 42, 0.12);
  padding: 0;
}
.header-btn.hamburger-trigger:hover {
  background: rgba(15, 23, 42, 0.1);
  color: #0f172a;
}
.hamburger-icon {
  display: inline-flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  gap: 2px;
  width: 14px;
}
.hamburger-line {
  display: block;
  height: 2px;
  width: 14px;
  border-radius: 999px;
  background: currentColor;
}
.hamburger-line.short {
  width: 9px;
}
.header-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #273049;
}
.new-chat-btn {
  box-shadow: 0 10px 24px rgba(64, 158, 255, 0.45);
}

.chat-body {
  flex: 1;
  padding: 12px 16px;
  overflow-y: auto;
}
.chat-message {
  margin: 8px 0;
  display: flex;
  flex-direction: column;
}
.chat-message.user {
  align-items: flex-end;
}
.chat-message.assistant {
  align-items: flex-start;
}
.assistant-name {
  font-size: 12px;
  margin-bottom: 4px;
  color: #8b97ab;
}
.bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 16px;
  word-break: break-word;
  box-shadow: 0 10px 24px rgba(39, 69, 135, 0.08);
}
.chat-message.user .bubble {
  background: linear-gradient(135deg, #5fa5ff, #7b8bff);
  color: #fff;
}
.chat-message.assistant .bubble {
  background-color: #f7f8fc;
  color: #333;
  border: 1px solid rgba(224, 224, 224, 0.6);
}

.chat-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid rgba(221, 221, 221, 0.4);
}
.chat-footer .el-input {
  flex: 1;
  --el-input-bg-color: rgba(255, 255, 255, 0.85);
  --el-input-border-radius: 16px;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
.attachment-btn {
  border: none;
  background: rgba(148, 163, 184, 0.18);
  color: #475569;
  width: 42px;
  height: 42px;
}
.attachment-btn:hover {
  background: rgba(96, 165, 250, 0.25);
  color: #1d4ed8;
}
.attachment-preview {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.attachment-image img {
  max-width: 240px;
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.9);
}
.attachment-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #475569;
}
.attachment-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}
.attachment-link:hover {
  text-decoration: underline;
}
.attachment-size {
  font-size: 12px;
  color: #94a3b8;
}
.pending-attachments {
  flex-basis: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.pending-attachment-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 16px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  color: #334155;
  font-size: 13px;
}
.chip-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.chip-name {
  font-weight: 600;
}
.chip-size {
  font-size: 12px;
  color: #94a3b8;
}
.chip-remove {
  cursor: pointer;
  color: #94a3b8;
}
.chip-remove:hover {
  color: #ef4444;
}

@media (min-width: 900px) {
  .chat-container {
    flex-direction: row;
    min-height: 720px;
    height: clamp(760px, 92vh, 1000px);
    width: 960px;
    padding: 0;
    gap: 0;
  }
  .chat-sidebar {
    position: relative;
    height: 100%;
    border-right: 1px solid rgba(226, 232, 240, 0.85);
    border-radius: 22px 0 0 22px;
    box-shadow: inset -1px 0 0 rgba(226, 232, 240, 0.85);
    transform: none !important;
  }
  .chat-main {
    border-radius: 0 22px 22px 0;
    height: 100%;
  }
  .sidebar-overlay {
    display: none;
  }
}

@media (max-width: 900px) {
  .chat-container {
    position: relative;
    top: 0;
    left: 0;
    transform: none;
    width: 100%;
    max-width: 100%;
    height: 100vh;
    border-radius: 0;
    box-shadow: none;
    background: linear-gradient(140deg, #eef2ff 0%, #fdf4ff 45%, #ffffff 100%);
    padding: 20px 12px 80px;
  }
}
</style>











.hamburger-trigger {
  padding: 6px;
}
