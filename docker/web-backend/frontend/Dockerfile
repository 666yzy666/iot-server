# Web 后台前端单独构建模板
# 职责：构建 Vue 前端，并用 Nginx 提供静态页面。
# 构建上下文建议：docker/web-backend

# ===== 阶段 1：前端构建 =====
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# 先复制依赖清单，利用 Docker 缓存减少重复安装。
COPY frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/index.html ./

# 复制前端源码。
COPY frontend/src ./src

# 安装依赖并生成 dist 产物。
RUN npm install && npm run build

# ===== 阶段 2：静态文件服务 =====
FROM nginx:alpine AS frontend-runtime

# 将构建产物复制到 Nginx 默认静态目录。
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Nginx 容器内监听端口；宿主机暴露规则由 compose 决定。
EXPOSE 80

# nginx 官方镜像已经提供默认 CMD，这里不重复声明。
