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
