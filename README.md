# 天枢售后智能中枢

一个面向中文电商售后场景的 AI Agent 课程作业 Demo。项目使用 Next.js + assistant-ui 构建前端工作台，FastAPI + LangGraph 编排后端 Agent，并结合 SQLite 演示数据库与本地 RAG 知识库，模拟“订单事实查询 + 售后政策解释 + 工单处理”的完整闭环。

## 项目能力

- 订单状态、支付信息、商品明细、物流轨迹查询
- 商品/SKU 库存、仓库、补货时间查询
- 退款资格结构化预判断
- 售后工单创建与流转查询
- 客户/订单关联工单查询
- 本地 RAG 售后政策检索，返回 citations
- 中文电商售后场景演示问题与数据验收脚本

## 技术栈

```text
frontend/
  Next.js 15
  React 18
  assistant-ui
  Tailwind CSS

backend/
  Python 3.11
  FastAPI
  LangGraph
  LangChain OpenAI-compatible model client
  SQLite demo database
  SQLite FTS RAG index
```

## 目录结构

```text
assistant-ui-langgraph-fastapi/
├─ backend/
│  ├─ app/
│  │  ├─ data/          # schema、数据模型文档、演示问题；SQLite 文件本地生成
│  │  ├─ langgraph/     # Agent、工具、RAG 检索逻辑
│  │  └─ rag_docs/      # official + internal Markdown 知识库
│  └─ scripts/          # 生成数据库、构建 RAG 索引、验收脚本
├─ frontend/
│  ├─ app/
│  └─ components/       # assistant-ui 工作台组件
└─ README.md
```

## 环境要求

- Python 3.11
- Node.js 20+
- Poetry
- pnpm 推荐；npm 也可以
- 一个 OpenAI-compatible Chat Completions 模型接口

## 后端配置

在 `backend` 目录创建 `.env` 文件，可参考 `backend/.env.example`：

```env
OPENAI_API_KEY=your-openai-compatible-api-key
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_MODEL=deepseek-chat
OPENAI_TEMPERATURE=0.2
```

只要服务兼容 OpenAI Chat Completions 风格，一般只需要替换这几个环境变量，不需要改后端代码。

## 前端配置

在 `frontend` 目录创建 `.env.local`，可参考 `frontend/.env.local.example`：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/chat
```

如果前后端都使用默认端口，这个值不用改。

## 首次运行

### 1. 安装后端依赖

```bash
cd backend
poetry install
```

### 2. 生成演示数据库

```bash
poetry run python scripts/generate_demo_db.py
```

会生成：

```text
backend/app/data/demo_ecommerce.sqlite
```

该文件是本地生成物，已被 `.gitignore` 忽略，不会上传到 GitHub。

### 3. 构建 RAG 索引

```bash
poetry run python scripts/build_rag_index.py
```

会读取：

```text
backend/app/rag_docs/official/
backend/app/rag_docs/internal/
```

并生成：

```text
backend/app/data/rag_index.sqlite
```

该文件同样是本地生成物，已被 `.gitignore` 忽略。

### 4. 验收数据和 RAG

```bash
poetry run python scripts/check_demo_db.py
poetry run python scripts/check_rag.py
```

### 5. 启动后端

```bash
poetry run python -m app.server
```

默认地址：

```text
http://localhost:8000
http://localhost:8000/api/chat
```

### 6. 安装并启动前端

推荐 pnpm：

```bash
cd frontend
pnpm install
pnpm dev
```

也可以使用 npm：

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：

```text
http://localhost:3000
```

## 演示问题

打开前端后，可以直接测试：

```text
帮我查一下订单 SO20260514000023 的物流状态
帮我查订单 SO20260514000023，手机号后四位是 2315
SKU 编号 377 现在还有库存吗，什么时候补货？
订单 SO20260514000002 还没发货，能不能直接退款？
七天无理由退货需要满足什么条件？
查一下工单 AS20260514000002 处理到哪一步了？
帮我为订单 SO20260514000026 创建一个质量问题工单，耳机右耳有杂音，手机号是 13800001234
```

更多覆盖全部工具链路的测试问题见：

```text
backend/app/data/DEMO_QUERIES.md
```

## 当前工具

后端 Agent 当前注册的主要工具：

- `query_order_status`
- `query_product_inventory`
- `evaluate_refund_eligibility`
- `create_after_sales_ticket`
- `query_after_sales_ticket`
- `query_refund_policy_rag`
- `query_refund_policy`
- `query_shipment_tracking`
- `query_customer_tickets`

推荐调用逻辑：

- 用户问订单、物流、支付、商品明细：查 SQLite。
- 用户问库存、补货：查 SQLite。
- 用户问“这个订单能不能退”：先做结构化资格判断，再检索 RAG 政策。
- 用户问凭证、规则、时效、例外情况：走 `query_refund_policy_rag`。
- 用户要创建售后：信息齐全后创建工单。

## 数据与 RAG 说明

SQLite 数据库由脚本生成，模拟：

- 5,000 名客户
- 800+ 商品 SPU
- 2,000+ SKU
- 20,000 订单
- 50,000+ 订单明细
- 3,000+ 售后工单
- 物流轨迹、退款、换货、补偿、凭证附件等关联数据

RAG 第一阶段只使用本地 Markdown：

- `backend/app/rag_docs/official/`：官方法规/规则摘要
- `backend/app/rag_docs/internal/`：项目内部售后 SOP

不会访问外部搜索，也不会依赖在线数据集。

## GitHub 上传说明

本项目已忽略本地大文件和可再生成文件：

```text
frontend/node_modules/
frontend/.next/
frontend/package-lock.json
backend/app/data/*.sqlite
backend/.env
frontend/.env.local
```

所以你本地可以保留 `node_modules`、`.next`、SQLite 数据库和环境变量文件；正常 `git add .` 不会把它们上传。

如果 clone 到新机器，需要重新执行：

```bash
cd backend
poetry install
poetry run python scripts/generate_demo_db.py
poetry run python scripts/build_rag_index.py

cd ../frontend
pnpm install
pnpm dev
```

## 许可与致谢

本项目基于 MIT License 发布。

原始项目来源：

- https://github.com/hminle/langserve-assistant-ui
- https://github.com/Yonom/assistant-ui-langgraph-fastapi

原始版权声明保留在 `LICENSE` 中。本项目新增的中文电商售后场景、SQLite 演示库、RAG 知识库、工具逻辑和前端工作台由 ForeseeXZ 维护。
