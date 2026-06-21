FROM node:20-alpine AS build

WORKDIR /app

# 安装 pnpm（可选，加速依赖安装）
# RUN npm install -g pnpm

# 先拷贝依赖声明，利用 Docker 缓存层
COPY package*.json ./

# 安装依赖（用 npm ci 保证锁文件一致）
RUN npm ci

# 拷贝源码
COPY . .

# 生产构建
RUN npm run build

# ── 运行阶段 ──────────────────────────────────────────────
FROM nginx:alpine

# 拷贝构建产物到 nginx 静态目录
COPY --from=build /app/dist /usr/share/nginx/html

# 拷贝 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
