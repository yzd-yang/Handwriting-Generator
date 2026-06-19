# Handwriting Generator - 手写文字生成器

一款在线手写文字生成工具，能够将用户输入的文字转换为逼真的手写体图片或 PDF 文件。

## 项目来源

本项目基于 [14790897/handwriting-web](https://github.com/14790897/handwriting-web) 进行修改和优化，在原项目基础上增加了以下功能和改进：

### 主要改进

- **富文本编辑器**：集成 Tiptap 编辑器，支持粗体、斜体、下划线、列表、段落对齐等格式操作
- **文档导入优化**：Word 文档导入保留段落格式（标题、缩进、段落结构）
- **UI 优化**：采用 Tailwind CSS 重构界面，深色主题设计
- **颜色选择器**：支持预设颜色和自定义颜色选择
- **预览优化**：单页快速预览，减少等待时间
- **工具栏固定**：富文本编辑器工具栏固定，内容区域独立滚动
- **PWA 支持**：可安装为桌面应用
- **异步任务队列**：支持并发控制和任务状态实时推送

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
| 文档解析 | pypandoc (Word) + PyPDF2 (PDF) |
| 部署 | Docker Compose |

## 快速开始

### Docker 部署（推荐）

```bash
docker compose up -d
```

- 前端访问：`http://localhost:2345`
- 后端 API：`http://localhost:5005`

### 本地开发

**前端：**
```bash
cd frontendVite
npm install
npm run dev
```

**后端：**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

## 项目结构

```
├── frontendVite/       # Vue 3 前端（Vite + Tailwind CSS）
├── backend/            # FastAPI 后端
├── ttf_files/          # 内置字体文件
├── serverless/         # Vercel Serverless 函数
├── mysql/              # MySQL 配置（可选）
├── docker-compose.yml  # Docker 部署配置
└── 产品说明书.md        # 详细产品文档
```

## 相关链接

- 原项目：[14790897/handwriting-web](https://github.com/14790897/handwriting-web)
- handright 库：[文档](https://handright.readthedocs.io/)

## 许可证

本项目基于原项目进行修改，请遵循原项目的许可证条款。
