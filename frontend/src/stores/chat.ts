// stores/chat.ts
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
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

function enforceSingleOpening(messages: ChatRecord[]) {
  const result: ChatRecord[] = []
  let openingAdded = false
  for (const msg of messages) {
    if (msg.message_type === 'opening') {
      if (openingAdded) continue
      openingAdded = true
    }
    result.push(msg)
  }
  return result
}

export const useChatStore = defineStore('chat', () => {
  // 每个助手的会话列表（键为字符串）
  const STORAGE_KEY = 'chat_conversations_v1'
  function loadStoredConversations(): AssistantConversations {
    if (typeof window === 'undefined') return {}
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY)
      if (!raw) return {}
      const parsed = JSON.parse(raw)
      return parsed && typeof parsed === 'object' ? parsed : {}
    } catch (err) {
      console.warn('Failed to load stored conversations', err)
      return {}
    }
  }

  const conversations = ref<AssistantConversations>(loadStoredConversations())

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
      let openingMessage: string | undefined
      if (!id) {
        // 调后端创建并获取 conversation_id
        const res = await api.post(`/conversation/${assistantId}`)
        id = res.data.conversation_id
        openingMessage = res.data.opening_message
      }

      if (!id) {
        throw new Error('没有获得 conversation_id')
      }

      let initialMessages = messages ? enforceSingleOpening([...messages]) : []
      if (!messages && openingMessage) {
        initialMessages = enforceSingleOpening([{
          role: 'assistant',
          content: openingMessage,
          hideName: true,
          message_type: 'opening'
        }])
      }

      const conv: Conversation = {
        id,
        assistantId,
        assistantName,
        messages: initialMessages
      }

      const key = String(assistantId)
      if (!Array.isArray(conversations.value[key])) {
        conversations.value[key] = []
      }

      const list = conversations.value[key]
      const hasUserMessages = (item: Conversation) => item.messages.some(msg => msg.role === 'user')
      if (!messages) {
        for (let i = list.length - 1; i >= 0; i--) {
          const item = list[i]
          if (item.id !== id && !hasUserMessages(item)) {
            list.splice(i, 1)
          }
        }
      }
      const existIndex = list.findIndex(c => c.id === id)
      if (existIndex !== -1) {
        // 更新现有会话信息
        const existing = list.splice(existIndex, 1)[0]
        existing.assistantName = assistantName
        if (messages && messages.length) {
          existing.messages = messages
        }
        list.unshift(existing)
      } else {
        list.unshift(conv)
      }

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
    if (!conv) return
    if (msg.message_type === 'opening') {
      const hasOpening = conv.messages.some(existing => existing.message_type === 'opening')
      if (hasOpening) return
    }
    conv.messages.push(msg)
  }

  function setConversationMessages(convId: string, assistantId: number, messages: ChatRecord[]) {
    const key = String(assistantId)
    const convs = conversations.value[key]
    if (!Array.isArray(convs)) return
    const conv = convs.find(c => c.id === convId)
    if (!conv) return
    conv.messages = enforceSingleOpening([...messages])
  }

  /** 设置当前会话（本地） */
  function setCurrent(convId: string, assistantId: number) {
    currentConversationId.value = convId
    currentAssistantId.value = assistantId
  }

  function getConversationsByAssistant(assistantId: number) {
    const key = String(assistantId)
    const convs = conversations.value[key]
    return Array.isArray(convs) ? convs : []
  }

  if (typeof window !== 'undefined') {
    watch(
      conversations,
      (value) => {
        try {
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
        } catch (err) {
          console.warn('Failed to persist conversations', err)
        }
      },
      { deep: true },
    )
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
    setConversationMessages,
    setCurrent,
    getConversationsByAssistant
  }
})
