# 竞赛管理系统（jingsai）

Django + Vue 3 竞赛管理平台，支持**学生 / 管理员 / 专家**三种角色：报名、作品提交、评审、公告与红点提醒等。

## 项目结构

```
jingsai/
├── backend/              # Django API
├── frontend/             # Vue 3 单页应用
├── deploy/               # 部署脚本、Nginx、环境变量模板
├── docs/                 # 详细文档
├── docker-compose.yml    # Docker 编排（在仓库根目录执行 compose）
├── README.md
└── .gitignore
```

根目录只保留 Git / Docker 必需项；**不要把 backend、frontend 再套一层父文件夹**，否则路径、`docker compose`、Vite 代理都会失效。

## 快速开始（本地开发）

**环境：** Python 3.10+、Node.js 18+

```powershell
# 终端 1 — 后端
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# 终端 2 — 前端
cd frontend
npm install
npm run dev
```

浏览器打开 **http://127.0.0.1:5173**。详见 **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)**。

## 一键部署（Docker）

在**仓库根目录**执行：

```powershell
.\deploy\deploy.ps1
```

默认访问 **http://localhost:8080**。详见 **[docs/DEPLOY.md](docs/DEPLOY.md)**。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django 5、DRF、Session 认证 |
| 前端 | Vue 3、Vite、Pinia、Element Plus |
| 部署 | Docker Compose、Nginx、PostgreSQL、Gunicorn |
