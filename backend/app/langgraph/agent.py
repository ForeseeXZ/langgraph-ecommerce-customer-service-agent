import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.errors import NodeInterrupt
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from .state import AgentState
from .tools import tools

load_dotenv()

DEFAULT_SYSTEM_PROMPT = """
你是“并夕夕购物智能售后平台”的中文电商售后专家 Agent，服务风格要专业、简洁、礼貌。

你可以使用以下工具：
- query_order_status: 查询订单状态、支付信息、商品明细、物流信息、物流轨迹和售后状态
- query_product_inventory: 按商品编号、商品名称或 SKU 编号查询库存、仓库和补货时间
- evaluate_refund_eligibility: 基于订单事实预判断退款资格
- create_after_sales_ticket: 创建售后工单
- query_after_sales_ticket: 查询售后工单状态、流转记录、退款、换货和补偿信息
- query_refund_policy_rag: 从本地 Markdown RAG 知识库查询售后政策、凭证、时效、例外情况，并返回 citations
- query_refund_policy: 查询退款或退换货参考规则
- query_shipment_tracking: 查询物流轨迹详情
- query_customer_tickets: 查询客户或订单关联的售后工单

你的职责：
1. 优先理解用户的售后诉求，例如物流进度、库存补货、退款资格、退款规则、售后工单进度。
2. 只要问题涉及订单、库存、退款资格、售后政策、退款规则或工单处理，优先调用工具，不要编造业务数据或政策条款。
3. 用户询问政策、所需凭证、处理时效、例外情况、不适用条件、SLA 或工单优先级时，优先调用 query_refund_policy_rag，并在回答中保留工具返回的引用依据。
4. 用户问“这个订单能不能退”“能不能退款”这类带订单事实的问题时，先调用 evaluate_refund_eligibility；然后调用 query_refund_policy_rag 补充政策依据。
5. query_refund_policy 仅作为旧版结构化退款规则兼容工具；复杂政策解释优先使用 query_refund_policy_rag。
6. 用户要创建售后时，确认有订单号、问题类型、问题描述和联系方式后调用 create_after_sales_ticket。
7. 工具返回后，简短引导用户查看结构化卡片，再给出下一步建议；不要把工具返回的结构化数据重复输出成表格。如果 RAG 返回 not_found，不要自行补写政策。
8. 信息不足时，明确告诉用户还需要什么，例如订单号、SKU 编号、手机号后四位或联系方式。
9. 这是课程作业演示系统，不承诺真实发货、真实退款或真实人工回访，只说明当前结果来自演示数据即可。
""".strip()


def create_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", "demo-key"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
    )


model = create_model()


def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return END
    else:
        return "tools"


class AnyArgsSchema(BaseModel):
    # By not defining any fields and allowing extras,
    # this schema will accept any input passed in.
    class Config:
        extra = "allow"


class FrontendTool(BaseTool):
    def __init__(self, name: str):
        super().__init__(name=name, description="", args_schema=AnyArgsSchema)

    def _run(self, *args, **kwargs):
        # Since this is a frontend-only tool, it might not actually execute anything.
        # Raise an interrupt or handle accordingly.
        raise NodeInterrupt("This is a frontend tool call")

    async def _arun(self, *args, **kwargs) -> str:
        # Similarly handle async calls
        raise NodeInterrupt("This is a frontend tool call")


def get_tool_defs(config):
    frontend_tools = [
        {"type": "function", "function": tool}
        for tool in config["configurable"]["frontend_tools"]
    ]
    return tools + frontend_tools


def get_tools(config):
    frontend_tools = [
        FrontendTool(tool.name) for tool in config["configurable"]["frontend_tools"]
    ]
    return tools + frontend_tools


async def call_model(state, config):
    system = config["configurable"].get("system") or DEFAULT_SYSTEM_PROMPT

    messages = [SystemMessage(content=system)] + state["messages"]
    model_with_tools = model.bind_tools(get_tool_defs(config))
    response = await model_with_tools.ainvoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": response}


async def run_tools(input, config, **kwargs):
    tool_node = ToolNode(get_tools(config))
    return await tool_node.ainvoke(input, config, **kwargs)


# Define a new graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", run_tools)

workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    ["tools", END],
)

workflow.add_edge("tools", "agent")

assistant_ui_graph = workflow.compile()
