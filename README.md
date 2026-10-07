# StyleMate 后端

AI 穿搭助手的后端服务 —— 基于 FastAPI + Supabase + 通义千问，提供用户认证、衣柜管理、AI 搭配推荐等 API。

## 🔗 线上地址

- **API 入口**：https://stylemate-production.up.railway.app
- **接口文档（Swagger）**：https://stylemate-production.up.railway.app/docs
- **健康检查**：https://stylemate-production.up.railway.app/health

## 🔗 相关仓库

- **前端仓库**：https://github.com/xuedi-cn/stylemate-frontend
- **线上体验**：https://stylemate-frontend.vercel.app

## 🏗️ 技术栈

| 层 | 技术 |
|---|---|
| Web 框架 | FastAPI 3.x |
| 数据库 | Supabase（PostgreSQL） |
| 认证 | Supabase Auth（JWT） |
| 对象存储 | 腾讯云 COS |
| AI 模型 | 通义千问（qwen-vl-plus / qwen-plus） |
| 部署 | Railway |

## ✨ 核心功能

- **用户认证**：注册 / 登录 / JWT 校验（三层权限防御）
- **单品管理**：上传衣柜单品 → 通义千问视觉模型自动识别品类、颜色、材质、风格标签
- **风格参考图**：上传喜欢的穿搭图 → AI 提取风格偏好
- **AI 搭配推荐**：Agent 调用多工具（衣柜 + 风格 + 收藏），生成 3 套个性化搭配
- **收藏系统**：保存喜欢的搭配，作为后续推荐的偏好参考

## 📁 项目结构

```
stylemate/
├── app/
│   ├── __init__.py
│   ├── main.py          # 入口 + 路由挂载 + CORS
│   ├── config.py        # 环境变量读取
│   ├── deps.py          # JWT 验证依赖
│   ├── auth.py          # 注册 / 登录
│   ├── items.py         # 单品上传 / 查询 / 删除
│   ├── styles.py        # 风格参考图上传 / 查询 / 删除
│   ├── outfits.py       # 搭配推荐 / 保存 / 查询
│   ├── storage.py       # 腾讯云 COS 封装
│   ├── ai.py            # AI 能力（视觉分析 + Agent）
│   └── tools.py         # Agent 可调用的工具函数
├── requirements.txt
├── railway.toml         # Railway 部署配置
└── .env                 # 本地环境变量（不提交）
```

### 1. 克隆仓库

```
git clone https://github.com/xuedi-cn/stylemate.git
cd stylemate
```

### 2. 创建虚拟环境

```bash
python -m venv venv
# Windows
venv\\Scripts\\activate
# Mac / Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装依赖

```
pip install -r requirements.txt
```


### 4. 配置环境变量

在根目录创建 `.env`，填入：

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=sb_publishable_xxx
SUPABASE_SERVICE_KEY=sb_secret_xxx
COS_SECRET_ID=xxx
COS_SECRET_KEY=xxx
COS_BUCKET=xxx
COS_REGION=ap-guangzhou
DASHSCOPE_API_KEY=sk-xxx
```

### 5. 启动服务

```
python -m uvicorn app.main:app --reload
```


访问 http://127.0.0.1:8000/docs 查看接口文档。

## 🔐 权限设计（三层防御）

1. **API 层**：`get_current_user` 依赖，验证 JWT，未登录返回 401
2. **业务层**：所有查询强制 `.eq("user_id", user.id)`，防止越权
3. **数据库层**：Supabase RLS 兜底，后端用 `service_role` key 绕过 RLS 做业务操作

## 🧠 AI Agent 架构

推荐搭配时，Agent 会：

1. 调用 `query_items` → 查用户衣柜
2. 调用 `query_style_refs` → 查风格偏好
3. 主动注入**收藏搭配**到 prompt（不走工具，减少不确定性）
4. LLM 综合推理 → 返回 3 套结构化搭配（`name` / `item_ids` / `reason`）

## 📄 License

MIT
