import axios from "axios"

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
})

// ================= 登录 =================
export interface LoginData {
  account: string
  password: string
}
export const login = (data: LoginData) => api.post("/login", data)

// ================= 注册 =================
export interface RegisterData {
  username: string
  password: string
  email?: string
  phone?: string
}
export const register = (data: RegisterData) => api.post("/register", data)

// ================= 忘记密码 =================
export interface ForgotPasswordData {
  account: string // 可以是邮箱或手机号
}
export const forgotPassword = (data: ForgotPasswordData) =>
  api.post("/forgot-password", data)

// ================= 重置密码 =================
export interface ResetPasswordData {
  account: string // 邮箱或手机号
  code: string    // 验证码
  new_password: string
}
export const resetPassword = (data: ResetPasswordData) =>
  api.post("/reset-password", data)
