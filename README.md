# assistant-ui-langgraph-fastapi

这是一个面向中文电商售后场景的智能客服 Agent 演示系统，保留了原始项目的整体骨架：

- 前端：Next.js + assistant-ui 聊天界面
- 后端：FastAPI + LangGraph Agent
- 模型：OpenAI-compatible API
- 数据：本地 JSON mock 数据

当前 demo 已替换为中文电商售后场景，支持以下工具闭环：

- 订单状态查询
- 商品库存查询
- 退款规则查询
- 售后工单创建

## 适合的用途

- 课程作业展示
- 本地快速演示 Agent + 工具调用
- 不依赖真实业务系统的中文客服原型验证

## 环境要求

- Python 3.11
- Node.js 20+
- 推荐使用 `poetry`
- 前端可使用 `pnpm` 或 `npm`

## 目录结构

```text
assistant-ui-langgraph-fastapi/
├─ backend/   # FastAPI + LangGraph + 本地 mock 数据
└─ frontend/  # Next.js + assistant-ui 中文客服界面
```

## 需要配置什么环境

### 1. 后端模型环境变量

在 `backend` 目录创建 `.env` 文件，可直接参考 [backend/.env.example](backend/.env.example)：

```env
OPENAI_API_KEY=your-openai-compatible-api-key
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_MODEL=deepseek-chat
OPENAI_TEMPERATURE=0.2
```

这四个变量里，必须至少配置：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

说明：

- 这里接的是 OpenAI-compatible API，不要求必须是 OpenAI 官方接口。
- 只要服务端兼容 OpenAI Chat Completions 风格，`langchain-openai` 这套初始化方式就能直接接。
- 如果你换别的中文模型服务，通常只需要改这三个环境变量，不需要改代码结构。

### 2. 前端环境变量

在 `frontend` 目录创建 `.env.local`，参考 [frontend/.env.local.example](frontend/.env.local.example)：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/chat
```

如果前后端都跑在本机默认端口，这个值一般不用改。

## 本地启动步骤

### 1. 启动后端

```bash
cd backend
poetry install
poetry run python -m app.server
```

默认监听：

- `http://localhost:8000`
- 聊天接口：`http://localhost:8000/api/chat`

### 2. 启动前端

如果你用 `pnpm`：

```bash
cd frontend
pnpm install
pnpm dev
```

如果你用 `npm`：

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：

- `http://localhost:3000`

## 你改完后怎么跑起来

按下面顺序即可：

1. 先在 `backend/.env` 配好模型接口
2. 启动后端 `poetry run python -m app.server`
3. 在 `frontend/.env.local` 确认后端地址
4. 启动前端 `pnpm dev`
5. 打开 `http://localhost:3000`

进入页面后，可以直接测试这些示例问题：

- `帮我查一下订单 SO20260418001 的物流状态`
- `SKU2001 现在还有库存吗，什么时候补货？`
- `数码产品质量问题可以怎么退款？`
- `帮我为订单 SO20260417008 创建一个质量问题售后工单`

## 当前实现说明

后端 mock 数据位于：

- [backend/app/data/orders.json](backend/app/data/orders.json)
- [backend/app/data/products.json](backend/app/data/products.json)
- [backend/app/data/refund_rules.json](backend/app/data/refund_rules.json)
- [backend/app/data/tickets.json](backend/app/data/tickets.json)

你后续如果要改成自己的课程题目数据，只需要替换这些 JSON 文件即可。

## 后续可选优化

如果你还有一点时间，但又不想把系统做重，可以继续加这几项：

- 把本地 JSON 换成 SQLite
- 给工单创建补一个“查询工单状态”工具
- 增加退货地址查询、优惠补偿说明等常见售后工具
- 补一个“演示模式数据说明”侧边栏

## 许可与致谢

本项目基于 MIT License 发布。

原始项目来源：

- https://github.com/hminle/langserve-assistant-ui
- https://github.com/Yonom/assistant-ui-langgraph-fastapi

原始版权声明保留在 [LICENSE](LICENSE) 中，本项目新增的中文电商售后场景、mock 数据、工具逻辑和界面改造由 ForeseeXZ 维护。更多说明见 [NOTICE](NOTICE)。
