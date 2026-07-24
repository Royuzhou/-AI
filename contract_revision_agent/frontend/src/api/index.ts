/**
 * API 统一入口 — 所有后端接口
 *
 * 后端路由前缀: /api
 * 开发代理:   vite → http://localhost:8080
 * 生产部署:   Flask 同源直连
 */

// ── 对话 & 聊天 ──
export {
  sendMessage,
  loadSessions,
  loadSession,
  injectRevisionContext,
} from './chat'

// ── 合同修订 ──
export {
  uploadFile,
  startRevision,
  getRevisionStatus,
} from './contract'

// ── 知识库 ──
export {
  uploadKbFile,
  processDocument,
  searchKnowledge,
  getKbStatus,
  deleteKbEntries,
} from './knowledge'

// ═══════════════════════════════════════════════
// 完整 API 表
// ═══════════════════════════════════════════════
//
//   GET    /api/chat/list              → loadSessions
//   GET    /api/chat/:id               → loadSession
//   POST   /api/chat/send              → sendMessage (SSE)
//   POST   /api/chat/context           → injectRevisionContext
//   DELETE /api/chat/:id               → (历史删除)
//
//   POST   /api/upload                 → uploadFile
//
//   POST   /api/contract/revise        → startRevision
//   GET    /api/contract/status/:id    → getRevisionStatus
//
//   GET    /api/kb/status              → getKbStatus
//   POST   /api/kb/upload              → uploadKbFile
//   POST   /api/kb/process             → processDocument
//   GET    /api/kb/search?q=&top_k=    → searchKnowledge
//   DELETE /api/kb/entries             → deleteKbEntries
//
//   GET    /api/config                 → useConfigStore.loadConfig
//   POST   /api/config/deepseek        → useConfigStore.saveDeepSeek
//   POST   /api/config/pinecone        → useConfigStore.savePinecone
//   POST   /api/config/test/deepseek   → useConfigStore.testDeepSeek
//   POST   /api/config/test/pinecone   → useConfigStore.testPinecone
