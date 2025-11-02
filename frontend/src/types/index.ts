export interface ChatRecord {
  role: 'user' | 'assistant'
  content: string
  hideName?: boolean
}

export interface Assistant {
  id: number
  name: string
  icon: string
  description: string
}
