<template>
  <div class="suggestion-list">
    <div v-for="(s, i) in suggestions" :key="i" class="suggestion-item">
      <div class="suggestion-header">
        <span class="suggestion-number">#{{ i + 1 }}</span>
        <span class="suggestion-position">{{ s.position }}</span>
      </div>
      <div class="suggestion-body">
        <div class="field">
          <span class="field-label">原文</span>
          <span class="field-value original-text">{{ s.original }}</span>
        </div>
        <div class="field">
          <span class="field-label">修改为</span>
          <span class="field-value revised-text">{{ s.revised_to }}</span>
        </div>
        <div class="field">
          <span class="field-label">法律依据</span>
          <span class="field-value law-text">{{ s.law_basis }}</span>
        </div>
        <div v-if="s.reason" class="field">
          <span class="field-label">修改原因</span>
          <span class="field-value">{{ s.reason }}</span>
        </div>
        <div v-if="s.risk" class="field">
          <span class="field-label">风险评估</span>
          <span class="field-value risk-text">{{ s.risk }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  suggestions: Array<{
    position: string
    original: string
    revised_to: string
    reason: string
    law_basis: string
    risk: string
  }>
}>()
</script>

<style scoped>
.suggestion-list { display: flex; flex-direction: column; gap: 12px; }
.suggestion-item {
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow);
}
.suggestion-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: #f9fafb;
  border-bottom: 1px solid var(--border-color);
}
.suggestion-number {
  font-size: 13px;
  font-weight: 700;
  color: var(--accent);
}
.suggestion-position { font-size: 13px; color: var(--text-secondary); }
.suggestion-body { padding: 14px 16px; }
.field {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
  font-size: 13px;
  line-height: 1.6;
}
.field:last-child { margin-bottom: 0; }
.field-label {
  min-width: 64px;
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.field-value { flex: 1; }
.original-text { color: #dc2626; background: #fef2f2; padding: 2px 8px; border-radius: 4px; }
.revised-text { color: #16a34a; background: #f0fdf4; padding: 2px 8px; border-radius: 4px; }
.law-text { color: #7c3aed; background: #f5f3ff; padding: 2px 8px; border-radius: 4px; }
.risk-text { color: #d97706; background: #fffbeb; padding: 2px 8px; border-radius: 4px; }
</style>
