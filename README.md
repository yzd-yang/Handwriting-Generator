# Handwriting Generator - 手写文字生成器

一款在线手写文字生成工具，能够将用户输入的文字转换为逼真的手写体图片或 PDF 文件。

## 项目来源

本项目基于 [14790897/handwriting-web](https://github.com/14790897/handwriting-web) 进行修改和优化，在原项目基础上增加了以下功能和改进：

### 主要改进

- **前端迁移Vite**：迁移到 Vite 更快的开发速度、更好的开发体验和更小的生产包体积。对于这个项目来说，冷启动从30秒降到2秒，热更新几乎即时，开发效率提升显著。
- **富文本编辑器**：集成 Tiptap 编辑器，支持粗体、斜体、下划线、列表、段落对齐等格式操作
- **文档导入优化**：Word 文档导入保留段落格式（标题、缩进、段落结构）
- **UI 优化**：采用 Tailwind CSS 重构界面，深色主题设计
- **颜色选择器**：支持预设颜色和自定义颜色选择

## 核心功能

- 手写文字生成（基于 handright 库）
- 多种纸张模板（空白、单线、方格、点阵）
- 多种纸张颜色和规格（A4/A5/B5/Letter）
- 丰富的手写参数调节（字号抖动、位置偏移、角度旋转、删除线、墨水深浅等）
- 段落排版（对齐、缩进、段间距）
- 文档导入（Word、PDF、TXT、RTF）
- 多页预览和导出（ZIP 图片包、PDF）

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Tailwind CSS + Tiptap |
| 后端 | FastAPI + Python 3.10+ |
| 手写渲染 | handright |
| 图像处理 | Pillow + OpenCV + scikit-learn |
| 文档解析 | pypandoc (Word) + PyMuPDF/PyPDF2 (PDF) |
| 其他后端库 | slowapi（限流）、Sentry SDK（监控）、schedule（定时任务）、psutil（系统监控）|
| 部署 | Docker Compose + K3s/Kubernetes |

## 快速开始

### Docker 部署（推荐）

```bash
docker compose up -d
```

- 前端访问：`http://localhost:2345`
- 后端 API：`http://localhost:5005`
- 字体文件挂载：`ttf_files/` → `/app/font_assets_host`

### 本地开发

**前置要求：**
- Python 3.10+
- Node.js 22+
- pandoc（文档转换，可选）

**前端：**
```bash
cd frontendVite
cp .env.example .env  # 配置环境变量（可选）
npm install
npm run dev
```

**后端：**
```bash
cd backend
cp .env.example .env  # 配置环境变量（必需）
pip install -r requirements.txt
python app.py
```

### 环境变量配置

**后端（backend/.env）：**
```bash
# 基础配置
PORT=5005
HOST=127.0.0.1

# 字体路径
FONT_ASSETS_HOST=/path/to/fonts

# 用户认证（可选，默认禁用）
ENABLE_USER_AUTH=false

# 监控（可选）
SENTRY_DSN=your_sentry_dsn

# 任务配置
MAX_ACTIVE_TASKS=8
MAX_CONCURRENT_EXECUTIONS=2
```

**前端（frontendVite/.env）：**
```bash
# API 地址
VITE_API_BASE_URL=http://localhost:5005

# 第三方服务（可选）
VITE_SENTRY_DSN=your_sentry_dsn
VITE_GA_ID=your_ga_id
VITE_CLARITY_ID=your_clarity_id
```

## 项目结构

```
├── frontendVite/            # Vue 3 前端（Vite + Tailwind CSS）
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   └── router/        # 路由配置
│   └── eslint.config.js    # ESLint 配置（flat config）
├── backend/                 # FastAPI 后端（模块化架构）
│   ├── app.py              # 主应用（路由定义、lifespan、中间件）
│   ├── config.py           # 环境变量配置管理
│   ├── services/           # 服务模块（6 个模块）
│   │   ├── cleanup.py     # 安全文件删除与临时目录清理
│   │   ├── image_utils.py # 纸张背景生成、颜色转换
│   │   ├── file_processing.py # docx/PDF 读取、段落排版预处理
│   │   ├── task_manager.py # WebSocket 推送、任务状态管理
│   │   ├── fonts.py       # 字体文件列表获取、字体同步
│   │   └── generation.py # 核心手写渲染逻辑 + 后台任务调度
│   ├── utils/             # 工具模块
│   │   └── logging_setup.py # 集中日志配置
│   ├── task_store.py      # 任务存储（SQLite）
│   ├── task_types.py      # 任务类型定义
│   └── identify.py       # 图片识别（纸张横线间距检测）
├── ttf_files/             # 内置字体文件
├── serverless/            # Vercel Serverless 函数
├── mysql/                 # MySQL 配置（可选）
├── docker-compose.yml     # Docker 部署配置
├── .github/workflows/     # CI/CD 配置
└── 产品说明书.md           # 详细产品文档
```

### 后端模块化架构

后端采用模块化设计，将 `app.py` 从 1697 行拆分到 6 个服务模块，提高可维护性：

- **services/cleanup.py**：安全文件删除与临时目录清理
- **services/image_utils.py**：纸张背景生成、颜色转换
- **services/file_processing.py**：docx/PDF 读取、段落排版预处理
- **services/task_manager.py**：WebSocket 推送、任务状态管理
- **services/fonts.py**：字体文件列表获取、字体同步
- **services/generation.py**：核心手写渲染逻辑 + 后台任务调度

## 相关链接

- 原项目：[14790897/handwriting-web](https://github.com/14790897/handwriting-web)

## 许可证

本项目基于原项目进行修改，请遵循原项目的许可证条款。
