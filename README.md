# 📚 AI 教案生成系统

基于大语言模型（LLM）的智能教案生成工具，支持单课时和批量生成 Word 教案文档。专为职业院校教师设计，帮助快速生成规范的教学方案。

## ✨ 功能特性

- **🤖 AI 智能生成**：对接 DeepSeek V3 / MiniMax 等大模型，根据课程信息自动生成完整教案内容
- **📝 两种生成模式**：支持手动填写单课时生成，也支持 Excel 批量导入多课时生成
- **📄 参考文档上传**：支持上传 docx、pptx、xlsx、txt、pdf 等格式的教学参考资料
- **🔧 可视化配置**：内置 `/setup` 设置页面，在浏览器中直接填写 API Key，无需手动编辑配置文件
- **📊 Excel 模板支持**：提供标准 Excel 模板下载，填写后一键导入批量生成
- **🎨 格式保持**：基于 Word 模板填充，保持原教案格式和排版不变
- **📦 开箱即用**：PyInstaller 打包为独立 exe，无需安装 Python 环境

## 🚀 快速开始

### 方式一：直接运行（推荐）

1. 从 [Releases](https://github.com/shuiyuccc/AI-Generated-teaching-plan/releases) 下载 `LessonPlanGenerator.exe`
2. 双击运行，程序会自动打开浏览器
3. 首次使用访问 `http://localhost:5000/setup` 配置 API Key
4. 返回首页开始生成教案

### 方式二：源码运行

```bash
# 克隆仓库
git clone https://github.com/shuiyuccc/AI-Generated-teaching-plan.git
cd AI-Generated-teaching-plan

# 安装 Python 依赖
pip install -r requirements.txt

# 启动服务
cd backend
python api_server.py

# 浏览器访问 http://localhost:5000
```

> **注意**：源码运行需要将 `requirements.txt` 和 `moban.docx`（教案模板）放置在 `backend/` 目录下。

## 🔑 API Key 配置

项目不内置任何 API Key。首次使用请按以下步骤配置：

1. 启动应用后访问 `/setup` 页面（或点击首页的设置入口）
2. 选择一个模型：
   - **DeepSeek V3**（推荐）：注册即送免费额度 → [获取 Key](https://platform.deepseek.com/api_keys)
   - **MiniMax**：→ [获取 Key](https://platform.minimaxi.com/user-center/basic-information/interface-key)
3. 填写 API Key 和 API 地址（地址一般保持默认即可）
4. 点击「保存配置」

配置保存在本地 `llm_settings.json` 文件中，不会上传到任何服务器。

### 支持的模型

| 模型 | API 地址 | 说明 |
|------|----------|------|
| DeepSeek V3 | `https://api.deepseek.com/v1/chat/completions` | 性价比高，推荐 |
| MiniMax-M2.7 | `https://api.minimaxi.com/v1/chat/completions` | 国产模型 |
| Kimi（兼容） | 自定义 API 地址 | 支持 OpenAI 兼容接口 |

> 任何兼容 OpenAI Chat Completions 接口的模型都可以通过修改 API 地址来接入。

## 📖 使用指南

### 单课时生成

1. 在首页填写课程信息（课题名称、授课地点、学时等）
2. 可选：上传教学参考资料（课件、教材等）
3. 点击「生成教案」
4. 等待 AI 生成完成后自动下载 Word 文档

### 批量生成（Excel 导入）

1. 点击「下载模板」获取标准 Excel 模板
2. 在 Excel 中填写多个课时的信息
3. 点击「导入 Excel」上传填写好的文件
4. 确认信息后点击「批量生成」
5. 系统逐课生成并汇总结果

### Excel 模板格式

| 课题名称 | 授课地点 | 授课时间 | 授课学时 | 授课类型 | 参考资料路径 |
|----------|----------|----------|----------|----------|--------------|
| 焊接5步法 | 焊接实训室 | 2026年2月 | 3学时 | 理实一体化 | C:\docs\焊接指南.docx |

## 🏗️ 技术架构

```
├── backend/                    # 后端（Python Flask）
│   ├── api_server.py           # Flask API 服务，所有接口
│   ├── config.py               # 配置管理，支持环境变量和 JSON 文件
│   ├── main.py                 # LLM 调用与教案生成核心逻辑
│   ├── document_processor.py   # 参考文档解析（docx/pptx/pdf等）
│   ├── excel_utils.py          # Excel 模板生成与解析
│   ├── fill_jiaoan_keep_format.py  # Word 模板填充（保持格式）
│   ├── analyze_template_with_merge.py  # Word 模板结构分析
│   └── test_minimax.py         # MiniMax API 连接测试
│
├── frontend/                   # 前端（React + TypeScript + Vite）
│   ├── src/                    # 源代码
│   └── dist/                   # 构建产物（含 setup.html 设置页）
│
└── moban.docx                  # 教案 Word 模板
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python Flask + flask-cors |
| 前端框架 | React + TypeScript + Ant Design |
| 构建工具 | Vite |
| 文档处理 | python-docx, openpyxl, python-pptx, pdfplumber |
| LLM 接口 | OpenAI 兼容 Chat Completions API |
| 打包部署 | PyInstaller |

### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/session` | POST | 创建生成会话 |
| `/api/session/<id>` | GET | 查询会话状态 |
| `/api/logs/<id>/poll` | GET | 轮询实时日志 |
| `/api/generate` | POST | 单课时生成 |
| `/api/batch-generate` | POST | 批量生成 |
| `/api/upload-document` | POST | 上传参考资料 |
| `/api/documents/<id>` | GET | 获取已上传文档列表 |
| `/api/documents/<id>/<filename>` | DELETE | 删除已上传文档 |
| `/api/download-template` | GET | 下载 Excel 模板 |
| `/api/upload-excel` | POST | 上传并解析 Excel |
| `/api/settings` | GET/POST | 读写 LLM 配置 |
| `/download/<filename>` | GET | 下载生成的教案 |
| `/setup` | GET | API 配置页面 |
| `/health` | GET | 健康检查 |

## 🔒 安全说明

- **API Key 不上传**：`llm_settings.json` 已加入 `.gitignore`，不会被提交到 Git
- **本地存储**：所有配置和生成文件保存在本地，不上传到任何云端
- **环境变量支持**：也支持通过 `.env` 文件或系统环境变量配置 API Key
- **Key 遮蔽**：设置页面不会完整显示已保存的 API Key

## 📋 环境要求

- **运行 exe**：Windows 10+ x64
- **源码运行**：Python 3.10+，Node.js 18+（仅前端开发需要）
- **API Key**：DeepSeek 或 MiniMax 账号（免费注册即可）

## 🛠️ 开发

```bash
# 后端开发
cd backend
pip install -r requirements.txt
python api_server.py

# 前端开发
cd frontend
npm install
npm run dev
```

## 📄 License

MIT License

---

Made with ❤️ for teachers
