import axios from 'axios'
import {
  getAssistantById,
  getHistory,
  sendMessage,
  createConversation,
  deleteConversation
} from './chat'

// 全局 baseURL
axios.defaults.baseURL = 'http://127.0.0.1:8000/api'

// ================= 登录 =================
export interface LoginData {
  account: string
  password: string
}
export const login = (data: LoginData) => axios.post('/login', data)

// ================= 注册 =================
export interface RegisterData {
  username: string
  password: string
  email?: string
  phone?: string
}
export const register = (data: RegisterData) => axios.post('/register', data)

// ================= 忘记密码 =================
export interface ForgotPasswordData {
  account: string
}
export const forgotPassword = (data: ForgotPasswordData) =>
  axios.post('/forgot-password', data)

// ================= 重置密码 =================
export interface ResetPasswordData {
  account: string
  code: string
  new_password: string
}
export const resetPassword = (data: ResetPasswordData) =>
  axios.post('/reset-password', data)

// ================= 助手与聊天 API =================
export const getAssistants = () => axios.get('/assistants')

// 从 chat.ts 导出
export {
  getAssistantById,
  getHistory,
  sendMessage,
  createConversation,
  deleteConversation
}

// ================= 管理端助手管理 =================
export interface UpdatePromptPayload {
  prompt_content?: string
  system_prompt?: string
  scene_prompt?: string
  user_prefill?: string
  opening_message?: string
}

export const getAdminAssistants = () => axios.get('/admin/assistants')

export const updateAssistantPrompts = (
  assistantId: number,
  data: UpdatePromptPayload
) => axios.put(`/admin/assistants/${assistantId}/prompt`, data)

// ================= 管理端文档管理 =================
export interface UpdateDocumentPayload {
  name?: string
  description?: string
  assistant_id?: number
  parameters?: Record<string, unknown>
  parse_status?: string
}

export const getAdminDocs = () => axios.get('/admin/docs')

export const uploadAdminDoc = (formData: FormData) =>
  axios.post('/admin/docs', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

export const parseAdminDoc = (docId: number) => axios.post(`/admin/docs/${docId}/parse`)

export const updateAdminDoc = (docId: number, data: UpdateDocumentPayload) =>
  axios.put(`/admin/docs/${docId}`, data)

export const deleteAdminDoc = (docId: number) => axios.delete(`/admin/docs/${docId}`)
