<template>
  <div class="history-page">
    <header class="page-header"><h2>📋 历史记录</h2></header>
    <div class="history-body">
      <el-table v-if="sessions.length" :data="sessions" style="width:100%" @row-click="openSession">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="message_count" label="消息数" width="100" />
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click.stop="openSession(row)">查看</el-button>
            <el-button size="small" text type="danger" @click.stop="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-else class="empty-state">暂无历史记录</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import { loadSessions, loadSession, deleteSession } from '@/api/chat'

const router = useRouter()
const store = useChatStore()
const sessions = ref<any[]>([])

function formatDate(d: string) { return d ? d.substring(0, 16).replace('T', ' ') : '' }

async function openSession(row: any) {
  const s = await loadSession(row.id)
  if (s?.messages) {
    store.messages = s.messages
    store.currentChatId = s.id
    router.push('/')
  }
}

async function confirmDelete(row: any) {
  try {
    await ElMessageBox.confirm('确定要删除这条对话记录吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteSession(row.id)
    ElMessage.success('已删除')
    sessions.value = await loadSessions()
  } catch { /* 用户取消 */ }
}

onMounted(async () => { sessions.value = await loadSessions() })
</script>

<style scoped>
.history-page { display: flex; flex-direction: column; height: 100vh; }
.page-header { padding: 14px 24px; background: var(--bg-white); border-bottom: 1px solid var(--border-color); }
.page-header h2 { font-size: 16px; font-weight: 600; }
.history-body { flex: 1; padding: 20px; overflow-y: auto; }
.empty-state { text-align: center; padding: 60px; color: var(--text-secondary); }
</style>
