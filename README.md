# 空压机能效计算系统（优化版）

基于原项目 air_cal_v3 的现代化重构：**FastAPI** 后端 + **Vue 3** 前端，保留全部业务功能。

## 功能概览

- 用户注册、登录、退出、忘记密码（邮件重置）
- 首页动态（发帖、列表）
- 用户主页
- **客户机（原有设备）**：添加、列表、修改、删除
- **供应商机（新设备）**：添加、列表、修改、删除
- **对比关系**：选择客户机与供应商机建立对比
- **能效计算**：勾选对比项生成 Excel（原有设备一览、原有设备能耗、能效对比）
- 下载生成的 Excel 报表

## 技术栈

- **后端**: FastAPI、SQLAlchemy 2、Pydantic、JWT、Bcrypt、Pandas、OpenPyXL
- **前端**: Vue 3、Vite、Vue Router、Pinia、Axios、Bootstrap 5
- **数据库**: SQLite（无需安装，开箱即用）
- **运行**: Conda 虚拟环境（后端）、Node.js（前端）

## 环境准备

### 1. Conda 环境（后端）

```bash
cd /Users/nexusg/PycharmProject/AirComp
conda env create -f environment.yml
conda activate aircomp
```

若已存在环境，可只安装后端依赖：

```bash
conda activate aircomp
pip install -r backend/requirements.txt
```

### 2. 数据库（SQLite）

- 使用 **SQLite**，无需安装数据库。首次启动后端会在 `backend/` 下自动创建 `aircomp.db` 并建表。
- 可选：在 `backend/` 下创建 `.env`（可复制 `backend/.env.example`），配置 `SECRET_KEY`、`FRONTEND_ORIGIN`、`SQLITE_PATH` 等。

### 3. 前端依赖（Node 18+）

```bash
cd frontend
npm install
```

## 启动

### 终端 1：后端（Conda 环境）

```bash
cd /Users/nexusg/PycharmProject/AirComp
conda activate aircomp
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

首次启动会自动建表。

### 终端 2：前端

```bash
cd /Users/nexusg/PycharmProject/AirComp/frontend
npm run dev
```

浏览器访问：**http://localhost:5173**。前端会通过 Vite 代理将 `/api` 请求转发到后端 8080 端口。

## 目录结构

```
AirComp/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/              # 路由：auth, posts, machines, calculate
│   │   ├── core/             # 配置、安全
│   │   ├── db/               # 数据库会话
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── schemas/          # Pydantic 模型
│   │   ├── services/         # 计算逻辑、邮件
│   │   ├── download/         # 生成的 Excel 输出目录
│   │   └── main.py
│   ├── requirements.txt
│   ├── aircomp.db            # SQLite 数据库（运行后自动生成）
│   └── .env.example
├── frontend/                 # Vue 3 + Vite
│   ├── src/
│   │   ├── api/
│   │   ├── router/
│   │   ├── stores/
│   │   └── views/
│   ├── package.json
│   └── vite.config.js
├── environment.yml           # Conda 环境
└── README.md
```

## 故障排查

### 智能解析一直「识别中」、后台没有任何输出

1. **确认请求是否到达后端**  
   重启后端后，每次有请求进来，终端应出现类似：  
   `[AirComp] POST /api/machines/smart-parse`  
   若点击「解析并填入表单」后**始终没有**这行，说明请求没到当前这个后端进程。

2. **让请求走 Vite 代理（推荐）**  
   在 `frontend/.env.development` 中**注释掉或删除** `VITE_API_BASE` 这一行（或设为空），保存后**重启前端**（`npm run dev`）。  
   这样前端会请求同源的 `/api/`，由 Vite 代理转发到 `vite.config.js` 里配置的后端地址（默认 8081），避免直连跨域或连错端口。

3. **确认后端端口一致**  
   - 用 `bash run_backend.sh` 启动时，后端在 **8081** 端口。  
   - `frontend/vite.config.js` 里 proxy 的 `target` 需为 `http://127.0.0.1:8081`。  
   若你改过后端端口，请同时改 vite 的 proxy 和（若使用直连）`.env.development` 里的 `VITE_API_BASE`。

4. **浏览器控制台**  
   打开 F12 → Console，点击解析时会出现 `[AirComp] 智能解析请求 URL: ...`，可确认实际请求地址；Network 里看该请求是否发出、状态码和响应。

## 说明

- 管理员：`user_id = 999` 可查看所有客户机数据（与蓝本一致）。
- 邮件重置密码需在 `.env` 中配置 `MAIL_USERNAME`、`MAIL_PASSWORD`、`MAIL_FROM`（如 QQ 邮箱 + 授权码）。
