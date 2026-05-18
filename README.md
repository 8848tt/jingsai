# 竞赛管理系统（jingsai）

面向学院场景的 **报名与评审管理系统**：Django REST 后端 + Vue 3 前端，支持学生、管理员、专家三类角色，覆盖竞赛发布、组队报名、审核、作品提交、专家评审、公告与未读提醒等流程。

**仓库地址：** https://github.com/8848tt/jingsai

---

## 实验进度报告

> 更新说明：以下内容对应当前 `main` 分支已实现功能，用于课题阶段汇报与仓库说明。

### 1. 总体进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| 需求分析与建模 | 三类角色、竞赛状态机、队伍/报名/作品/评审/公告数据模型 | 已完成 |
| 后端 API | Django 5 + DRF，Session 认证，权限与业务校验 | 已完成 |
| 前端界面 | Vue 3 + Element Plus，分角色菜单与主要业务页 | 已完成 |
| 主流程联调 | 发布 → 报名 → 审核 → 提交 → 评审 → 查询 | 已跑通 |
| 公告红点提醒 | 提醒范围配置、未读统计、已读标记 | 已完成 |
| 工程化 | Git 托管、`.gitignore`、开发与 Docker 部署文档 | 已完成 |
| 增强功能 | 盲审匿名、排名奖项、成绩导出、参赛档案等 | 规划中 |

### 2. 已实现功能（按角色）

#### 学生端

| 功能 | 说明 |
|------|------|
| 注册 / 登录 | 学生账号注册，Session + CSRF 登录 |
| 竞赛列表 | 浏览已发布竞赛，按标题搜索，查看竞赛相关公告入口 |
| 队伍管理 | 创建队伍（队长）、申请加入队伍、队长审核成员（待审核/通过/拒绝） |
| 报名 | 以队伍为单位提交报名，查看「我的报名」及审核状态 |
| 作品提交 | 多附件上传，结合竞赛状态与时间窗口控制是否可提交 |
| 公告 | 公告列表与详情、附件下载；开启提醒时侧栏与列表显示未读红点，打开详情后标记已读 |

#### 管理员端

| 功能 | 说明 |
|------|------|
| 竞赛管理 | 创建/编辑/删除竞赛；配置报名与比赛时间、队伍人数上限、竞赛状态（草稿/报名中/进行中/报名截止/评审中/已结束等） |
| 专家分配 | 为竞赛关联评审专家；设置每份作品评审专家数量 |
| 报名审核 | 报名列表、按竞赛筛选，更新审核状态（通过/拒绝等） |
| 作品与评分 | 查看提交作品及附件；列表展示作品平均分（基于专家已提交评分） |
| 公告管理 | 全局或竞赛关联公告；多附件；红点提醒（不提醒 / 全体学生 / 本竞赛已报名学生）；竞赛管理页可快速发布公告 |
| 评审分配 | 竞赛进入「评审中」后，从已选专家中为每份作品随机分配若干评审任务 |

#### 专家端

| 功能 | 说明 |
|------|------|
| 评审任务 | 查看被分配竞赛及作品列表 |
| 在线评审 | 下载/查看附件；在「评审中」阶段提交或修改分数与评审意见 |

#### 系统与部署

| 功能 | 说明 |
|------|------|
| 角色权限 | `student` / `admin` / `expert` 接口与对象级权限隔离 |
| 文件存储 | 作品与公告附件存于 `backend/media/`（开发环境由 Django 提供访问） |
| 本地开发 | SQLite + `runserver` + Vite 代理 `/api` |
| 一键部署 | `docker-compose.yml` + `deploy/deploy.ps1`，Nginx 同域反代，PostgreSQL + Gunicorn |

### 3. 主业务流程（当前可演示）

```text
管理员创建并发布竞赛
    → 学生组队、提交报名
    → 管理员审核报名
    → 学生在开放期内提交作品（多附件）
    → 管理员将竞赛设为「评审中」（触发专家分配）
    → 专家对分配作品打分
    → 管理员查看作品平均分
    → 管理员发布公告（可选红点提醒）→ 学生查看并消除未读
```

### 4. 技术实现摘要

| 模块 | 技术选型 |
|------|----------|
| 后端 | Python 3.10+、Django 5、Django REST Framework |
| 前端 | Vue 3、Vite、Vue Router、Pinia、Element Plus、Axios |
| 认证 | SessionAuthentication + CSRF；开发期 Vite 代理，部署期 Nginx 同域 |
| 数据库 | SQLite（开发）/ PostgreSQL（Docker 部署） |
| 核心 App | `apps.accounts`（用户与认证）、`apps.competitions`（业务） |

### 5. 后续计划

- 作品盲审（专家端隐藏学生身份信息）
- 成绩排名、奖项映射与公示导出
- 学生参赛档案与历史查询
- 分材料类型的格式校验与独立上传端口
- 接口与前端自动化测试、性能与安全加固

---

## 项目结构

```
jingsai/
├── backend/              # Django API（apps/accounts、apps/competitions）
├── frontend/             # Vue 3 单页应用
├── deploy/               # 部署脚本、Nginx、.env.example
├── docs/                 # 开发与部署说明
├── docker-compose.yml    # Docker 编排（仓库根目录执行）
├── README.md
└── .gitignore
```

## 快速开始（本地开发）

**环境：** Python 3.10+、Node.js 18+

```powershell
# 终端 1 — 后端
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # 首次；再在 Admin 将 role 设为 admin
python manage.py runserver 0.0.0.0:8000

# 终端 2 — 前端
cd frontend
npm install
npm run dev
```

浏览器打开 **http://127.0.0.1:5173**（接口代理到 `http://127.0.0.1:8000`）。

更完整说明见 **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)**。

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

## 小组成员

| 姓名 | 学号 | 分工 |
|------|------|------|
| 唐堂 | 2025213781 | 后端开发 |
| 王铮 | 2025213770 | 前端开发 |
| 杨滨铖 | 2024213822 | 后端开发 |

指导教师：于凤敏老师
