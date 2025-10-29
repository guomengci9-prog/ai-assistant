import axios from 'axios'
axios.defaults.baseURL = 'http://127.0.0.1:8000/api'

export const register = (username: string, password: string, email?: string) =>
  axios.post('/register', { username, password, email })

export const login = (username: string, password: string) =>
  axios.post('/login', { username, password })

export const getAssistants = () => axios.get('/assistants')
export const getAssistantById = (id: number) => axios.get(`/assistants/${id}`)

export const sendMessage = (assistantId: number, message: string) =>
  axios.post(`/chat/${assistantId}`, { assistant_id: assistantId, message })

export const getHistory = (assistantId: number) =>
  axios.get(`/chat/history/${assistantId}`)
