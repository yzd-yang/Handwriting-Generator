# Handwriting Web Frontend (Vite)

基于 Vite + Vue 3 的手写文字生成网站前端。

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发服务器

```bash
npm run dev
```

开发服务器将在 `http://localhost:5173` 启动，`/api` 请求自动代理到 `http://127.0.0.1:5005`。

### 生产构建

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 代码检查

```bash
npm run lint
```

## 项目结构

```
frontendVite/
├── public/              # 静态资源
├── src/
│   ├── assets/          # 资源文件
│   ├── components/      # 公共组件
│   │   └── TiptapEditor.vue  # 富文本编辑器组件
│   ├── router/          # 路由配置
│   ├── store/           # Vuex 状态管理
│   ├── utils/           # 工具函数
│   ├── views/           # 页面组件
│   │   └── HomeView.vue      # 主页面（配置 + 预览）
│   ├── i18n.js          # 国际化配置
│   ├── main.js          # 入口文件
│   └── App.vue          # 根组件
├── index.html           # HTML 模板
├── vite.config.js       # Vite 配置
├── tailwind.config.js   # Tailwind CSS 配置
└── .prettierrc          # Prettier 配置
```

## 主要功能

### 富文本编辑器（TiptapEditor）

基于 Tiptap 的富文本编辑器，支持：

- **文本格式**：粗体、斜体、下划线
- **列表**：无序列表、有序列表
- **段落对齐**：左对齐、居中、右对齐、两端对齐
- **滚动**：工具栏固定，内容区域可滚动（最大高度 240px）

编辑器输出 HTML 格式，生成手写图片时自动转换为纯文本。

### 文档导入

支持导入 `.docx`、`.pdf`、`.txt`、`.rtf` 格式文档：

- Word 文档：后端使用 pypandoc 转换为 HTML，保留段落格式
- PDF 文档：后端使用 PyPDF2 提取文本，转换为 HTML 段落
- 导入后在富文本编辑器中显示，可继续编辑

### 纸张配置

- **模板**：空白、单线、方格、点阵
- **颜色**：6 种预设 + 自定义颜色选择器
- **规格**：A4、A5、B5、Letter 一键切换

### 生成与导出

- **预览**：快速渲染第一页查看效果
- **生成图片**：渲染全部页面，打包 ZIP 下载
- **生成 PDF**：渲染全部页面，合并 PDF 下载

## 技术栈

| 类别 | 技术 |
|------|------|
| 构建工具 | Vite |
| 前端框架 | Vue 3 |
| 状态管理 | Vuex 4 |
| 路由 | Vue Router |
| UI 框架 | Tailwind CSS |
| 富文本编辑 | Tiptap |
| 国际化 | vue-i18n |
| HTTP 客户端 | axios + axios-retry |
| 错误监控 | Sentry |
| 弹窗组件 | SweetAlert2 |
| PWA | vite-plugin-pwa |

## 开发说明

### API 代理

开发环境下，`/api` 请求会被代理到 `http://127.0.0.1:5005`。

配置位于 `vite.config.js`：

```js
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:5005',
      changeOrigin: true
    }
  }
}
```

### 代码规范

项目使用 ESLint + Prettier 进行代码规范检查。

- ESLint: `eslint-plugin-vue`
- Prettier: 单引号、无分号、2 空格缩进

### 关键依赖

- `@tiptap/vue-3`：富文本编辑器框架
- `@tiptap/starter-kit`：Tiptap 基础扩展包
- `@tiptap/extension-underline`：下划线支持
- `@tiptap/extension-text-align`：段落对齐支持
- `axios-retry`：HTTP 请求自动重试（3 次，指数退避）

## 部署

### Docker

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:5005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 相关链接

- [Vite 文档](https://vitejs.dev/)
- [Vue 3 文档](https://vuejs.org/)
- [Tiptap 文档](https://tiptap.dev/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
