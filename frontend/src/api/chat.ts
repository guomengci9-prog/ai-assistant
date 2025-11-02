import axios from "axios"

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
})

export interface ChatRecord {
  role: string
  content: string
}

//export const getHistory = (assistant_id: number) =>
  //api.get(`/chat/history/${assistant_id}`)

export const getHistory = (assistantId: number, conversationId: number) =>
  api.get(`/history/${assistantId}`, {
    params: { conversationId }
  })


export const sendMessage = (assistant_id: number, msg: string) =>
  api.post(`/chat/${assistant_id}`, { role: "user", content: msg })
