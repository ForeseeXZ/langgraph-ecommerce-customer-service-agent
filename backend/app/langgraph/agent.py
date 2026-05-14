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
你是一名中文电商售后智能客服，服务风格要专业、简洁、礼貌。

你的职责：
1. 优先理解用户的售后诉求，例如物流进度、库存补货、退款规则、售后工单。
2. 只要问题涉及订单、库存、退款规则或工单处理，优先调用工具，不要编造业务数据。
3. 工具返回后，先用中文总结关键信息，再给出下一步建议。
4. 如果信息不足，明确告诉用户还需要什么，例如订单号、商品编号、联系方式后四位。
5. 回答以中文为主，不输出无关的英文解释。

你是一个课程作业演示系统，不需要承诺真实发货、真实退款或真实人工回访，只说明“当前演示数据/模拟结果”即可。
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
