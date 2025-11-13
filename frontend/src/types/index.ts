export interface ChatAttachment {
  id: string
  filename: string
  url: string
  content_type?: string
  size?: number
  uploaded_at?: number
}

export interface ChatRecord {
  role: 'user' | 'assistant'
  content: string
  hideName?: boolean
  message_type?: 'text' | 'attachment' | 'opening'
  attachments?: ChatAttachment[]
}

export interface Assistant {
  id: number
  name: string
  icon: string
  description: string
  prompt_content?: string
  system_prompt?: string
  scene_prompt?: string
  user_prefill?: string
  opening_message?: string
  defaultPrompt?: string
  model_parameters?: Record<string, unknown>
  knowledge_ids?: number[]
  update_time?: string
}
