# Web 后台后端单独构建模板
# 职责：只构建 FastAPI 后端，不包含 Vue 前端产物。
# 构建上下文建议：docker/web-backend

FROM python:3.12-slim AS backend-runtime

# 后端运行工作目录。
WORKDIR /app

# 后端源码位于 /app/src，加入 PYTHONPATH 后，代码中的 api/config/services 等顶层导入才能生效。
ENV PYTHONPATH=/app/src

# 先复制依赖清单，利用 Docker 缓存减少重复安装。
COPY backend/requirements.txt .

# 安装 Python 依赖。
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端源码。
COPY backend/src ./src

# 复制启动入口脚本：先初始化数据库，再启动 Web 服务。
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# 容器内监听端口；宿主机暴露规则由 compose 决定。
EXPOSE 8000

# 容器启动时先执行 entrypoint 初始化数据库，再启动 FastAPI。
ENTRYPOINT ["/app/entrypoint.sh"]

# FastAPI 启动命令。
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
