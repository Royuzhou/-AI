import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'chat',
      component: () => import('@/pages/ChatPage.vue'),
      meta: { title: '对话' },
    },
    {
      path: '/knowledge',
      name: 'knowledge',
      component: () => import('@/pages/KnowledgePage.vue'),
      meta: { title: '知识库' },
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('@/pages/HistoryPage.vue'),
      meta: { title: '历史记录' },
    },
    {
      path: '/revision/:taskId',
      name: 'revision',
      component: () => import('@/pages/RevisionPage.vue'),
      meta: { title: '修订结果' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/pages/SettingsPage.vue'),
      meta: { title: '设置' },
    },
  ],
})

export default router
