# Web 后台镜像模板
# 职责：构建 Vue 前端产物，并打包 FastAPI 后端运行环境。
# 构建上下文：docker/web-backend

# ===== 阶段 1：前端构建 =====
# 如需升级 Node 版本，只改这里即可。
FROM node:20-alpine AS frontend-builder

# 前端构建工作目录。
WORKDIR /build

# 先复制依赖清单，利用 Docker 缓存减少重复安装。
COPY frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/index.html ./

# 复制前端源码。
COPY frontend/src/ ./src/

# 安装依赖并生成 dist 产物。
RUN npm install && npm run build

# ===== 阶段 2：后端运行时 =====
# 如需升级 Python 版本，只改这里即可。
FROM python:3.12-slim AS runtime

# 后端运行工作目录。
WORKDIR /app

# 后端源码位于 /app/src，加入 PYTHONPATH 后，代码中的 api/config/services 等顶层导入才能生效。
ENV PYTHONPATH=/app/src

# 先复制依赖清单，利用 Docker 缓存减少重复安装。
COPY backend/requirements.txt .

# 安装 Python 依赖；不保留 pip 缓存以减小镜像体积。
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端源码到容器内 /app/src。
COPY backend/src/ ./src/

# 复制前端构建产物，FastAPI 会从 /app/frontend/dist 托管静态页面。
COPY --from=frontend-builder /build/dist/ ./frontend/dist/

# 容器内监听端口；宿主机暴露规则由 docker-compose.yml 决定。
EXPOSE 8000

# 启动 FastAPI。端口保持 8000，外部端口映射交给 compose 管理。
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
