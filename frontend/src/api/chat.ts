// src/api/chat.ts
import axios from "axios"
import type { ChatRecord } from "@/types"

// axios 实例（确保 baseURL 正确）
const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
})

export type { ChatRecord }

export const getAssistantById = (assistantId: number) =>
  api.get(`/assistants/${assistantId}`)

// 新建会话 -> POST /conversation/{assistant_id}
export const createConversation = (assistantId: number) =>
  api.post(`/conversation/${assistantId}`)

// 删除会话 -> DELETE /conversation/{assistant_id}/{conversation_id}
export const deleteConversation = (assistantId: number, conversationId: string) =>
  api.delete(`/conversation/${assistantId}/${conversationId}`)

// 获取历史 -> GET /chat/history/{assistant_id}?conversation_id=...
export const getHistory = (assistantId: number, conversationId: string) =>
  api.get(`/chat/history/${assistantId}`, { params: { conversation_id: conversationId } })

// 备用 - 非流式发送（/chat/{assistant_id}）
export const sendMessage = (assistantId: number, message: string, conversationId?: string) =>
  api.post(`/chat/${assistantId}`, { message, conversation_id: conversationId })

export interface AttachmentUploadResponse {
  conversation_id: string
  message: ChatRecord
  opening_message?: string
}

export const uploadAttachment = (assistantId: number, conversationId: string, file: File) => {
  const formData = new FormData()
  formData.append('conversation_id', conversationId)
  formData.append('file', file)
  return api.post<AttachmentUploadResponse>(`/chat/${assistantId}/attachments`, formData)
}

export default api
