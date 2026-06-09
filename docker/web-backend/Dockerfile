# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /build
COPY frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/index.html ./
COPY frontend/src/ ./src/
RUN npm install && npm run build

# Stage 2: Backend runtime
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src/ ./src/
COPY --from=frontend-builder /build/dist/ ./frontend/dist/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
