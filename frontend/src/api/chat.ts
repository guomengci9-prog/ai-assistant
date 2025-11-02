// api/chat.ts
import axios from "axios"

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
})

export interface ChatRecord {
  role: string
  content: string
}

/** 获取助手历史记录，用于初始化 Pinia */
export const getHistory = (assistantId: number) =>
  api.get(`/chat/history/${assistantId}`)

/** 获取单个助手信息 */
export const getAssistantById = (assistantId: number) =>
  api.get(`/assistants/${assistantId}`)

/**
 * 注意：发送消息现在前端走 WebSocket，不再使用 HTTP POST
 * 如果你需要保留，可写作备用接口，但前端 send() 方法不调用它
 */
export const sendMessage = (assistantId: number, msg: string) =>
  api.post(`/chat/${assistantId}`, { message: msg })
