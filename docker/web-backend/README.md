# Web Backend

This service receives EMQX Webhook messages, stores device property reports in
MySQL, and serves the first device preview page.

## Responsibilities

- Provide web admin APIs.
- Receive EMQX property report Webhooks.
- Store the latest device status in MySQL.
- Keep raw property history for debugging and later charts.
- Serve a simple device preview page.

## Runtime

当前推荐运行方式是 Docker bridge 模式。容器只把 Web 服务绑定到宿主机
`127.0.0.1:${APP_PORT:-8000}`，由宝塔/Nginx 反向代理对外提供 HTTPS。
容器通过 `host.docker.internal` 访问宝塔创建的 MySQL。

MySQL 仍然使用宝塔面板创建和管理。

```bash
cp .env.example .env
vim .env
bash deploy.sh
```

`.env` 中的 `DATABASE_URL` 示例:

```text
DATABASE_URL=mysql+pymysql://iot_server:你的数据库密码@host.docker.internal:3306/iot_server
```

## EMQX Webhook 入库

EMQX 规则 SQL:

```sql
SELECT topic, payload, timestamp FROM "vitam/devices/+/property/post"
```

Webhook:

```text
POST https://api.hyrain.xyz/api/iot/emqx/property
```

Request body:

```json
{
	"topic": "${topic}",
	"payload": "${payload}",
	"timestamp": "${timestamp}"
}
```

The backend writes:

- `devices`: device identity and metadata.
- `device_latest_status`: latest state used by the preview page.
- `device_property_history`: raw property report history.

## 宝塔部署

1. 宝塔软件商店安装 MySQL，创建数据库 `iot_server` 和用户 `iot_server`。
2. 在服务器上 `git clone` 项目。
3. 进入 `docker/web-backend`。
4. 复制 `.env.example` 为 `.env`，把数据库密码替换成真实密码。
5. 执行:

```bash
bash deploy.sh
```

脚本会执行:

```bash
docker compose --env-file .env build
docker compose --env-file .env run --rm web-backend python -m src.init_db
docker compose --env-file .env up -d --build
```

6. 宝塔网站中新建 `api.hyrain.xyz`，开启 HTTPS。
7. 反向代理 `https://api.hyrain.xyz` 到 `http://127.0.0.1:8000`。
8. EMQX Webhook URL 使用 `https://api.hyrain.xyz/api/iot/emqx/property`。

## Manual commands

初始化数据表:

```bash
docker compose --env-file .env run --rm web-backend python -m src.init_db
```

启动服务:

```bash
docker compose --env-file .env up -d --build
```

查看日志:

```bash
docker compose logs -f web-backend
```

也可以从 `docker/` 根编排文件统一启动多个服务；根编排只组织容器，镜像构建
仍使用本目录的 `Dockerfile`。
