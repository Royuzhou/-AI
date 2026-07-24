<template>
  <div class="chat-page" :class="{ 'split-mode': showRevision }">
    <!-- 左侧: 对话区 -->
    <div class="chat-left">
      <header class="chat-header">
        <h2>{{ currentTitle }}</h2>
        <el-button text @click="newChat">+ 新建对话</el-button>
      </header>

      <div class="message-area">
        <div v-if="store.messages.length === 0" class="empty-state">
          <div class="empty-icon">💬</div>
          <h3>合同修订智能助手</h3>
          <p>上传合同文件或输入法律问题，我将为您提供专业的法律分析和合同修订建议。</p>
          <p class="try-hint">试试这样问：审查合同中的法律风险 · 解释民法典第585条 · 修改违约条款</p>
        </div>
        <ChatMessage v-for="(msg,i) in store.messages" :key="i" :role="msg.role" :content="msg.content" :think="msg.think" :files="msg.files" :streaming="store.streaming && i===store.messages.length-1 && msg.role==='assistant'" />
        <div ref="anchor"></div>
      </div>

      <div v-if="store.streaming" class="thinking-bar">
        <el-progress :percentage="100" :indeterminate="true" :show-text="false" :stroke-width="2" />
        <span>{{ thinkingText }}</span>
      </div>

      <ChatInput @send="handleSend" :disabled="store.streaming" />
    </div>

    <!-- 右侧: 修订面板 -->
    <div v-if="showRevision" class="chat-right">
      <div class="revision-panel">
        <div class="panel-header">
          <h3>📄 合同修订结果</h3>
          <a v-if="currentTaskId" :href="revising ? undefined : '/api/contract/download/'+currentTaskId" :class="['download-btn', { disabled: revising }]" @click.prevent="revising ? null : undefined">⬇ 下载</a>
          <el-button text size="small" @click="closeRevision">✕ 关闭</el-button>
        </div>

        <div v-if="revising" class="panel-loading">
          <el-progress :percentage="100" :indeterminate="true" :show-text="false" />
          <p>正在修订合同，请稍候...</p>
        </div>

        <div v-else class="panel-content">
          <div v-if="revItems.length === 0" class="panel-empty">等待修订结果...</div>
          <div v-for="(item, idx) in revItems" :key="idx" class="rev-item">
            <div class="rev-item-header">#{{ idx + 1 }}</div>
            <div class="revision-block">
              <h4>1. 合同原文</h4>
              <div class="block-text original-text">{{ item.original }}</div>
            </div>
            <div class="revision-block">
              <h4>2. RAG 检索的法律条款原文</h4>
              <div class="block-text law-text">{{ item.lawRef }}</div>
            </div>
            <div class="revision-block">
              <h4>3. 修改建议</h4>
              <div class="block-text suggestion-text">{{ item.suggestion }}</div>
            </div>
            <div class="revision-block">
              <h4>4. 修改后原文</h4>
              <div class="block-text revised-text">{{ item.revised }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatMessage from '@/components/ChatMessage.vue'
import ChatInput from '@/components/ChatInput.vue'
import { sendMessage, loadSessions, loadSession } from '@/api/chat'
import { uploadFile } from '@/api/contract'

const store = useChatStore()
const currentTitle = ref('新对话')
const anchor = ref<HTMLElement>()

const showRevision = ref(false)
const revising = ref(false)
const currentTaskId = ref('')
let revisionTimer: number | null = null

function closeRevision() {
  if (revisionTimer) { clearInterval(revisionTimer); revisionTimer = null }
  showRevision.value = false
  revising.value = false
  currentTaskId.value = ''
}
const revItems = ref<Array<{original:string;lawRef:string;suggestion:string;revised:string}>>([])

const thinkingText = computed(() => {
  if (!store.messages.length) return ''
  const last = store.messages[store.messages.length - 1]
  if (last.role === 'assistant' && !last.content) return '正在思考...'
  if (last.role === 'assistant') return '正在回复...'
  return ''
})

function scrollDown() { nextTick(() => anchor.value?.scrollIntoView({ behavior: 'smooth' })) }
function newChat() { closeRevision(); store.clearMessages(); currentTitle.value = '新对话'; revItems.value = [] }

function parseRevision(text: string) {
  revItems.value = []
  const blocks = text.split('§CHANGE')
  for (const block of blocks) {
    const o = block.match(/§ORIGINAL\s*([\s\S]*?)(?=§LAW|§END|$)/)
    const l = block.match(/§LAW\s*([\s\S]*?)(?=§SUGGESTION|§END|$)/)
    const s = block.match(/§SUGGESTION\s*([\s\S]*?)(?=§REVISED|§END|$)/)
    const r = block.match(/§REVISED\s*([\s\S]*?)(?=§END|$)/)
    if (o && l && s && r) {
      revItems.value.push({ original: o[1].trim(), lawRef: l[1].trim(), suggestion: s[1].trim(), revised: r[1].trim() })
    }
  }
  // fallback: Chinese markers
  if (revItems.value.length === 0) {
    const cm = text.match(/【合同内原文】\s*([\s\S]*?)(?=【匹配的法律原文】|$)/)
    const lm = text.match(/【匹配的法律原文】\s*([\s\S]*?)(?=【合同修改建议】|$)/)
    const sm = text.match(/【合同修改建议】\s*([\s\S]*?)$/)
    if (cm || lm || sm) {
      revItems.value.push({ original: cm?.[1]?.trim()||'', lawRef: lm?.[1]?.trim()||'', suggestion: sm?.[1]?.trim()||'', revised: '' })
    }
  }
}

async function handleSend(text: string, file?: File) {
  let filePath = '', fileName = ''
  if (file) {
    const up = await uploadFile(file)
    if (!up.success) { store.addMessage({ role:'system', content:'文件上传失败: '+up.error }); return }
    filePath = up.path || ''; fileName = file.name
  }
  store.addMessage({ role:'user', content: text, files: fileName?[fileName]:[] })
  scrollDown()

  const revKw = ['修订','审查合同','修改合同','审阅合同','帮我修订','合同修订']
  if (revKw.some(k=>text.includes(k)) && filePath) {
    showRevision.value = true; revising.value = true; revItems.value = []
    store.addMessage({ role:'system', content:'正在启动合同修订流程...' })
    try {
      const resp = await fetch('/api/contract/revise', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({filepath:filePath}) })
      const raw = await resp.text()
      let data: any = {}
      try { data = JSON.parse(raw) } catch { data = { success:false, error:'Server response: '+raw.substring(0,200) } }
      if (data.success) { pollRevision(data.task_id) }
      else { store.addMessage({ role:'system', content:'修订启动失败: '+(data.error||'unknown') }); revising.value = false }
    } catch (e: any) { store.addMessage({ role:'system', content:'网络错误: '+e.message }); revising.value = false }
    return
  }

  await sendMessage(text, filePath?[filePath]:[], ()=>{ currentTitle.value = text.substring(0,30)||'对话' }, (err)=>{ store.addMessage({ role:'system', content:'错误: '+err }) })
  scrollDown()
}

function pollRevision(taskId: string) {
  let count = 0
  const maxPolls = 40
  revisionTimer = setInterval(async () => {
    count++
    try {
      const resp = await fetch('/api/contract/status/'+taskId)
      const data = await resp.json()
      if (data.status === 'completed') { clearInterval(revisionTimer!); revisionTimer = null; revising.value = false; parseRevision(data.result||''); store.addMessage({ role:'assistant', content:'合同修订已完成，请查看右侧面板。' }) }
      else if (data.status === 'failed') { clearInterval(revisionTimer!); revisionTimer = null; revising.value = false; store.addMessage({ role:'system', content:'修订失败: '+(data.error||'') }) }
      else if (count >= maxPolls) { clearInterval(revisionTimer!); revisionTimer = null; revising.value = false; store.addMessage({ role:'system', content:'修订超时，请重试。' }) }
    } catch { clearInterval(revisionTimer!); revisionTimer = null; revising.value = false }
  }, 3000)
}

onMounted(async () => {
  const sessions = await loadSessions()
  if (sessions.length > 0) { const s = await loadSession(sessions[0].id); if (s?.messages) { store.messages = s.messages; store.currentChatId = s.id; currentTitle.value = s.title||'对话' } }
})
</script>

<style scoped>
.chat-page { display:flex; height:100vh; }
.chat-left { flex:1; display:flex; flex-direction:column; min-width:0; }
.chat-header { display:flex; justify-content:space-between; align-items:center; padding:14px 24px; background:var(--bg-white); border-bottom:1px solid var(--border-color); }
.chat-header h2 { font-size:16px; font-weight:600; }
.message-area { flex:1; overflow-y:auto; padding:20px 0; }
.empty-state { text-align:center; padding:80px 20px; color:var(--text-secondary); }
.empty-icon { font-size:48px; margin-bottom:16px; }
.empty-state h3 { font-size:18px; margin-bottom:8px; color:var(--text-primary); }
.empty-state p { font-size:14px; max-width:420px; margin:0 auto; }
.try-hint { font-size:13px; color:#9ca3af; margin-top:8px; }
.thinking-bar { padding:8px 24px; background:var(--bg-white); border-top:1px solid var(--border-color); display:flex; align-items:center; gap:12px; }
.thinking-bar span { font-size:13px; color:var(--accent); white-space:nowrap; }
.split-mode .chat-left { border-right:1px solid var(--border-color); }
.chat-right { width:420px; display:flex; flex-direction:column; background:var(--bg-white); overflow-y:auto; }
.revision-panel { flex:1; display:flex; flex-direction:column; }
.panel-header { display:flex; justify-content:space-between; align-items:center; padding:14px 16px; border-bottom:1px solid var(--border-color); position:sticky; top:0; background:var(--bg-white); z-index:2; }
.panel-header h3 { font-size:15px; font-weight:600; margin:0; }
.download-btn { font-size:13px; color:var(--accent); text-decoration:none; padding:4px 12px; border:1px solid var(--accent); border-radius:4px; margin-right:8px; }
.download-btn:hover { background:var(--accent); color:#fff; }
.download-btn.disabled { opacity:0.4; pointer-events:none; }
.panel-loading { text-align:center; padding:40px 20px; color:var(--text-secondary); }
.panel-loading p { margin-top:12px; font-size:13px; }
.panel-content { padding:16px; }
.panel-empty { text-align:center; padding:40px; color:var(--text-secondary); font-size:13px; }
.rev-item { margin-bottom:24px; padding-bottom:16px; border-bottom:2px solid var(--border-color); }
.rev-item:last-child { border-bottom:none; }
.rev-item-header { font-size:13px; font-weight:700; color:var(--accent); margin-bottom:12px; background:#eef2ff; padding:4px 10px; border-radius:4px; display:inline-block; }
.revision-block { margin-bottom:10px; }
.revision-block h4 { font-size:12px; font-weight:600; margin-bottom:4px; color:var(--text-primary); }
.block-text { font-size:13px; line-height:1.7; padding:8px 10px; border-radius:6px; white-space:pre-wrap; max-height:200px; overflow-y:auto; }
.original-text { background:#fef2f2; color:#991b1b; border:1px solid #fecaca; }
.law-text { background:#f5f3ff; color:#5b21b6; border:1px solid #ddd6fe; }
.suggestion-text { background:#fffbeb; color:#92400e; border:1px solid #fde68a; }
.revised-text { background:#f0fdf4; color:#166534; border:1px solid #bbf7d0; }
</style>
