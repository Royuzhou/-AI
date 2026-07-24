import { useChatStore } from '@/stores/chat'

export async function sendMessage(
  text: string,
  files: string[] = [],
  onDone: (chatId: string) => void,
  onError: (err: string) => void,
) {
  const store = useChatStore()
  store.streaming = true
  store.ensureAssistant()

  try {
    const resp = await fetch('/api/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, files, chat_id: store.currentChatId || undefined }),
    })

    const reader = resp.body?.getReader()
    if (!reader) { onError('no stream'); return }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'tool_call') {
            store.addMessage({ role: 'system', content: `[调用工具: ${data.name}...]` })
          } else if (data.type === 'tool_result') {
            store.addMessage({ role: 'system', content: `[工具 ${data.name} 返回: ${data.text}]` })
          } else if (data.token) {
            store.appendAnswer(data.token)
          }
          if (data.done) {
            store.currentChatId = data.chat_id
            onDone(data.chat_id)
          }
          if (data.error) onError(data.error)
        } catch { /* skip */ }
      }
    }
  } catch (e: any) {
    onError(e.message || 'error')
  } finally {
    store.streaming = false
  }
}

export async function loadSessions() {
  try { const r = await fetch('/api/chat/list'); return await r.json() } catch { return [] }
}

export async function loadSession(chatId: string) {
  try { const r = await fetch(`/api/chat/${chatId}`); return await r.json() } catch { return null }
}

export async function deleteSession(chatId: string) {
  await fetch(`/api/chat/${chatId}`, { method: 'DELETE' })
}

export async function injectRevisionContext(chatId: string, revisionText: string) {
  const r = await fetch('/api/chat/context', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, revision_text: revisionText }),
  })
  return await r.json()
}
