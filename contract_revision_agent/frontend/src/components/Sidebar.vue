<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="logo-icon">📋</div>
      <h1>合同修订智能体</h1>
    </div>
    <nav class="sidebar-nav">
      <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
        <span class="nav-icon">💬</span>
        <span>对话</span>
      </router-link>
      <router-link to="/knowledge" class="nav-item" :class="{ active: $route.path === '/knowledge' }">
        <span class="nav-icon">📚</span>
        <span>知识库</span>
      </router-link>
      <router-link to="/history" class="nav-item" :class="{ active: $route.path === '/history' }">
        <span class="nav-icon">📋</span>
        <span>历史记录</span>
      </router-link>
      <router-link to="/settings" class="nav-item" :class="{ active: $route.path === '/settings' }">
        <span class="nav-icon">⚙️</span>
        <span>设置</span>
      </router-link>
    </nav>
    <div class="sidebar-footer">
      <div class="kb-indicator" :class="kbStore.connected ? 'online' : 'offline'">
        <span class="dot"></span>
        <span>{{ kbStore.loading ? '连接中...' : (kbStore.connected ? 'KB 已连接' : 'KB 未连接') }}</span>
      </div>
      <span class="version">v1.0</span>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useKbStore } from '@/stores/kb'
const kbStore = useKbStore()
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  user-select: none;
}
.sidebar-header {
  padding: 24px 20px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.logo-icon { font-size: 24px; margin-bottom: 8px; }
.sidebar-header h1 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-sidebar-active);
  letter-spacing: 0.5px;
}
.sidebar-nav {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  color: var(--text-sidebar);
  font-size: 14px;
  transition: all 0.15s;
  text-decoration: none;
}
.nav-item:hover {
  background: rgba(255,255,255,0.08);
  color: var(--text-sidebar-active);
}
.nav-item.active {
  background: var(--accent);
  color: #fff;
  font-weight: 500;
}
.nav-icon { font-size: 16px; width: 20px; text-align: center; }
.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(255,255,255,0.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.kb-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: rgba(255,255,255,0.5);
}
.kb-indicator .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.kb-indicator.online .dot { background: #4ade80; }
.kb-indicator.offline .dot { background: #f87171; }
.version {
  color: rgba(255,255,255,0.3);
  font-size: 12px;
}
</style>
