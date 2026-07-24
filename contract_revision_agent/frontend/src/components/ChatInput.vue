<template>
  <div
    class="chat-input-wrapper"
    @dragover.prevent="dragover = true"
    @dragleave="dragover = false"
    @drop.prevent="handleDrop"
    :class="{ dragover }"
  >
    <div v-if="dragover" class="drop-overlay">
      <span>📂 释放文件以上传</span>
    </div>

    <div v-if="attachedFile" class="attached-file">
      <span>↑ {{ attachedFile.name }}</span>
      <button class="remove-file" @click="clearFile">✕</button>
    </div>

    <div class="input-row">
      <label class="attach-btn" title="上传文件">
        ↑
        <input type="file" hidden @change="handleFileSelect" accept=".pdf,.docx,.txt" :disabled="props.disabled" />
      </label>
      <textarea
        ref="textarea"
        v-model="text"
        class="message-input"
        :placeholder="props.disabled ? 'AI 正在回复...' : '输入消息, 或拖拽合同文件到此处...'"
        rows="1"
        :disabled="props.disabled"
        @keydown.enter.exact="handleSend"
        @input="autoGrow"
      ></textarea>
      <button
        class="send-btn"
        :disabled="!canSend"
        @click="handleSend"
      >
        发送
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ disabled?: boolean }>()

const emit = defineEmits<{
  send: [text: string, file?: File]
}>()

const text = ref('')
const dragover = ref(false)
const attachedFile = ref<File | null>(null)
const textarea = ref<HTMLTextAreaElement>()

const canSend = computed(() => !props.disabled && !!(text.value.trim() || attachedFile.value))

function autoGrow() {
  const el = textarea.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 150) + 'px'
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) attachedFile.value = input.files[0]
}

function handleDrop(e: DragEvent) {
  dragover.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) attachedFile.value = file
}

function clearFile() { attachedFile.value = null }

function handleSend(e?: Event) {
  if (e instanceof KeyboardEvent && e.shiftKey) return
  e?.preventDefault()
  if (!canSend.value) return
  emit('send', text.value.trim(), attachedFile.value || undefined)
  text.value = ''
  attachedFile.value = null
  if (textarea.value) { textarea.value.style.height = 'auto' }
}
</script>

<style scoped>
.chat-input-wrapper {
  position: relative;
  border-top: 1px solid var(--border-color);
  background: var(--bg-white);
  padding: 12px 16px;
}
.chat-input-wrapper.dragover {
  background: #eef2ff;
}
.drop-overlay {
  position: absolute;
  inset: 0;
  background: rgba(102,126,234,0.08);
  border: 2px dashed var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: var(--accent);
  border-radius: 8px;
  z-index: 10;
}
.attached-file {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  padding: 4px 10px;
  margin-bottom: 8px;
  background: #f0f4ff;
  border-radius: 6px;
  width: fit-content;
}
.remove-file {
  background: none; border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
}
.input-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}
.attach-btn {
  cursor: pointer;
  font-size: 18px;
  font-weight: 700;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f0f4ff;
  color: var(--accent);
  transition: all 0.15s;
}
.attach-btn:hover { background: var(--accent); color: #fff; }
.message-input {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
  padding: 8px 0;
  max-height: 150px;
  font-family: inherit;
}
.message-input::placeholder { color: #c0c4cc; }
.send-btn {
  padding: 8px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}
.send-btn:hover:not(:disabled) { background: var(--accent-light); }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
