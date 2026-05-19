export const EXAMPLE_QUESTIONS = [
  "帮我查一下订单 SO20260514000023 的物流状态",
  "帮我查订单 SO20260514000023，手机号后四位是 2315",
  "SKU 编号 377 现在还有库存吗，什么时候补货？",
  "订单 SO20260514000002 还没发货，能不能直接退款？",
  "七天无理由退货需要满足什么条件？",
  "查一下工单 AS20260514000002 处理到哪一步了？",
  "帮我为订单 SO20260514000026 创建一个质量问题工单，耳机右耳有杂音，手机号是 13800001234",
];

export const TOOL_GROUPS = [
  {
    title: "结构化查询",
    items: ["订单物流", "库存补货", "工单进度"],
  },
  {
    title: "售后决策",
    items: ["退款资格", "RAG 政策", "SLA 优先级"],
  },
  {
    title: "业务动作",
    items: ["创建工单", "查询客户售后", "物流轨迹"],
  },
];

export const WORKBENCH_METRICS = [
  { label: "订单事实", value: "SQLite", detail: "20k 演示订单" },
  { label: "政策知识", value: "RAG", detail: "官方资料 + SOP" },
  { label: "智能编排", value: "LangGraph", detail: "多工具决策链" },
];

export const ASSISTANT_INSTRUCTIONS = `
你是“并夕夕购物智能售后平台”的中文电商售后专家 Agent。
优先围绕订单状态、库存、退款资格、退款规则和售后工单处理来回答。
涉及业务数据时必须优先调用工具，不要凭空编造订单、库存、退款或工单信息。
用户询问退款资格时，先调用 evaluate_refund_eligibility。
用户询问政策、凭证、时效、例外情况或工单优先级时，优先调用 query_refund_policy_rag。
用户询问工单进度或退款到账时，优先调用 query_after_sales_ticket。
工具返回后，简短引导用户查看结构化卡片，再给出下一步建议；不要把卡片里的结构化数据重复输出成表格。
`.trim();
