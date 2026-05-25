"""
LangGraph 图构建器
"""
from langgraph.graph import StateGraph, END
from .state.planning_state import PlanningState
from .nodes import N1ReaderPersonaNode, N2ConceptNode
from .adapters import TemplateAdapter, SourceDataAdapter
from .utils.llm_client import LLMClient


def build_planning_graph(
    llm_provider: str = "openai",
    llm_model: str = None,
    xfq_root: str = "C:/Users/Administrator/Desktop/XFQ-Project",
    base_url: str = None,
    api_key: str = None,
) -> StateGraph:
    """
    构建规划阶段的 LangGraph（N1-N5）

    Args:
        llm_provider: LLM provider（"openai" 或 "anthropic"）
        llm_model: LLM 模型名称
        xfq_root: XFQ-Project 根目录
        base_url: 自定义 API 地址（用于兼容接口）
        api_key: API Key

    Returns:
        编译后的 StateGraph
    """
    # 初始化组件
    llm_client = LLMClient(
        provider=llm_provider,
        model=llm_model,
        base_url=base_url,
        api_key=api_key,
    )
    template_adapter = TemplateAdapter(xfq_root=xfq_root)
    source_adapter = SourceDataAdapter(xfq_root=xfq_root)

    # 初始化节点
    n1_node = N1ReaderPersonaNode(
        llm_client=llm_client,
        template_adapter=template_adapter,
        source_adapter=source_adapter,
    )

    n2_node = N2ConceptNode(
        llm_client=llm_client,
        source_adapter=source_adapter,
    )

    # 创建 StateGraph
    workflow = StateGraph(PlanningState)

    # 添加节点
    workflow.add_node("n1", n1_node)
    workflow.add_node("n2", n2_node)

    # 添加边（线性流）
    workflow.add_edge("n1", "n2")
    workflow.add_edge("n2", END)

    # 设置入口
    workflow.set_entry_point("n1")

    return workflow.compile()


def run_n1_n2(
    llm_provider: str = "openai",
    llm_model: str = None,
    xfq_root: str = "C:/Users/Administrator/Desktop/XFQ-Project",
    base_url: str = None,
    api_key: str = None,
) -> PlanningState:
    """
    运行 N1-N2 流程

    Args:
        llm_provider: LLM provider（"openai" 或 "anthropic"）
        llm_model: LLM 模型名称
        xfq_root: XFQ-Project 根目录
        base_url: 自定义 API 地址（用于兼容接口）
        api_key: API Key

    Returns:
        最终状态
    """
    # 构建图
    graph = build_planning_graph(
        llm_provider=llm_provider,
        llm_model=llm_model,
        xfq_root=xfq_root,
        base_url=base_url,
        api_key=api_key,
    )

    # 初始状态
    initial_state: PlanningState = {
        "reader_persona": "",
        "concept": "",
        "world_setting": "",
        "character_cards": "",
        "story_graph": "",
        "style_fingerprint": "",
        "arc_outlines": {},
        "current_node": "",
        "last_error": None,
    }

    # 运行图
    print("开始运行 N1-N2 流程...")
    final_state = graph.invoke(initial_state)
    print("N1-N2 流程完成")

    return final_state
