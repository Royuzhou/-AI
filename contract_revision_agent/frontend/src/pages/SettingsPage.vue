<template>
  <div class="settings-page">
    <header class="page-header"><h2>⚙️ 系统设置</h2></header>
    <div class="settings-body">
      <el-tabs>
        <el-tab-pane label="🤖 DeepSeek API">
          <el-form label-width="100px">
            <el-form-item label="API Key">
              <el-input v-model="store.deepseekKey" type="password" show-password placeholder="sk-..." />
            </el-form-item>
            <el-form-item label="Base URL">
              <el-input v-model="store.deepseekUrl" />
            </el-form-item>
            <el-form-item label="Model">
              <el-input v-model="store.deepseekModel" />
            </el-form-item>
            <el-form-item>
              <el-button @click="testDS" :loading="dsTesting">测试连接</el-button>
              <el-button type="primary" @click="saveDS">保存</el-button>
              <span v-if="dsResult" :class="dsResult.connected ? 'text-success' : 'text-danger'" style="margin-left:12px;font-size:13px">
                {{ dsResult.connected ? '连接成功' : dsResult.error }}
              </span>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="🗄️ Pinecone">
          <el-form label-width="100px">
            <el-form-item label="API Key">
              <el-input v-model="store.pineconeKey" type="password" show-password placeholder="pcsk_..." />
            </el-form-item>
            <el-form-item label="Index">
              <el-input v-model="store.pineconeIndex" />
            </el-form-item>
            <el-form-item label="Top K">
              <el-input-number v-model="store.pineconeTopK" :min="1" :max="20" />
            </el-form-item>
            <el-form-item>
              <el-button @click="testPC" :loading="pcTesting">测试连接</el-button>
              <el-button type="primary" @click="savePC">保存</el-button>
              <span v-if="pcResult" :class="pcResult.connected ? 'text-success' : 'text-danger'" style="margin-left:12px;font-size:13px">
                {{ pcResult.connected ? '连接成功' : pcResult.error }}
              </span>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useConfigStore } from '@/stores/config'

const store = useConfigStore()
const dsTesting = ref(false)
const pcTesting = ref(false)
const dsResult = ref<any>(null)
const pcResult = ref<any>(null)

async function testDS() { dsTesting.value = true; dsResult.value = await store.testDeepSeek(); dsTesting.value = false }
async function saveDS() {
  const ok = await store.saveDeepSeek()
  ElMessage({ message: ok ? 'DeepSeek 配置已保存' : '保存失败', type: ok ? 'success' : 'error' })
}
async function testPC() { pcTesting.value = true; pcResult.value = await store.testPinecone(); pcTesting.value = false }
async function savePC() {
  const ok = await store.savePinecone()
  ElMessage({ message: ok ? 'Pinecone 配置已保存' : '保存失败', type: ok ? 'success' : 'error' })
}

onMounted(() => store.loadConfig())
</script>

<style scoped>
.settings-page { display: flex; flex-direction: column; height: 100vh; }
.page-header { padding: 14px 24px; background: var(--bg-white); border-bottom: 1px solid var(--border-color); }
.page-header h2 { font-size: 16px; font-weight: 600; }
.settings-body { flex: 1; padding: 20px; overflow-y: auto; max-width: 600px; }
.text-success { color: var(--success); }
.text-danger { color: var(--danger); }
</style>
