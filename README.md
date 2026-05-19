# 并夕夕购物智能售后平台

这是一个面向中文电商售后场景的 AI Agent 课程作业 Demo。项目使用 Next.js + assistant-ui 构建前端工作台，FastAPI + LangGraph 编排后端 Agent，并结合 SQLite 演示数据库与本地 RAG 知识库，模拟“订单事实查询、售后政策解释、工单创建与进度跟踪”的完整流程。

## 项目能力

- 查询订单状态、支付信息、商品明细、物流轨迹
- 查询商品/SKU 库存、仓库、补货时间
- 基于订单事实做退款资格预判断
- 创建售后工单，查询工单流转、退款、换货、补偿记录
- 通过本地 RAG 知识库检索售后政策、所需凭证、处理时效和例外情况
- 提供演示数据库生成脚本、RAG 索引构建脚本和验收脚本

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
│  │  ├─ data/          # schema、数据模型文档、演示问题；SQLite 文件本地生成或拷贝
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

## 环境变量

后端在 `backend/.env` 中配置模型接口，可参考 `backend/.env.example`：

```env
OPENAI_API_KEY=your-openai-compatible-api-key
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_MODEL=deepseek-chat
OPENAI_TEMPERATURE=0.2
```

前端在 `frontend/.env.local` 中配置聊天接口，可参考 `frontend/.env.local.example`：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/chat
```

## 运行方式 A：从脚本生成数据

适合第一次完整复现项目，或者没有拿到现成 SQLite 文件的情况。

### 1. 安装后端依赖

```bash
cd backend
poetry install
```

### 2. 生成演示数据库

```bash
poetry run python scripts/generate_demo_db.py
```

生成文件：

```text
backend/app/data/demo_ecommerce.sqlite
```

### 3. 构建 RAG 索引

```bash
poetry run python scripts/build_rag_index.py
```

该脚本会读取：

```text
backend/app/rag_docs/official/
backend/app/rag_docs/internal/
```

生成文件：

```text
backend/app/data/rag_index.sqlite
```

### 4. 验收数据和 RAG

```bash
poetry run python scripts/check_demo_db.py
poetry run python scripts/check_rag.py
```

## 运行方式 B：直接使用组内共享数据

适合组内成员已经拿到以下文件的情况，可以省略“生成数据库”和“构建 RAG 索引”两个步骤：

```text
demo_ecommerce.sqlite
rag_index.sqlite
```

把这两个文件放到：

```text
backend/app/data/demo_ecommerce.sqlite
backend/app/data/rag_index.sqlite
```

然后只需要安装依赖并启动服务：

```bash
cd backend
poetry install
poetry run python scripts/check_demo_db.py --skip-tools
poetry run python scripts/check_rag.py
poetry run python -m app.server
```

如果只是快速跑 Demo，也可以先跳过两个验收脚本，直接启动后端。遇到查询失败时，再确认这两个 SQLite 文件是否放在正确目录。

## 启动后端

```bash
cd backend
poetry run python -m app.server
```

默认地址：

```text
http://localhost:8000
http://localhost:8000/api/chat
```

## 启动前端

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

更多测试问题见：

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

- 订单、物流、支付、商品明细：查询 SQLite。
- 库存、补货：查询 SQLite。
- “这个订单能不能退”：先做结构化资格判断，再检索 RAG 政策。
- 凭证、规则、时效、例外情况：走 `query_refund_policy_rag`。
- 创建售后：信息齐全后创建工单。

## 数据与 RAG 说明

SQLite 数据库模拟：

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

当前 RAG 不访问外部搜索，也不依赖在线数据集。

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

所以本地可以保留依赖目录、构建缓存、SQLite 数据库和环境变量文件；正常提交不会上传这些内容。组内共享 SQLite 文件时，建议单独通过网盘、压缩包或课程平台附件传递。

## 许可与致谢

本项目基于 MIT License 发布。

原始项目来源：

- https://github.com/hminle/langserve-assistant-ui
- https://github.com/Yonom/assistant-ui-langgraph-fastapi

原始版权声明保留在 `LICENSE` 中。本项目新增的中文电商售后场景、SQLite 演示库、RAG 知识库、工具逻辑和前端工作台由 ForeseeXZ 维护。
