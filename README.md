# 竞赛管理系统（jingsai）

优秀的系统 — Django 5 + Django REST Framework 后端，Vite + Vue 3 + Element Plus 前端。三种角色：学生、管理员、专家。

## 环境要求

- Python 3.10+
- Node.js 18+ 与 npm（用于前端）

## 后端

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

在 Django Admin（`http://127.0.0.1:8000/admin/`）中将超级用户的 **role** 设为 **admin**（默认可能是 student）。专家、管理员账号也可在后台创建，并把 **role** 设为 `expert` 或 `admin`。

```powershell
python manage.py runserver 0.0.0.0:8000
```

API 前缀：`/api/`；认证：`/api/auth/login/` 等（Session + CSRF）。开发时前端通过 Vite 代理访问后端，无需单独配置跨域 Cookie。

## 前端

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 Vite 提示的地址（一般为 `http://127.0.0.1:5173`）。接口会代理到 `http://127.0.0.1:8000`。

## 典型流程

1. **管理员**：登录 → 竞赛管理 → 新建竞赛（状态可先为「草稿」再改为「进行中」）→ 分配专家 → 报名审核 → 将竞赛状态改为「评审中」供专家打分 → 公告管理发布通知。
2. **学生**：注册/登录 → 竞赛列表报名 → 审核通过后「我的作品」提交（可传附件或链接）。
3. **专家**：评审任务 → 进入竞赛 → 对作品打分（仅当竞赛状态为「评审中」时允许提交/修改评分）。

## 目录说明

- `backend/`：Django 项目、`apps/accounts`（用户与认证）、`apps/competitions`（业务模型与 API）。
- `frontend/`：Vue 单页应用。

上传文件保存在 `backend/media/`（开发环境由 Django 提供访问）。

## 一键部署（Docker，界面与功能不变）

生产环境通过 **Nginx 同域反代** 提供前端页面与 `/api`、`/media`，与开发时 Vite 代理行为一致，**无需修改 Vue 页面**。

### 要求

- 已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（Windows/macOS）或 Docker Engine + Compose（Linux）

### 启动

**Windows（PowerShell）：**

```powershell
cd code
.\deploy.ps1
```

**Linux / macOS：**

```bash
cd code
chmod +x deploy.sh
./deploy.sh
```

首次运行会自动从 `.env.example` 生成 `.env`。默认访问：**http://localhost:8080**

### 创建管理员

```bash
docker compose exec api python manage.py createsuperuser
```

登录后打开 **http://localhost:8080/admin/**，将用户的 **role** 设为 **admin**（或通过后台创建专家/管理员账号）。

### 常用命令

```bash
docker compose logs -f          # 查看日志
docker compose down             # 停止并移除容器
docker compose down -v          # 同时删除数据库与上传卷（慎用）
docker compose up -d --build    # 重新构建并启动
```

### 配置说明（`.env`）

| 变量 | 说明 |
|------|------|
| `PUBLIC_ORIGIN` | 浏览器访问的完整根地址，须与 `WEB_PORT` 一致（CSRF） |
| `WEB_PORT` | 宿主机映射端口，默认 `8080` |
| `DJANGO_SECRET_KEY` | 生产环境务必改为随机长字符串 |
| `POSTGRES_*` | 内置 PostgreSQL 账号库名，一般保持默认即可 |

上传附件与数据库分别保存在 Docker 卷 `media`、`pgdata` 中，重启容器不会丢失。

### 与本地开发的区别

| | 本地开发 | Docker 部署 |
|--|----------|-------------|
| 前端 | Vite `:5173` | Nginx `:8080` |
| 后端 | `runserver :8000` | Gunicorn（容器内） |
| 数据库 | SQLite | PostgreSQL |
| 配置 | `settings.py` 默认 `DEBUG=True` | `.env` 中 `DJANGO_DEBUG=false` |

本地开发方式不变，仍可按上文「后端」「前端」章节分别启动。
