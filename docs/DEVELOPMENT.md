# 本地开发说明

## 环境要求

- Python 3.10+
- Node.js 18+ 与 npm

## 后端

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

在 Django Admin（http://127.0.0.1:8000/admin/）中将超级用户的 **role** 设为 **admin**（默认可能是 student）。专家、管理员账号也可在后台创建，并把 **role** 设为 `expert` 或 `admin`。

- API 前缀：`/api/`
- 认证：`/api/auth/login/` 等（Session + CSRF）
- 开发时前端通过 Vite 代理访问后端，无需单独配置跨域 Cookie

## 前端

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 Vite 提示的地址（一般为 http://127.0.0.1:5173），接口会代理到 http://127.0.0.1:8000。

## 典型业务流程

1. **管理员**：竞赛管理 → 新建/发布竞赛 → 分配专家 → 报名审核 → 状态改为「评审中」→ 公告管理（可设红点提醒）。
2. **学生**：注册/登录 → 竞赛报名 → 审核通过后提交作品 → 查看公告。
3. **专家**：评审任务 → 进入竞赛 → 对作品打分（竞赛为「评审中」时可提交/修改评分）。

## 数据与上传

- 开发数据库：SQLite（`backend/db.sqlite3`）
- 上传文件：`backend/media/`（开发环境由 Django 在 `DEBUG=True` 时提供访问）
