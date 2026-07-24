<template>
  <div class="revision-page">
    <header class="revision-header">
      <div class="h-left">
        <el-button text @click="$router.push('/')">← 返回对话</el-button>
        <el-tag v-if="status === 'processing'" type="warning">处理中</el-tag>
        <el-tag v-else-if="status === 'completed'" type="success">已完成</el-tag>
        <el-tag v-else-if="status === 'failed'" type="danger">失败</el-tag>
      </div>
      <el-button v-if="status === 'completed'" type="primary" @click="sendToChat">发送到对话</el-button>
    </header>

    <div class="revision-body">
      <div v-if="status === 'processing'" class="loading-state">
        <el-icon class="is-loading" :size="36"><Loading /></el-icon>
        <p>合同修订进行中，请稍候...</p>
      </div>
      <div v-else-if="status === 'failed'" class="error-state">
        <p>{{ error }}</p>
        <el-button @click="$router.push('/')">返回对话</el-button>
      </div>
      <div v-else-if="status === 'completed'">
        <section v-if="revisedContract" class="content-section">
          <h2>📄 修订后的完整合同</h2>
          <DiffView v-for="(e, i) in edits" :key="i" :label="e.position" :original="e.original" :revised="e.revised" />
          <div v-if="edits.length === 0" class="full-text"><pre>{{ revisedContract }}</pre></div>
        </section>
        <section v-if="suggestions.length" class="content-section">
          <h2>📋 修改建议清单</h2>
          <SuggestionList :suggestions="suggestions" />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { getRevisionStatus } from '@/api/contract'
import { injectRevisionContext } from '@/api/chat'
import { useChatStore } from '@/stores/chat'
import DiffView from '@/components/DiffView.vue'
import SuggestionList from '@/components/SuggestionList.vue'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const taskId = route.params.taskId as string
const status = ref('processing')
const error = ref('')
const result = ref('')
const revisedContract = ref('')
const edits = ref<Array<{ position: string; original: string; revised: string }>>([])
const suggestions = ref<Array<any>>([])
let timer: number | null = null

function parse(text: string) {
  // 提取完整合同
  const cm = text.match(/【修订后的完整合同】\s*([\s\S]*?)(?=【修改建议清单】|$)/)
  if (cm) revisedContract.value = cm[1].trim()

  // 提取修改建议清单——按 §CHANGE 分割
  const sm = text.match(/【修改建议清单】\s*([\s\S]*)$/)
  if (sm) {
    const blocks = sm[1].split('§CHANGE').filter((s: string) => s.trim())
    for (const block of blocks) {
      const origMatch = block.match(/§ORIGINAL\s*([\s\S]*?)(?=§LAW|$)/)
      const lawMatch = block.match(/§LAW\s*([\s\S]*?)(?=§SUGGESTION|$)/)
      const sugMatch = block.match(/§SUGGESTION\s*([\s\S]*?)(?=§REVISED|$)/)
      const revMatch = block.match(/§REVISED\s*([\s\S]*?)(?=§END|$)/)

      edits.value.push({
        position: '修订条目 ' + (edits.value.length + 1),
        original: origMatch ? origMatch[1].trim() : '',
        revised: revMatch ? revMatch[1].trim() : '',
      })

      suggestions.value.push({
        position: '第' + (suggestions.value.length + 1) + '条',
        original: origMatch ? origMatch[1].trim().substring(0, 300) : '',
        revised_to: revMatch ? revMatch[1].trim().substring(0, 300) : '',
        reason: (sugMatch ? sugMatch[1].trim() : '').substring(0, 300),
        law_basis: lawMatch ? lawMatch[1].trim().substring(0, 500) : '',
        risk: '',
      })
    }
  }
}


async function poll() {
  try {
    const d = await getRevisionStatus(taskId)
    status.value = d.status
    if (d.status === 'completed') { result.value = d.result || ''; parse(d.result || ''); stop() }
    else if (d.status === 'failed') { error.value = d.error || '修订失败'; stop() }
  } catch (e: any) { error.value = e.message; stop() }
}
function start() { poll(); timer = window.setInterval(poll, 3000) }
function stop() { if (timer) { clearInterval(timer); timer = null } }

async function sendToChat() {
  if (!result.value) return
  await injectRevisionContext(chatStore.currentChatId, result.value)
  router.push('/')
}

onMounted(start)
onUnmounted(stop)
</script>

<style scoped>
.revision-page { display: flex; flex-direction: column; height: 100vh; }
.revision-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 24px; background: var(--bg-white); border-bottom: 1px solid var(--border-color); }
.h-left { display: flex; align-items: center; gap: 12px; }
.revision-body { flex: 1; overflow-y: auto; padding: 24px; max-width: 900px; margin: 0 auto; width: 100%; }
.loading-state { text-align: center; padding: 80px 20px; color: var(--text-secondary); }
.loading-state p { margin-top: 16px; }
.error-state { text-align: center; padding: 80px 20px; }
.error-state p { color: var(--danger); margin-bottom: 16px; }
.content-section { margin-bottom: 32px; }
.content-section h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.full-text pre { white-space: pre-wrap; font-family: inherit; font-size: 14px; line-height: 1.8; background: var(--bg-white); padding: 20px; border-radius: var(--radius); border: 1px solid var(--border-color); }
</style>
