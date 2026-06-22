# 📚 教案生成系统

基于大语言模型（LLM）的智能教案生成工具。用户上传自己的 Word 教案模板，AI 自动分析模板结构并生成完整教案内容进行填充。

## ✨ 功能特性

- **📄 自定义模板上传**：支持上传你自己的 `.docx` 教案模板，系统自动分析结构并基于模板生成
- **🤖 通用大模型接入**：支持任意兼容 OpenAI Chat Completions API 的模型
  - DeepSeek / MiniMax / Kimi / 通义千问 / 智谱 GLM / OpenAI 及更多
- **🔧 可视化配置**：内置 `/setup` 页面，在浏览器中直接填写 API Key、选择模型预设
- **📊 Excel 批量导入**：下载 Excel 模板 → 填写多个课时 → 导入一键批量生成
- **📎 参考文档上传**：支持上传 docx、pptx、xlsx、txt、pdf 等教学参考资料
- **🎨 格式保持**：基于 Word 模板填充，保持原教案格式和排版不变
- **📦 开箱即用**：PyInstaller 打包为独立 exe，无需安装 Python 环境

## 🚀 快速开始

### 方式一：直接运行（推荐）

1. 从 [Releases](https://github.com/shuiyuccc/AI-Generated-teaching-plan/releases) 下载 `LessonPlanGenerator.exe`
2. 双击运行，浏览器访问 `http://localhost:5000`
3. 首次使用点击右下角 **⚙️ 齿轮按钮** 配置 API Key
4. 上传你的教案模板（或使用内置默认模板）
5. 填写课程信息，点击生成

### 方式二：源码运行

```bash
git clone https://github.com/shuiyuccc/AI-Generated-teaching-plan.git
cd AI-Generated-teaching-plan

# 安装依赖
pip install flask flask-cors python-docx openpyxl requests python-dotenv

# 启动服务
cd backend
python api_server.py

# 浏览器访问 http://localhost:5000
```

## 🔑 API Key 配置

项目不内置任何 API Key。首次使用：

1. 点击页面右下角 **⚙️ 蓝色齿轮按钮**（或访问 `/setup`）
2. 选择一个模型预设（推荐 DeepSeek，注册即送免费额度）
3. 填入你的 API Key，保存即可

支持的模型预设：

| 模型 | 获取 Key |
|------|----------|
| 🔮 DeepSeek V3 | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| 🤖 MiniMax | [platform.minimaxi.com](https://platform.minimaxi.com) |
| 🌙 Kimi | [platform.moonshot.cn](https://platform.moonshot.cn) |
| ☁️ 通义千问 | [dashscope.aliyun.com](https://dashscope.aliyun.com) |
| 🧠 智谱 GLM | [open.bigmodel.cn](https://open.bigmodel.cn) |
| ✏️ 自定义 | 任意兼容 OpenAI 接口的 API 地址 |

配置保存在本地 `llm_settings.json`，不会上传到任何服务器。

## 📖 使用指南

### 单课时生成

1. 点击右下角 **📄 绿色按钮** 上传你的教案模板（可选，不上传则使用内置模板）
2. 填写课程基本信息（院系、专业名称、课程名称等）
3. 填写课时信息（课题名称、授课地点、学时等）
4. 可选：上传教学参考资料（课件、教材等）
5. 点击 **「生成教案」**
6. 等待 AI 生成完成后自动下载 Word 文档

### 批量生成（Excel 导入）

```
下载模板 → 填写 Excel → 导入 Excel → 批量生成
```

1. 点击 **「下载模板」** 获取 Excel 模板
2. 在 Excel 中逐行填写各课时的信息
3. 点击 **「导入 Excel」** 上传填好的文件
4. 确认信息后点击 **「批量生成」**
5. 系统逐课生成并汇总结果

### 上传自定义教案模板

1. 点击右下角 **📄 绿色上传按钮**
2. 选择你的 `.docx` 格式教案模板
3. 系统自动识别模板中的所有填写区域（标签、段落、教学环节表格等）
4. 生成时 AI 会基于模板结构动态填充每个位置

## 🏗️ 技术架构

```
├── backend/                        # 后端（Python Flask）
│   ├── api_server.py               # Flask API 服务，所有接口
│   ├── config.py                   # 通用 LLM 配置，支持预设+自定义
│   ├── main.py                     # LLM 调用与教案生成核心逻辑
│   ├── template_manager.py         # 模板分析、动态填充引擎
│   ├── document_processor.py       # 参考文档解析（docx/pptx/pdf等）
│   ├── excel_utils.py              # Excel 模板生成与解析
│   ├── fill_jiaoan_keep_format.py  # Word 模板填充（格式保持）
│   └── analyze_template_with_merge.py  # Word 模板结构分析
│
├── frontend/                       # 前端（React + TypeScript + Vite）
│   ├── src/                        # 源代码
│   └── dist/                       # 构建产物
│       ├── index.html              # 主页面（含浮动按钮）
│       └── setup.html              # 大模型配置页面
│
└── moban.docx                      # 默认教案 Word 模板
```

### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/session` | POST | 创建生成会话 |
| `/api/session/<id>` | GET | 查询会话状态 |
| `/api/logs/<id>/poll` | GET | 轮询实时日志 |
| `/api/generate` | POST | 单课时生成 |
| `/api/batch-generate` | POST | 批量生成 |
| `/api/upload-document` | POST | 上传参考资料 |
| `/api/upload-template` | POST | 上传自定义教案模板 |
| `/api/template-info/<id>` | GET | 获取模板分析结果 |
| `/api/documents/<id>` | GET | 获取已上传文档列表 |
| `/api/documents/<id>/<filename>` | DELETE | 删除已上传文档 |
| `/api/download-template` | GET | 下载 Excel 模板 |
| `/api/upload-excel` | POST | 上传并解析 Excel |
| `/api/settings` | GET/POST | 读写 LLM 配置 |
| `/api/presets` | GET | 获取模型预设列表 |
| `/download/<filename>` | GET | 下载生成的教案 |
| `/setup` | GET | 大模型配置页面 |
| `/health` | GET | 健康检查 |

## 🔒 安全说明

- **API Key 不上传**：所有配置保存在本地 `llm_settings.json`，已加入 `.gitignore`
- **本地存储**：所有配置和生成文件保存在本地
- **环境变量支持**：也支持通过 `.env` 文件或系统环境变量配置
- **Key 遮蔽**：设置页面不会完整显示已保存的 API Key

## 📋 环境要求

- **运行 exe**：Windows 10+ x64
- **源码运行**：Python 3.10+，Node.js 18+（仅前端开发需要）
- **API Key**：任意兼容 OpenAI Chat Completions API 的大模型账号

## 🛠️ 开发

```bash
# 后端
cd backend
pip install flask flask-cors python-docx openpyxl requests python-dotenv
python api_server.py

# 前端开发
cd frontend
npm install
npm run dev
```

## 📄 License

MIT License
