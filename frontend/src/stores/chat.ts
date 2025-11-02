// stores/chat.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatRecord } from '../types'
import api from '@/api/chat'

export interface Conversation {
  id: string
  assistantId: number
  assistantName: string
  messages: ChatRecord[]
}

// 注意：键使用 string，避免 TS 将数字索引当作不同类型
export interface AssistantConversations {
  [assistantId: string]: Conversation[]
}

export const useChatStore = defineStore('chat', () => {
  // 每个助手的会话列表（键为字符串）
  const conversations = ref<AssistantConversations>({})

  // 当前选中会话（string），以及当前助手 id（number | null）
  const currentConversationId = ref<string | null>(null)
  const currentAssistantId = ref<number | null>(null)

  // 当前助手的会话列表（安全返回数组）
  const currentAssistantConversations = computed(() => {
    const aid = currentAssistantId.value
    if (aid === null) return []
    const key = String(aid)
    const convs = conversations.value[key]
    return Array.isArray(convs) ? convs : []
  })

  // 当前会话对象
  const currentConversation = computed(() => {
    const convs = currentAssistantConversations.value
    return convs.find(c => c.id === currentConversationId.value) || null
  })

  // 当前消息列表
  const currentMessages = computed(() => currentConversation.value?.messages || [])

  /**
   * 新建会话
   * - assistantId: number
   * - assistantName: string
   * - convId?: 已知会话 id（用于导入/恢复）
   * - messages?: 可选初始消息数组
   */
  async function addConversation(
    assistantId: number,
    assistantName: string,
    convId?: string,
    messages?: ChatRecord[]
  ) {
    try {
      let id = convId
      if (!id) {
        // 调后端创建并获取 conversation_id
        const res = await api.post(`/conversation/${assistantId}`)
        id = res.data.conversation_id
      }

      if (!id) {
        throw new Error('没有获得 conversation_id')
      }

      const conv: Conversation = {
        id,
        assistantId,
        assistantName,
        messages: messages ?? []
      }

      const key = String(assistantId)
      if (!Array.isArray(conversations.value[key])) {
        conversations.value[key] = []
      }

      // 防止重复 push（幂等）
      const exists = conversations.value[key].some(c => c.id === id)
      if (!exists) conversations.value[key].push(conv)

      // 设置当前
      currentConversationId.value = id
      currentAssistantId.value = assistantId

      return conv
    } catch (err) {
      console.error('新增会话失败:', err)
      return null
    }
  }

  /** 删除会话（同步后端） */
  async function deleteConversation(convId: string, assistantId: number) {
    const key = String(assistantId)
    const convs = conversations.value[key]
    if (!Array.isArray(convs)) return

    try {
      await api.delete(`/conversation/${assistantId}/${convId}`)
      conversations.value[key] = convs.filter(c => c.id !== convId)

      // 如果删除了当前会话，切换到该助手第一个会话或设为 null
      if (currentConversationId.value === convId) {
        const next = conversations.value[key]?.[0] || null
        currentConversationId.value = next?.id || null
      }
    } catch (err) {
      console.error('删除会话失败:', err)
    }
  }

  /** 添加消息到会话（不触发后端） */
  function addMessage(convId: string, msg: ChatRecord, assistantId: number) {
    const key = String(assistantId)
    const convs = conversations.value[key]
    if (!Array.isArray(convs)) return
    const conv = convs.find(c => c.id === convId)
    if (conv) conv.messages.push(msg)
  }

  /** 设置当前会话（本地） */
  function setCurrent(convId: string, assistantId: number) {
    currentConversationId.value = convId
    currentAssistantId.value = assistantId
  }

  return {
    conversations,
    currentConversationId,
    currentAssistantId,
    currentAssistantConversations,
    currentConversation,
    currentMessages,
    addConversation,
    deleteConversation,
    addMessage,
    setCurrent
  }
})
