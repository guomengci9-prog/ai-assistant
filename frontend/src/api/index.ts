import axios from 'axios'

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
// account 可以是邮箱或手机号
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
export const getAssistantById = (id: number) => axios.get(`/assistants/${id}`)

export const sendMessage = (assistantId: number, message: string) =>
  axios.post(`/chat/${assistantId}`, { assistant_id: assistantId, message })

export const getHistory = (assistantId: number) =>
  axios.get(`/chat/history/${assistantId}`)
