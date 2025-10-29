import axios from "axios"

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
})

export const getAssistants = () => api.get("/assistants")
export const getAssistantById = (id: number) => api.get(`/assistants/${id}`)
