import axios from "axios"

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
})

export interface LoginData {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  password: string
  email?: string
}

export const login = (data: LoginData) => api.post("/login", data)
export const register = (data: RegisterData) => api.post("/register", data)
