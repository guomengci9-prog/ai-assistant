export interface ChatRecord {
  role: 'user' | 'assistant'
  content: string
}

export interface Assistant {
  id: number
  name: string
  icon: string
  description: string
}
