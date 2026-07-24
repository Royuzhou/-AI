<template>
  <div class="message-wrapper" :class="role">
    <div class="message-bubble">
      <details v-if="think" class="think-section" :open="streaming && think.length > 0">
        <summary>🧠 思考过程</summary>
        <div class="think-content">{{ think }}</div>
      </details>
      <div v-if="content" class="message-content" v-html="renderedContent"></div>
      <div v-if="files && files.length" class="message-files">
        <span v-for="f in files" :key="f" class="file-chip">↑ {{ f }}</span>
      </div>
      <div class="message-meta">
        <span class="role-label">{{ role === 'user' ? '我' : 'AI 助手' }}</span>
        <span v-if="streaming" class="streaming-dot">●</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  role: 'user' | 'assistant' | 'system'
  content: string
  think?: string
  files?: string[]
  streaming?: boolean
}>()

function simpleMarkdown(text: string): string {
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>')
  return html
}

const renderedContent = computed(() => simpleMarkdown(props.content))
</script>

<style scoped>
.message-wrapper { display: flex; margin-bottom: 16px; padding: 0 16px; }
.message-wrapper.user { justify-content: flex-end; }
.message-wrapper.assistant { justify-content: flex-start; }
.message-wrapper.system { justify-content: center; }
.message-bubble {
  max-width: 75%; padding: 12px 16px; border-radius: 12px;
  font-size: 14px; line-height: 1.7;
}
.user .message-bubble { background: var(--accent); color: #fff; border-bottom-right-radius: 4px; }
.assistant .message-bubble {
  background: var(--bg-white); border: 1px solid var(--border-color);
  border-bottom-left-radius: 4px; box-shadow: var(--shadow);
}
.system .message-bubble {
  background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534;
  font-size: 13px; max-width: 90%;
}
.think-section {
  margin-bottom: 10px; padding: 8px 12px;
  background: #f8fafc; border-radius: 6px;
  border-left: 3px solid #94a3b8;
}
.think-section summary {
  font-size: 12px; color: #64748b; cursor: pointer;
  user-select: none;
}
.think-content {
  margin-top: 6px; font-size: 13px; color: #64748b;
  white-space: pre-wrap; line-height: 1.6;
  max-height: 200px; overflow-y: auto;
}
.message-content :deep(.code-block) {
  background: rgba(0,0,0,0.06); padding: 10px 14px; border-radius: 6px;
  font-size: 13px; margin: 8px 0; overflow-x: auto;
}
.message-content :deep(.inline-code) {
  background: rgba(0,0,0,0.06); padding: 1px 6px; border-radius: 4px; font-size: 13px;
}
.user .message-content :deep(.code-block), .user .message-content :deep(.inline-code) {
  background: rgba(255,255,255,0.15);
}
.message-content :deep(h2), .message-content :deep(h3), .message-content :deep(h4) {
  margin: 8px 0 4px; font-weight: 600;
}
.message-content :deep(li) { margin-left: 16px; }
.message-files { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
.file-chip {
  font-size: 12px; padding: 2px 10px; border-radius: 12px; background: rgba(0,0,0,0.06);
}
.user .file-chip { background: rgba(255,255,255,0.2); }
.message-meta {
  margin-top: 6px; font-size: 11px; opacity: 0.6;
  display: flex; align-items: center; gap: 6px;
}
.streaming-dot { color: var(--success); animation: pulse 1s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
</style>
