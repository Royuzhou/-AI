import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getKbStatus } from '@/api/knowledge'

export const useKbStore = defineStore('kb', () => {
  const connected = ref(false)
  const vectors = ref('--')
  const dimension = ref('--')
  const loading = ref(false)

  async function refresh() {
    loading.value = true
    try {
      const d = await getKbStatus()
      connected.value = !!d.connected
      vectors.value = d.total_vectors ?? '--'
      dimension.value = d.dimension ?? '--'
    } catch {
      connected.value = false
    } finally {
      loading.value = false
    }
  }

  return { connected, vectors, dimension, loading, refresh }
})
