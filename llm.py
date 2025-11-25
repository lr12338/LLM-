from dataclasses import dataclass, field
from typing import List

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from config import huoshan_model_deepseekv3_1, huoshan_base_url, huoshan_api_key
import os

# --------------------------
# 1. 初始化火山方舟模型（兼容 OpenAI API）
# --------------------------
llm = ChatOpenAI(
    model=huoshan_model_deepseekv3_1,
    base_url=huoshan_base_url,
    api_key=huoshan_api_key
)

# --------------------------
# 2. 定义 LangGraph 状态和节点
# --------------------------
@dataclass
class State:
    """工作流状态：存储对话历史和生成结果"""
    messages: List[BaseMessage] = field(default_factory=list)  # 对话历史
    result: str = ""  # 最终生成结果

def generate_response(state: State) -> State:
    """生成模型响应的节点"""
    # 调用火山方舟模型
    response = llm.invoke(state.messages)
    # 更新状态：添加模型回复 + 保存结果
    state.messages.append(response)
    state.result = response.content
    return state

# --------------------------
# 3. 构建并运行工作流
# --------------------------
# 初始化工作流
workflow = StateGraph(State)
workflow.add_node("generate", generate_response)  # 添加生成节点
workflow.set_entry_point("generate")  # 设置入口节点
workflow.add_edge("generate", END)  # 生成后结束流程
app = workflow.compile()

# 运行工作流（输入示例问题）
initial_state = State(
    messages=[
        SystemMessage(content="你是专业的助手，回答需简洁明了。"),
        HumanMessage(content="常见的十字花科植物有哪些？")
    ]
)
final_state = app.invoke(initial_state)

# 输出结果
print("模型回复：", final_state["result"])