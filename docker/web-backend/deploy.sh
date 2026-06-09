#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
    echo "missing .env; copy .env.example to .env and set the real MySQL password" >&2
    exit 1
fi

# 1. 构建前端（用 Docker node 临时容器，不需要宿主机安装 Node）
echo ">>> Building frontend..."
mkdir -p frontend/dist
docker run --rm \
  -v "$(pwd)/frontend:/build" \
  -w /build \
  node:20-alpine \
  sh -c "npm install --silent && npm run build"

# 2. 确保镜像是最新的（仅 Python 依赖变化时需要重构建）
echo ">>> Ensuring image is up to date..."
docker compose build --pull

# 3. 启动/重启容器
echo ">>> Starting services..."
docker compose --env-file .env up -d

echo ">>> Done."
