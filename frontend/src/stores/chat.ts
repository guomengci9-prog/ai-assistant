// stores/chat.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatRecord } from '../types'

interface Conversation {
  id: number                  // 前端唯一会话ID
  assistantId: number         // 对应后端 assistant_id
  assistantName: string
  messages: ChatRecord[]
}

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<number | null>(null)

  /** 当前会话 */
  const currentMessages = computed(() => {
    const conv = conversations.value.find(c => c.id === currentConversation.value)
    return conv ? conv.messages : []
  })

  /** 新增会话 */
  function addConversation(conv: Conversation) {
    conversations.value.push(conv)
    currentConversation.value = conv.id
  }

  /** 删除会话 */
  function deleteConversation(id: number) {
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (currentConversation.value === id) {
      currentConversation.value = conversations.value.length
        ? conversations.value[0].id
        : null
    }
  }

  /** 添加消息到指定会话 */
  function addMessage(convId: number, msg: ChatRecord) {
    const conv = conversations.value.find(c => c.id === convId)
    if (conv) conv.messages.push(msg)
  }

  /** 设置当前会话 */
  function setCurrent(convId: number) {
    currentConversation.value = convId
  }

  /** 查找当前会话对象 */
  function getCurrentConversation() {
    return conversations.value.find(c => c.id === currentConversation.value) || null
  }

  return {
    conversations,
    currentConversation,
    currentMessages,
    addConversation,
    deleteConversation,
    addMessage,
    setCurrent,
    getCurrentConversation
  }
}, {
  persist: true   // 可选：保持刷新后聊天状态
})
