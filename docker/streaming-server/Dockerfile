# 流媒体服务镜像模板
# 职责：安装 Nginx + RTMP 模块，并加载本目录的 nginx.conf。
# 构建上下文：docker/streaming-server

FROM debian:bookworm-slim AS streaming-runtime

# 安装 Nginx、RTMP 模块和 CA 证书；清理 apt 缓存以减小镜像体积。
RUN apt-get update \
	&& apt-get install -y --no-install-recommends nginx libnginx-mod-rtmp ca-certificates \
	&& rm -rf /var/lib/apt/lists/*

# 复制流媒体服务配置。
COPY nginx.conf /etc/nginx/nginx.conf

# 1935 用于 RTMP，8080 用于 HTTP 状态页和拉流入口。
EXPOSE 1935 8080

# 前台运行 Nginx，交给 Docker 管理进程生命周期。
CMD ["nginx", "-g", "daemon off;"]
