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

当前推荐运行方式是 Docker host 网络模式。容器直接复用宿主机网络，可通过
`127.0.0.1` 访问宝塔创建的 MySQL，避免额外配置 Docker 网段的 MySQL 授权。
对外访问仍建议统一由宝塔/Nginx 提供 HTTPS。

MySQL 仍然使用宝塔面板创建和管理。

```bash
cp .env.example .env
vim .env
bash deploy.sh
```

`.env` 中的 `DATABASE_URL` 示例:

```text
DATABASE_URL=mysql+pymysql://iot_server:你的数据库密码@127.0.0.1:3306/iot_server
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

## 账号与设备归属

容器启动时会自动创建以下安全相关数据表:

- `users`: 保存账号、显示名称、密码盐值和 PBKDF2 密码哈希，不保存明文密码。
- `user_sessions`: 只保存会话 Token 的 SHA-256 哈希和过期时间，不保存明文 Token。
- `user_device_bindings`: 保存 `user_id` 与 `device_id` 的绑定关系。

登录流程:

1. 前端通过 `/api/auth/login` 登录，或通过 `/api/auth/register` 创建账号。
2. 后端校验密码哈希后设置 `vitam_session` HttpOnly Cookie。
3. 前端访问设备列表、历史、服务发布接口时由浏览器自动携带 Cookie，前端 JS 不保存明文 Token。
4. 后端根据当前 `user_id` 过滤设备，只展示并控制该用户绑定的设备。

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
docker compose --env-file .env up -d --build
```

容器启动时会自动执行数据库初始化，成功后再启动 Web 服务。

6. 宝塔网站中新建 `api.hyrain.xyz`，开启 HTTPS。
7. 反向代理 `https://api.hyrain.xyz` 到 `http://127.0.0.1:8000`。
8. EMQX Webhook URL 使用 `https://api.hyrain.xyz/api/iot/emqx/property`。

## Manual commands

手动初始化数据表:

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
