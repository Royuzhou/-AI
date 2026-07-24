import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  think?: string
  files?: string[]
}

export interface ChatSession {
  id: string
  title: string
  created_at: string
  message_count: number
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const streaming = ref(false)
  const currentChatId = ref<string>('')
  const sessions = ref<ChatSession[]>([])

  const lastUserMessage = computed(() => {
    for (let i = messages.value.length - 1; i >= 0; i--) {
      if (messages.value[i].role === 'user') return messages.value[i]
    }
    return null
  })

  function addMessage(msg: ChatMessage) {
    messages.value.push(msg)
  }

  function ensureAssistant() {
    const last = messages.value[messages.value.length - 1]
    if (!last || last.role !== 'assistant') {
      messages.value.push({ role: 'assistant', content: '', think: '' })
    }
  }

  function appendThink(text: string) {
    ensureAssistant()
    const last = messages.value[messages.value.length - 1]
    if (last.role === 'assistant') {
      last.think = (last.think || '') + text
    }
  }

  function appendAnswer(text: string) {
    ensureAssistant()
    const last = messages.value[messages.value.length - 1]
    if (last.role === 'assistant') {
      last.content += text
    }
  }

  function clearMessages() {
    messages.value = []
    currentChatId.value = ''
  }

  function setSessions(list: ChatSession[]) {
    sessions.value = list
  }

  return {
    messages, streaming, currentChatId, sessions,
    lastUserMessage, addMessage, ensureAssistant,
    appendThink, appendAnswer, clearMessages, setSessions,
  }
})
