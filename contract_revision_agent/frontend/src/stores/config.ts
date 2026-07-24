import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useConfigStore = defineStore('config', () => {
  const deepseekKey = ref('')
  const deepseekUrl = ref('https://api.deepseek.com/v1')
  const deepseekModel = ref('deepseek-chat')
  const pineconeKey = ref('')
  const pineconeIndex = ref('software')
  const pineconeTopK = ref(3)
  const loading = ref(false)

  async function loadConfig() {
    try {
      const resp = await fetch('/api/config')
      const data = await resp.json()
      if (data.deepseek) {
        deepseekKey.value = data.deepseek.api_key || ''
        deepseekUrl.value = data.deepseek.base_url || 'https://api.deepseek.com/v1'
        deepseekModel.value = data.deepseek.model || 'deepseek-chat'
      }
      if (data.pinecone) {
        pineconeKey.value = data.pinecone.api_key || ''
        pineconeIndex.value = data.pinecone.index_name || 'software'
        pineconeTopK.value = data.pinecone.top_k || 3
      }
    } catch { /* ignore */ }
  }

  async function testDeepSeek(): Promise<{ connected: boolean; error?: string }> {
    try {
      const resp = await fetch('/api/config/test/deepseek', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: deepseekKey.value, base_url: deepseekUrl.value, model: deepseekModel.value }),
      })
      return await resp.json()
    } catch (e: any) {
      return { connected: false, error: e.message }
    }
  }

  async function saveDeepSeek(): Promise<boolean> {
    try {
      const resp = await fetch('/api/config/deepseek', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: deepseekKey.value, base_url: deepseekUrl.value, model: deepseekModel.value }),
      })
      const data = await resp.json()
      return data.success === true
    } catch { return false }
  }

  async function testPinecone(): Promise<{ connected: boolean; error?: string }> {
    try {
      const resp = await fetch('/api/config/test/pinecone', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: pineconeKey.value }),
      })
      return await resp.json()
    } catch (e: any) {
      return { connected: false, error: e.message }
    }
  }

  async function savePinecone(): Promise<boolean> {
    try {
      const resp = await fetch('/api/config/pinecone', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: pineconeKey.value, index_name: pineconeIndex.value, top_k: pineconeTopK.value }),
      })
      const data = await resp.json()
      return data.success === true
    } catch { return false }
  }

  return {
    deepseekKey, deepseekUrl, deepseekModel,
    pineconeKey, pineconeIndex, pineconeTopK,
    loading, loadConfig, testDeepSeek, saveDeepSeek, testPinecone, savePinecone,
  }
})
