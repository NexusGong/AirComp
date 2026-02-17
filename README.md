<p align="center">
  <img src="frontend/public/logo.png" alt="AirComp" width="240" />
</p>

# AirComp

**空压机能耗计算与对比系统** — 基于 FastAPI + Vue 3 的现代化应用，支持客户设备与供应商设备维护、能效对比、节能量计算与报告导出。

---

## 功能概览

### 设备与计算

- **客户机（原有设备）**：添加、列表、修改、删除；支持 Excel/CSV 上传或粘贴表格，由智能解析自动填入表单。
- **供应商机（新设备）**：同样支持智能解析与增删改查。
- **对比关系**：在「设备信息」中选择客户机与供应商机建立对比项。
- **能效计算**：在「能耗计算」页勾选对比项，设置年运行小时等参数，一键生成 Excel（原有设备一览、能耗、能效对比）并自动生成可下载的报告记录。

### 分析对话

- 在「新建对话」中通过自然语言上传客户/供应商设备表格，或直接要求「计算某公司某几台机的节能量」，由助手引导选型与计算。

### 账号与权限

- **登录**：支持手机号+验证码、手机号/用户名+密码；注册后可设置密码以便下次密码登录。
- **个人资料 / 修改密码 / 账号权限**：在侧栏用户菜单中通过弹窗完成，无需跳转独立页面。
- **历史报告**：报告列表按时间倒序，可查看详情并下载对应 Excel。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | FastAPI | API 与路由 |
| | SQLAlchemy 2 + Pydantic | 模型与校验 |
| | JWT + Bcrypt | 认证与密码 |
| | Pandas + OpenPyXL | 能耗计算与 Excel 生成 |
| 前端 | Vue 3 + Vite | 应用与构建 |
| | Pinia + Vue Router | 状态与路由 |
| | Axios | 请求封装（含 /api 代理） |
| 数据 | SQLite | 默认库，首次启动在 `backend/` 下自动创建 `aircomp.db` 并建表 |

可选：短信验证码（互亿无线）、豆包大模型（智能解析/分析对话）。均通过 `backend/.env` 配置。

---

## 环境准备

- **Python 与后端依赖**：推荐使用 Conda。从项目根目录执行：
  ```bash
  conda env create -f environment.yml
  conda activate aircomp
  ```
  若环境已存在，可只安装后端依赖：`pip install -r backend/requirements.txt`
- **Node.js**：建议 18+，用于前端。进入 `frontend/` 后执行 `npm install`。
- **数据库**：默认 SQLite，无需单独安装。首次启动后端会自动建表。
- **可选配置**：在 `backend/` 下复制 `.env.example` 为 `.env`，可配置：
  - `SECRET_KEY`、`FRONTEND_ORIGIN`（CORS）
  - 短信：`SMS_ENABLED`、`SMS_ACCOUNT`、`SMS_PASSWORD` 等
  - 豆包：`DOUBAO_API_KEY`、`DOUBAO_API_URL`、`DOUBAO_MODEL`
  - 邮件重置密码（若启用）：`MAIL_USERNAME`、`MAIL_PASSWORD`、`MAIL_FROM`

---

## 启动方式

### 方式一：从项目根目录用脚本启动后端

```bash
./run_backend.sh
```

后端将在 **8081** 端口启动（Conda 环境 `aircomp` 内运行 uvicorn）。

### 方式二：手动分步启动

**终端 1 — 后端**

```bash
cd backend
conda activate aircomp
uvicorn app.main:app --reload --host 0.0.0.0 --port 8081
```

**终端 2 — 前端**

```bash
cd frontend
npm install   # 首次
npm run dev
```

浏览器访问 **http://localhost:5173**。前端通过 Vite 将 `/api` 代理到 `http://127.0.0.1:8081`，无需配置 CORS；若修改后端端口，需同步修改 `frontend/vite.config.js` 中的 proxy `target`。

---

## 项目结构

```
AirComp/
├── backend/
│   ├── app/
│   │   ├── api/           # 路由：auth, posts, machines, calculate, analysis, reports
│   │   ├── core/          # 配置、安全（JWT、密码哈希）
│   │   ├── db/            # 数据库会话与 Base
│   │   ├── models/        # User, Post, 设备、对比、分析、报告
│   │   ├── schemas/       # Pydantic 请求/响应模型
│   │   ├── services/      # 计算逻辑、设备匹配、智能解析、短信、豆包
│   │   ├── download/      # 计算生成的 Excel 临时输出
│   │   ├── reports/       # 报告文件存储
│   │   └── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── aircomp.db         # 运行后自动生成
├── frontend/
│   ├── src/
│   │   ├── api/           # axios 实例与拦截器
│   │   ├── router/        # 路由与鉴权
│   │   ├── stores/        # auth, analysis
│   │   ├── views/         # 登录、分析、设备、数据处理、报告等页面
│   │   ├── components/    # 侧栏、弹窗等
│   │   └── utils/        # 错误信息、表格解析等
│   ├── public/            # 静态资源（如 logo.png）
│   ├── vite.config.js     # 开发代理指向后端 8081
│   └── package.json
├── environment.yml        # Conda 环境定义
├── run_backend.sh         # 一键启动后端（端口 8081）
└── README.md
```

---

## 故障排查

### 智能解析一直「识别中」、后端无任何输出

1. **确认请求是否到达后端**  
   重启后端后，每次请求终端应出现类似：`[AirComp] POST /api/machines/smart-parse`。若点击「解析并填入表单」后始终没有这行，说明请求未到达当前后端进程。

2. **使用 Vite 代理（推荐）**  
   在 `frontend/.env.development` 中注释或删除 `VITE_API_BASE`，保存后重启前端（`npm run dev`），使前端请求同源 `/api/`，由 Vite 转发到 `vite.config.js` 中配置的后端地址（默认 8081）。

3. **端口一致**  
   - 使用 `run_backend.sh` 时后端在 **8081**。  
   - `frontend/vite.config.js` 的 proxy `target` 需为 `http://127.0.0.1:8081`。  
   若修改后端端口，请同时修改 proxy 与（若使用直连）`.env.development` 中的 `VITE_API_BASE`。

4. **浏览器**  
   打开 F12 → Console / Network，可查看请求 URL 与状态码，便于确认是否发出及是否被代理。


