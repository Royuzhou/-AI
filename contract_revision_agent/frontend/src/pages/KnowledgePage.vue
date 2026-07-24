<template>
  <div class="kb-page">
    <header class="page-header">
      <h2>📚 法律知识库</h2>
      <div class="kb-stats">
        <span class="stat">向量: <strong>{{ kbStore.loading ? '...' : kbStore.vectors }}</strong></span>
        <span class="stat">维度: <strong>{{ kbStore.loading ? '...' : kbStore.dimension }}</strong></span>
        <span class="stat">
          状态:
          <strong v-if="kbStore.loading" class="text-warning">连接中...</strong>
          <strong v-else :class="kbStore.connected ? 'text-success' : 'text-danger'">{{ kbStore.connected ? '已连接' : '未连接' }}</strong>
        </span>
      </div>
    </header>

    <div class="kb-content">
      <div class="kb-left">
        <el-card header="上传文档">
          <el-upload drag :auto-upload="false" :on-change="onFileChange" :limit="1" accept=".pdf,.docx,.txt">
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处或点击上传</div>
            <template #tip><div class="el-upload__tip">支持 .pdf / .docx / .txt</div></template>
          </el-upload>
          <div v-if="kbFile" class="file-info">
            <span>📎 {{ kbFile.name }}</span>
            <el-input-number v-model="chunkSize" :min="100" :max="2000" size="small" style="width:140px" />
          </div>
          <el-button v-if="kbFile" type="primary" :loading="processing" @click="processDoc" style="width:100%;margin-top:12px">
            处理并入库
          </el-button>
          <div v-if="processResult" :class="processResult.success ? 'text-success' : 'text-danger'" style="margin-top:12px;font-size:13px">
            {{ processResult.success ? `入库成功! 分块: ${processResult.chunks}, 向量: ${processResult.vectors}` : processResult.error }}
          </div>
        </el-card>
      </div>

      <div class="kb-right">
        <el-card header="知识库搜索">
          <el-input v-model="searchQuery" placeholder="输入法律条款关键词..." @keyup.enter="doSearch">
            <template #append><el-button @click="doSearch">搜索</el-button></template>
          </el-input>
          <div class="search-results">
            <div v-if="searching" class="search-loading">
              <el-progress :percentage="100" :indeterminate="true" :show-text="false" />
              <span>搜索中...</span>
            </div>
            <div v-else-if="searchResults.length === 0" class="text-muted" style="padding:20px;text-align:center">
              {{ searchQuery ? '未找到匹配结果' : '输入关键词搜索' }}
            </div>
            <div v-if="!searching && searchResults.length > 0" class="result-count">
              找到 {{ searchResults.length }} 条结果
            </div>
            <div v-for="(r, i) in searchResults" :key="i" class="result-item">
              <div class="result-header">
                <span class="result-score">#{{ i + 1 }} 相似度: {{ r.score }}</span>
                <span class="result-source">来源: {{ r.source || r.id }}</span>
              </div>
              <p class="result-text">{{ r.text }}</p>
              <details class="result-meta">
                <summary>查看完整 metadata</summary>
                <pre>{{ JSON.stringify(r.metadata, null, 2) }}</pre>
              </details>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadKbFile, processDocument, searchKnowledge } from '@/api/knowledge'
import { useKbStore } from '@/stores/kb'

const kbStore = useKbStore()
const kbFile = ref<File | null>(null)
const chunkSize = ref(500)
const processing = ref(false)
const processResult = ref<any>(null)
const searchQuery = ref('')
const searchResults = ref<any[]>([])
const searching = ref(false)

function onFileChange(_file: any, fileList: any) {
  const files = fileList.map((f:any) => f.raw).filter(Boolean)
  kbFile.value = files[0] || null
  processResult.value = null
}

async function processDoc() {
  if (!kbFile.value) return
  processing.value = true; processResult.value = null
  try {
    const up = await uploadKbFile(kbFile.value)
    if (!up.success) { processResult.value = { success: false, error: up.error }; return }
    const res = await processDocument(up.path, chunkSize.value)
    processResult.value = res
    if (res.success) kbStore.refresh()
  } catch (e: any) {
    processResult.value = { success: false, error: e.message }
  } finally { processing.value = false }
}

async function doSearch() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  searchResults.value = []
  try {
    const data = await searchKnowledge(searchQuery.value.trim())
    searchResults.value = data.results || []
  } catch { searchResults.value = [] }
  finally { searching.value = false }
}

onMounted(() => {})
</script>

<style scoped>
.kb-page { display: flex; flex-direction: column; height: 100vh; }
.page-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 24px; background: var(--bg-white); border-bottom: 1px solid var(--border-color); }
.page-header h2 { font-size: 16px; font-weight: 600; }
.kb-stats { display: flex; gap: 20px; font-size: 13px; }
.stat strong { margin-left: 4px; }
.text-success { color: var(--success); }
.text-danger { color: var(--danger); }
.kb-content { display: grid; grid-template-columns: 380px 1fr; gap: 20px; padding: 20px; flex: 1; overflow: hidden; }
.kb-left { overflow-y: auto; }
.kb-right { overflow-y: auto; }
.file-info { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; font-size: 13px; }
.search-results { margin-top: 16px; }
.result-item { padding: 12px; border-bottom: 1px solid var(--border-color); }
.result-header { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; }
.result-text { font-size: 13px; line-height: 1.6; color: var(--text-primary); }
.text-muted { color: var(--text-secondary); }
.text-warning { color: var(--warning); }
.result-count { font-size: 12px; color: var(--text-secondary); padding: 8px 0; border-bottom: 1px solid var(--border-color); }
.result-meta { margin-top: 8px; }
.result-meta summary { font-size: 12px; color: var(--accent); cursor: pointer; }
.result-meta pre { font-size: 11px; background: #f9fafb; padding: 8px; border-radius: 4px; overflow-x: auto; max-height: 200px; }
.search-loading { text-align: center; padding: 20px; }
.search-loading span { display: block; margin-top: 8px; font-size: 13px; color: var(--text-secondary); }
</style>
