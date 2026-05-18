# Docker 一键部署

生产环境通过 **Nginx 同域反代** 提供前端与 `/api`、`/media`，与开发时 Vite 代理行为一致，**无需修改 Vue 页面**。

## 要求

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)（Windows/macOS）或 Docker Engine + Compose（Linux）

## 启动

在**仓库根目录**执行：

**Windows：**

```powershell
.\deploy\deploy.ps1
```

**Linux / macOS：**

```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

首次运行会自动从 `deploy/.env.example` 在根目录生成 `.env`。默认访问：**http://localhost:8080**

`docker-compose.yml` 保留在仓库根目录，便于直接执行 `docker compose` 命令。

## 创建管理员

```bash
docker compose exec api python manage.py createsuperuser
```

登录 http://localhost:8080/admin/ ，将用户 **role** 设为 **admin**。

## 常用命令

```bash
docker compose logs -f
docker compose down
docker compose down -v          # 同时删除数据库与上传卷（慎用）
docker compose up -d --build
```

## 环境变量（`.env`）

| 变量 | 说明 |
|------|------|
| `PUBLIC_ORIGIN` | 浏览器访问根地址，须与 `WEB_PORT` 一致（CSRF） |
| `WEB_PORT` | 宿主机端口，默认 `8080` |
| `DJANGO_SECRET_KEY` | 生产环境务必改为随机长字符串 |
| `POSTGRES_*` | 内置 PostgreSQL，一般保持默认 |

上传附件与数据库保存在 Docker 卷 `media`、`pgdata` 中。

## 与本地开发的区别

| | 本地开发 | Docker 部署 |
|--|----------|-------------|
| 前端 | Vite `:5173` | Nginx `:8080` |
| 后端 | `runserver :8000` | Gunicorn |
| 数据库 | SQLite | PostgreSQL |
