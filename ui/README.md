# 🎯 合同修订与法律知识库管理系统

## 📋 项目简介

这是一个面向最终用户的现代化 Web 应用系统，集成了两大核心功能:

1. **合同智能修订** - 基于 AI 大模型的合同自动审查与修订系统
2. **法律知识库管理** - Pinecone 向量数据库管理与语义检索系统

### ✨ 主要特性

- 🎨 **现代化 UI** - 渐变色设计、响应式布局、流畅动画
- 🔗 **双模块集成** - 统一管理入口，两个独立功能模块
- 🤖 **AI 驱动** - 使用 DeepSeek 大模型进行智能分析
- 💾 **向量检索** - Pinecone 支持的语义相似度搜索
- 📱 **响应式设计** - 支持 PC、平板、手机等多种设备
- ⚡ **实时反馈** - 进度条、状态指示器、即时通知

---

## 🚀 快速开始

### 方式一：直接启动 (推荐)

```bash
# 在项目根目录执行
python ui/app.py
```

### 方式二：使用启动脚本

```bash
# 创建启动脚本 (如果还没有)
echo "python ui/app.py" > start_ui.bat

# Windows 双击运行
start_ui.bat

# Linux/Mac
./start_ui.sh
```

### 访问地址

启动后在浏览器访问：**http://localhost:5000**

---

## 📁 项目结构

```
ui/
├── app.py                      # Flask 后端主程序
├── templates/                  # HTML 模板
│   ├── index.html             # 主页 (功能选择)
│   ├── contract_revision.html # 合同修订页面
│   └── pinecone_manager.html  # Pinecone 管理页面
├── static/                     # 静态资源
│   ├── style.css              # 全局样式
│   └── main.js                # 通用 JavaScript 工具
└── README.md                   # 本文档
```

---

## 🎯 功能说明

### 1️⃣ 合同智能修订

#### 功能特点
- ✅ 支持 PDF/Word 格式文件
- ✅ 自动 OCR 识别扫描件
- ✅ AI 识别法律条款 (责任、监管、合规、争议解决等)
- ✅ 自动匹配相关法律法规
- ✅ 生成修订版本和详细修改建议

#### 使用流程
1. 进入"合同修订"页面
2. 上传或选择合同文件
3. 点击"开始智能审查"
4. 查看结果:
   - **修订合同** - 完整的修订后文本
   - **修改建议** - 逐条列出修改意见和理由
   - **法律条款** - 识别到的法律条款分类

#### API 端点
- `GET /contract` - 合同修订页面
- `POST /api/contract/process` - 处理合同
- `GET /api/contract/files` - 获取文件列表

---

### 2️⃣ 法律知识库管理

#### 功能特点
- ✅ Pinecone 向量数据库连接管理
- ✅ 文档上传与向量化处理
- ✅ 语义相似度搜索
- ✅ 索引状态监控
- ✅ 配置管理 (API Key、索引名、分块后端)

#### 使用流程
1. 进入"知识库管理"页面
2. 配置 Pinecone 连接参数
3. 上传文档进行处理
4. 使用向量搜索功能
5. 查看统计信息

#### API 端点
- `GET /pinecone` - 知识库管理页面
- `GET /api/pinecone/status` - 获取连接状态
- `GET /api/pinecone/config` - 获取配置
- `POST /api/pinecone/config` - 保存配置
- `POST /api/pinecone/upload` - 上传文档
- `POST /api/pinecone/search` - 向量搜索
- `GET /api/pinecone/stats` - 获取统计

---

## ⚙️ 配置说明

### 环境变量 (可选)

创建 `.env` 文件配置敏感信息:

```bash
# Pinecone配置
PINECONE_API_KEY=your_api_key_here
PINECONE_INDEX=software

# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-f421b6764bab44a08617c32812bbd607
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

### 配置文件

系统会自动读取以下配置文件:

1. **合同修订配置** - `config.py` 中的 `CONFIG`
2. **Pinecone配置** - `data/knowledge_base/kb_config.json`

---

## 🎨 UI 设计特色

### 配色方案
- **主色调**: 渐变紫 (#667eea → #764ba2)
- **成功色**: #28a745
- **错误色**: #dc3545
- **警告色**: #ffc107
- **信息色**: #17a2b8

### 组件库
- **卡片式设计** - 阴影效果、圆角边框
- **渐变色按钮** - 视觉吸引力强
- **状态指示器** - 实时显示服务状态
- **模态框** - 文件选择器
- **通知系统** - Toast 消息提示
- **进度条** - 平滑动画效果
- **选项卡** - 内容切换展示

### 响应式断点
- **桌面**: > 768px
- **平板**: 768px - 1024px
- **手机**: < 768px

---

## 🔧 开发指南

### 添加新功能模块

1. **后端路由** - 在 `app.py` 中添加路由
2. **前端页面** - 在 `templates/` 中创建 HTML
3. **API 接口** - 添加对应的 RESTful 端点
4. **导航菜单** - 更新各页面的导航栏

### 自定义样式

编辑 `static/style.css`,可以修改:
- 颜色变量
- 字体大小
- 间距尺寸
- 动画效果

### 扩展 JavaScript

在 `static/main.js` 中添加:
- 新的工具函数
- API 请求封装
- 本地存储方法
- 表单验证规则

---

## 🐛 故障排查

### 问题 1: 无法启动服务

**症状**: 运行 `python ui/app.py` 报错

**解决方案**:
```bash
# 检查依赖是否安装
pip install flask openai pinecone python-docx PyPDF2 paddleocr

# 查看详细错误信息
python ui/app.py --debug
```

### 问题 2: Pinecone 连接失败

**症状**: 状态显示"未连接"

**解决方案**:
1. 检查 API Key 是否正确
2. 确认索引名称存在
3. 检查网络连接
4. 查看 `kb_config.json` 配置

### 问题 3: 合同处理超时

**症状**: 进度条长时间不动

**解决方案**:
1. 检查文件大小 (建议 < 10MB)
2. 确认 DeepSeek API 配额充足
3. 检查 OCR 引擎是否正常
4. 尝试离线模式

---

## 📊 性能优化建议

### 前端优化
- ✅ 使用 CDN 加载常用库
- ✅ 压缩 CSS 和 JS 文件
- ✅ 图片懒加载
- ✅ 减少 HTTP 请求

### 后端优化
- ✅ 启用 Flask 缓存
- ✅ 异步处理长任务
- ✅ 数据库连接池
- ✅ 静态文件服务使用 Nginx

### 部署优化
- ✅ 使用 Gunicorn/uWSGI
- ✅ 启用 HTTPS
- ✅ 配置反向代理 (Nginx/Apache)
- ✅ 设置适当的超时时间

---

## 🔒 安全注意事项

### 生产环境部署
1. **启用 HTTPS** - 使用 Let's Encrypt 免费证书
2. **隐藏调试信息** - 设置 `debug=False`
3. **限制上传大小** - 防止 DoS 攻击
4. **输入验证** - 所有用户输入都要验证
5. **速率限制** - 防止 API 滥用
6. **日志审计** - 记录所有操作日志

### 敏感信息保护
- ❌ 不要将 API Key 提交到版本控制
- ✅ 使用环境变量或加密存储
- ✅ 定期轮换密钥
- ✅ 最小权限原则

---

## 📝 更新日志

### v1.0.0 (2026-03-14)
- ✅ 初始版本发布
- ✅ 集成合同修订功能
- ✅ 集成 Pinecone 管理功能
- ✅ 现代化 UI 设计
- ✅ 响应式布局
- ✅ 完整文档

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request!

### 开发环境搭建
```bash
# 克隆项目
git clone <repository-url>
cd contract_revision_agent/ui

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
```

### 代码规范
- 遵循 PEP 8 规范
- 添加必要的注释
- 编写单元测试
- 更新文档

---

## 📧 联系方式

- **项目负责人**: [Your Name]
- **邮箱**: [Your Email]
- **GitHub**: [Repository URL]

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

感谢以下开源项目:
- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [DeepSeek](https://www.deepseek.com/) - AI 大模型
- [Pinecone](https://www.pinecone.io/) - 向量数据库
- [UltraRAG](https://github.com/) - RAG 框架

---

**🎉 享受使用合同修订与法律知识库管理系统!**
