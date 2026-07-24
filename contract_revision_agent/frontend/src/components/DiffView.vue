<template>
  <div class="diff-card">
    <div v-if="label" class="diff-label">{{ label }}</div>
    <div class="diff-columns">
      <div class="diff-col original">
        <div class="col-header">📄 原文</div>
        <div class="col-body">{{ original }}</div>
      </div>
      <div class="diff-col revised">
        <div class="col-header">✅ 修订后</div>
        <div class="col-body">{{ revised }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  original: string
  revised: string
  label?: string
}>()
</script>

<style scoped>
.diff-card {
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
}
.diff-label {
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  background: #f9fafb;
  border-bottom: 1px solid var(--border-color);
}
.diff-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
}
.diff-col {
  padding: 0;
}
.diff-col:first-child { border-right: 1px solid var(--border-color); }
.col-header {
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
}
.original .col-header { background: #fef2f2; color: #dc2626; }
.revised .col-header { background: #f0fdf4; color: #16a34a; }
.col-body {
  padding: 14px;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  min-height: 80px;
}
</style>
