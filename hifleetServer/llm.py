from typing import Annotated
from typing_extensions import TypedDict
from dataclasses import dataclass, field
from typing import List
from langchain.tools import tool

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from config import huoshan_model_deepseekv3_1, huoshan_base_url, huoshan_api_key
import os
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
#添加记忆
from langgraph.checkpoint.memory import MemorySaver

# 1. 初始化火山方舟模型（兼容 OpenAI API）
# --------------------------
huoshanModel = ChatOpenAI(
    model=huoshan_model_deepseekv3_1,
    base_url=huoshan_base_url,
    api_key=huoshan_api_key
)

# 定义工具 Tool
@tool
def multiply(a: int,b: int) -> int:
    """计算两个整数相乘的结果。只用于计算乘法。"""
    print(f"工具触发，正在计算{a}*{b}...")
    return a*b

@tool
# 将工具放入一个列表
tools = [multiply]
#关键步骤：告诉大模型它有哪些工具可用 (bind_tools)
# 这相当于给了大模型一本“工具说明书”
llm_with_tools = huoshanModel.bind_tools(tools)


# 2. 定义 LangGraph 状态State和节点Node
class State(TypedDict):
    # messages 是一个列表。
    # Annotated[list, add_messages] 的意思是：
    # 当有新消息返回时，不要覆盖原来的，而是“追加”（Append）到列表后面。
    # 这就是 AI 拥有“记忆”的基础。
    messages:Annotated[list, add_messages]

# 3.定义Node 节点
def chat_node(state: State):
    #1.获取 State 的 messages
    messages = state["messages"]
    #2.调用 huoshanModel
    response = huoshanModel.invoke(messages)
    #3.返回response 
    #注：这里返回的字典会自动合并入State中的messages ,基于 add_messages逻辑：当有新消息返回时，不要覆盖原来的，而是“追加”（Append）到列表后面
    return {"messages": [response]}

def agent_node(state: State):
    print("AI思考中")
    #注意：这里我们调用的是绑定了工具的 llm_with_tools
    return {"messages":[llm_with_tools.invoke(state["messages"])]}

#ToolNode 是 LangGraph提供的一个预制节点：专门检测AI是否发起了工具调用请求 -> 运行工具 -> 返回结果
tool_node = ToolNode(tools)



#4.绘制Graph 图
#4.1 创建一个Graph实例 workflow
workflow = StateGraph(State) 
#4.2 添加两个节点
# workflow.add_node("chatbot", chat_node)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
#4.3 定义边
# Start是图的入口：启动后直接进入node：“chatbot”
# workflow.add_edge(START,"chatbot")
workflow.add_edge(START,"agent")

#5.关键！设置conditional edge 条件边
# 1. 从 "agent" 节点出来后，不要直接走，先停下来看一眼 (tools_condition)。
# 2. tools_condition 是 LangGraph 自带的逻辑：
#    - 如果 AI 说“我要调用工具”，就去 "tools" 节点。
#    - 如果 AI 说“你好/讲个笑话”（不需要工具），就去 END。
workflow.add_conditional_edges(
    "agent",         #出发点
    tools_condition, #路由逻辑
)

#6定义闭环
# 工具干完活 ("tools")，必须回到 "agent" 让大脑再整理一下结果
workflow.add_edge("tools", "agent")



#7.编译与运行,并配置记忆
#compile 将 画纸 编译成 程序
# app = workflow.compile()
#7.1 初始化内存管理器 memory
memory = MemorySaver()
#7.2 编译时，标注图用 该管理器保存状态
app  = workflow.compile(checkpointer=memory)

#设置进程id
thread_config = {"configurable":{"thread_id":"user_1_session"}}


## 调试，测试日志
print("\n--- 🕵️‍♂️ 进入侦探模式：逐帧查看运行过程 ---")

inputs = {"messages": [("user", "计算 5 乘以 5，然后再把结果乘以 10")]}
config = {"configurable": {"thread_id": "debug_session_1"}}

# 关键点：使用 stream 而不是 invoke
# stream_mode="values" 的意思是：每经过一个节点，就把当前的整个 State 打印出来
for event in app.stream(inputs, config=config, stream_mode="values"):
    
    # event 其实就是当前的 State
    messages = event["messages"]
    last_message = messages[-1]
    
    # 打印当前最新的那条消息是谁发出的，内容是什么
    # type 可能是 'human', 'ai', 'tool'
    print(f"📍 [节点结束] 最新消息类型: {last_message.type}")
    print(f"   内容: {last_message.content}")
    
    # 如果是工具调用，打印一下细节
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print(f"   🛠️  AI 决定调用工具: {last_message.tool_calls}")
    
    print("-" * 30)
    
# print("\n--- 🗺️  流程地图 ---")
# # try:
# print(app.get_graph().draw_ascii())
# except Exception as e:
#     print("打印图表需要安装 extra 依赖，如果报错可以跳过。")

# ## 测试记忆
# user_input1 = "我的幸运数字是10"
# response_1 = app.invoke(
#     {"messages":[HumanMessage(content=user_input1)]},
#     config = thread_config
# )
# print(f"user:{user_input1}\n AI:{response_1['messages'][-1].content}")
# user_input2 = "我的幸运数字乘于5是多少"
# response_2 = app.invoke(
#     {"messages":[HumanMessage(content=user_input2)]},
#     config = thread_config
# )
# print(f"user:{user_input2}\n AI:{response_2['messages'][-1].content}")


## 测试 tool 调用
# #输入：
# print('简单对话')
# answer = app.invoke({"messages":[("user","你是谁")]})
# print(f"user ask:{query}\n,llm answer{answer['messages'][-1].content}")
# print("Ar应该直接回复，不调用工具")

# print('测试工具调用')
# query = "计算 12345 乘以 6789 等于多少？"
# print(f"用户: {query}")

# user_input = "hello,please introduce langgraph"
# system_inout = ""
# #invoke 触发运行，传入初始状态 State，返回最终状态
# # final_state = app.invoke({"messages": [("user",user_input)]})
# #OpenAI API）要求 messages 是 BaseMessage 实例列表（如 HumanMessage/SystemMessage
# final_state = app.invoke({
#     "messages":[
#         HumanMessage(content=query)
#         # SystemMessage(content=system_input)
#     ]
# })

# print(f"user ask:{query}\n,llm answer{final_state['messages'][-1].content}")
