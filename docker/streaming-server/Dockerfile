FROM debian:bookworm-slim

RUN apt-get update \
	&& apt-get install -y --no-install-recommends nginx libnginx-mod-rtmp ca-certificates \
	&& rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 1935 8080

CMD ["nginx", "-g", "daemon off;"]
