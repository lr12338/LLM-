"""
LangGraph优化示例 - 租船邮件分析Agent

这是一个简化的示例，展示如何使用LangGraph重构租船邮件分析系统
"""

from typing import TypedDict, List, Optional, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import asyncio

# ==================== 状态定义 ====================

class CharterEmailState(TypedDict):
    """邮件处理状态"""
    # 输入
    raw_email: Optional[bytes]  # 原始邮件
    email_data: Optional[dict]  # 解析后的邮件数据
    
    # AI解析结果
    ai_result: Optional[dict]  # AI解析的原始结果
    intent: List[str]  # 意图列表: ['openvessels', 'cargo', 'unknown']
    
    # 处理结果
    vessels: List[dict]  # 船盘数据列表
    cargos: List[dict]  # 货盘数据列表
    
    # 增强数据
    enriched_vessels: List[dict]  # 增强后的船盘数据
    enriched_cargos: List[dict]  # 增强后的货盘数据
    
    # 元数据
    user_id: Optional[int]
    email_user: Optional[str]
    errors: List[str]  # 错误列表
    
    # 控制流
    should_continue: bool
    retry_count: int
    current_step: str  # 当前执行步骤


# ==================== 节点实现 ====================

def email_parse_node(state: CharterEmailState) -> CharterEmailState:
    """节点1: 解析邮件"""
    print("📧 [节点1] 解析邮件...")
    
    try:
        from charter_utils import parse_email
        
        raw_email = state.get("raw_email")
        if not raw_email:
            state["errors"].append("缺少原始邮件数据")
            state["should_continue"] = False
            return state
        
        email_data = parse_email(raw_email)
        state["email_data"] = email_data
        state["email_user"] = email_data.get("from_email")
        state["current_step"] = "email_parsed"
        
        print(f"✅ 邮件解析成功: {email_data.get('subject')}")
        
    except Exception as e:
        state["errors"].append(f"邮件解析失败: {str(e)}")
        state["should_continue"] = False
    
    return state


def intent_recognition_node(state: CharterEmailState) -> CharterEmailState:
    """节点2: AI意图识别"""
    print("🤖 [节点2] AI意图识别...")
    
    try:
        from charter_email_monitor_service import call_deepseek_api
        
        email_data = state.get("email_data")
        if not email_data:
            state["errors"].append("缺少邮件数据")
            state["should_continue"] = False
            return state
        
        # 调用AI解析
        content = email_data.get('subject', '') + "\n" + email_data.get('body', '')
        ai_result = call_deepseek_api(content[:5000])
        
        state["ai_result"] = ai_result
        state["intent"] = ai_result.get('intent', [])
        state["current_step"] = "intent_recognized"
        
        print(f"✅ 意图识别成功: {state['intent']}")
        
    except Exception as e:
        state["errors"].append(f"AI识别失败: {str(e)}")
        state["should_continue"] = False
    
    return state


def extract_vessels_node(state: CharterEmailState) -> CharterEmailState:
    """节点3: 提取船盘数据"""
    print("🚢 [节点3] 提取船盘数据...")
    
    try:
        ai_result = state.get("ai_result", {})
        charter_data = ai_result.get('data', {})
        vessels = charter_data.get('openvessels', [])
        
        state["vessels"] = vessels
        state["current_step"] = "vessels_extracted"
        
        print(f"✅ 提取到 {len(vessels)} 条船盘数据")
        
    except Exception as e:
        state["errors"].append(f"船盘提取失败: {str(e)}")
    
    return state


def extract_cargos_node(state: CharterEmailState) -> CharterEmailState:
    """节点4: 提取货盘数据"""
    print("📦 [节点4] 提取货盘数据...")
    
    try:
        ai_result = state.get("ai_result", {})
        charter_data = ai_result.get('data', {})
        cargos = charter_data.get('cargo', [])
        
        state["cargos"] = cargos
        state["current_step"] = "cargos_extracted"
        
        print(f"✅ 提取到 {len(cargos)} 条货盘数据")
        
    except Exception as e:
        state["errors"].append(f"货盘提取失败: {str(e)}")
    
    return state


def enrich_vessel_imo_node(state: CharterEmailState) -> CharterEmailState:
    """节点5: 船盘IMO补全（可并行）"""
    print("🔍 [节点5] 船盘IMO补全...")
    
    try:
        vessels = state.get("vessels", [])
        enriched = []
        
        for vessel in vessels:
            # 如果IMO缺失，尝试补全
            if not vessel.get("IMO"):
                shipname = vessel.get("船名", "")
                # 调用API补全IMO（示例，实际需要实现）
                # imo = fetch_imo_by_name(shipname)
                # vessel["IMO"] = imo
            
            enriched.append(vessel)
        
        state["enriched_vessels"] = enriched
        state["current_step"] = "vessels_imo_enriched"
        
        print(f"✅ IMO补全完成")
        
    except Exception as e:
        state["errors"].append(f"IMO补全失败: {str(e)}")
    
    return state


def enrich_vessel_port_node(state: CharterEmailState) -> CharterEmailState:
    """节点6: 船盘港口识别（可并行）"""
    print("🌍 [节点6] 船盘港口识别...")
    
    try:
        from charter_utils import call_deepseek_region
        
        vessels = state.get("vessels", [])
        enriched = []
        
        for vessel in vessels:
            port = vessel.get("OPEN位置")
            if port:
                # 调用AI识别港口区域
                port_result = call_deepseek_region(port)
                if port_result:
                    vessel["port_region"] = port_result.get('region_name')
                    vessel["port_region_cn"] = port_result.get('region_cn_name')
            
            enriched.append(vessel)
        
        state["enriched_vessels"] = enriched
        state["current_step"] = "vessels_port_enriched"
        
        print(f"✅ 港口识别完成")
        
    except Exception as e:
        state["errors"].append(f"港口识别失败: {str(e)}")
    
    return state


def enrich_vessel_tags_node(state: CharterEmailState) -> CharterEmailState:
    """节点7: 船盘标签生成"""
    print("🏷️ [节点7] 船盘标签生成...")
    
    try:
        from charter_utils import generate_vessel_tags
        
        vessels = state.get("enriched_vessels", [])
        enriched = []
        
        for vessel in vessels:
            # 生成标签
            tags_result = generate_vessel_tags(vessel)
            vessel["tags"] = tags_result.get('tags', '')
            enriched.append(vessel)
        
        state["enriched_vessels"] = enriched
        state["current_step"] = "vessels_tagged"
        
        print(f"✅ 标签生成完成")
        
    except Exception as e:
        state["errors"].append(f"标签生成失败: {str(e)}")
    
    return state


def enrich_cargo_port_node(state: CharterEmailState) -> CharterEmailState:
    """节点8: 货盘港口识别"""
    print("🌍 [节点8] 货盘港口识别...")
    
    try:
        from charter_utils import call_deepseek_region
        
        cargos = state.get("cargos", [])
        enriched = []
        
        for cargo in cargos:
            load_port = cargo.get("装货港")
            if load_port:
                port_result = call_deepseek_region(load_port)
                if port_result:
                    cargo["load_port_region"] = port_result.get('region_name')
                    cargo["load_port_region_cn"] = port_result.get('region_cn_name')
            
            enriched.append(cargo)
        
        state["enriched_cargos"] = enriched
        state["current_step"] = "cargos_port_enriched"
        
        print(f"✅ 货盘港口识别完成")
        
    except Exception as e:
        state["errors"].append(f"货盘港口识别失败: {str(e)}")
    
    return state


def data_storage_node(state: CharterEmailState) -> CharterEmailState:
    """节点9: 数据存储"""
    print("💾 [节点9] 数据存储...")
    
    try:
        from db_utils import get_db_connection
        from charter_utils import convert_date, clean_sender_name
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        email_data = state.get("email_data", {})
        email_user = state.get("email_user")
        user_id = state.get("user_id")
        
        # 存储船盘数据
        vessels = state.get("enriched_vessels", [])
        for vessel in vessels:
            # 插入数据库（简化示例）
            # insert_vessel_to_db(cursor, vessel, email_user, user_id)
            pass
        
        # 存储货盘数据
        cargos = state.get("enriched_cargos", [])
        for cargo in cargos:
            # 插入数据库（简化示例）
            # insert_cargo_to_db(cursor, cargo, email_user, user_id)
            pass
        
        conn.commit()
        cursor.close()
        conn.close()
        
        state["current_step"] = "data_stored"
        print(f"✅ 数据存储完成")
        
    except Exception as e:
        state["errors"].append(f"数据存储失败: {str(e)}")
    
    return state


# ==================== 路由函数 ====================

def route_by_intent(state: CharterEmailState) -> Literal["vessel_branch", "cargo_branch", "unknown_branch", "end"]:
    """根据意图路由到不同分支"""
    intent = state.get("intent", [])
    
    if not state.get("should_continue", True):
        return "end"
    
    if "openvessels" in intent:
        return "vessel_branch"
    elif "cargo" in intent:
        return "cargo_branch"
    else:
        return "unknown_branch"


# ==================== 图构建 ====================

def create_charter_email_graph():
    """创建租船邮件分析图"""
    
    # 创建状态图
    workflow = StateGraph(CharterEmailState)
    
    # 添加节点
    workflow.add_node("parse_email", email_parse_node)
    workflow.add_node("recognize_intent", intent_recognition_node)
    workflow.add_node("extract_vessels", extract_vessels_node)
    workflow.add_node("extract_cargos", extract_cargos_node)
    
    # 船盘处理分支（可并行）
    workflow.add_node("enrich_vessel_imo", enrich_vessel_imo_node)
    workflow.add_node("enrich_vessel_port", enrich_vessel_port_node)
    workflow.add_node("enrich_vessel_tags", enrich_vessel_tags_node)
    
    # 货盘处理分支
    workflow.add_node("enrich_cargo_port", enrich_cargo_port_node)
    
    # 数据存储
    workflow.add_node("store_data", data_storage_node)
    
    # 设置入口
    workflow.set_entry_point("parse_email")
    
    # 添加边
    workflow.add_edge("parse_email", "recognize_intent")
    workflow.add_conditional_edges(
        "recognize_intent",
        route_by_intent,
        {
            "vessel_branch": "extract_vessels",
            "cargo_branch": "extract_cargos",
            "unknown_branch": "end",
            "end": END
        }
    )
    
    # 船盘分支流程
    workflow.add_edge("extract_vessels", "enrich_vessel_imo")
    workflow.add_edge("extract_vessels", "enrich_vessel_port")  # 并行
    workflow.add_edge("enrich_vessel_imo", "enrich_vessel_tags")
    workflow.add_edge("enrich_vessel_port", "enrich_vessel_tags")
    workflow.add_edge("enrich_vessel_tags", "store_data")
    
    # 货盘分支流程
    workflow.add_edge("extract_cargos", "enrich_cargo_port")
    workflow.add_edge("enrich_cargo_port", "store_data")
    
    # 存储后结束
    workflow.add_edge("store_data", END)
    
    # 编译图
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


# ==================== 使用示例 ====================

async def process_email_example():
    """处理邮件示例"""
    
    # 创建图
    app = create_charter_email_graph()
    
    # 初始化状态
    initial_state = {
        "raw_email": b"...",  # 实际邮件数据
        "email_data": None,
        "ai_result": None,
        "intent": [],
        "vessels": [],
        "cargos": [],
        "enriched_vessels": [],
        "enriched_cargos": [],
        "user_id": None,
        "email_user": None,
        "errors": [],
        "should_continue": True,
        "retry_count": 0,
        "current_step": "start"
    }
    
    # 执行图
    config = {"configurable": {"thread_id": "email-1"}}
    result = await app.ainvoke(initial_state, config)
    
    # 输出结果
    print("\n" + "="*50)
    print("处理完成!")
    print(f"意图: {result.get('intent')}")
    print(f"船盘数量: {len(result.get('vessels', []))}")
    print(f"货盘数量: {len(result.get('cargos', []))}")
    print(f"错误: {result.get('errors', [])}")
    print("="*50)
    
    return result


# ==================== 主函数 ====================

if __name__ == "__main__":
    # 运行示例
    asyncio.run(process_email_example())

