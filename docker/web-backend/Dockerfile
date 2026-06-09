# Web 后台镜像模板（简化版）
# 只打包 Python 运行时，前端和后端源码通过 volume 挂载。
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONPATH=/app/src

# 安装 Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 启动入口
COPY entrypoint.sh .
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
