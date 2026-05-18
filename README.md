# 竞赛管理系统（jingsai）

Django + Vue 3 竞赛管理平台，支持**学生 / 管理员 / 专家**三种角色：报名、作品提交、评审、公告与红点提醒等。

## 项目结构

```
jingsai/
├── backend/              # Django API（apps/accounts、apps/competitions）
├── frontend/             # Vue 3 + Element Plus 单页应用
├── deploy/               # Docker / Nginx 配置与一键脚本
├── docs/                 # 开发与部署说明（详细步骤见此处）
├── docker-compose.yml    # 生产一键部署
├── .env.example          # 部署环境变量模板
├── deploy.ps1            # Windows 一键部署
└── deploy.sh             # Linux/macOS 一键部署
```

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

浏览器打开 **http://127.0.0.1:5173**。首次使用请在 Django Admin 创建用户并将 `role` 设为 `admin` / `expert` / `student`。

更完整的步骤、账号说明与业务流程见 **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)**。

## 一键部署（Docker）

```powershell
.\deploy.ps1
```

默认访问 **http://localhost:8080**。详见 **[docs/DEPLOY.md](docs/DEPLOY.md)**。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django 5、Django REST Framework、Session 认证 |
| 前端 | Vue 3、Vite、Pinia、Element Plus |
| 部署 | Docker Compose、Nginx、PostgreSQL、Gunicorn |
