"""
LangGraph 图构建器
"""
from langgraph.graph import StateGraph, END
from .state.planning_state import PlanningState
from .nodes import (
    N1ReaderPersonaNode,
    N2ConceptNode,
    N3SettingNode,
    N4OutlineNode,
    N5StyleNode,
    N6ChapterOutlineNode,
    N7ChapterWritingNode,
)
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

    n3_node = N3SettingNode(
        llm_client=llm_client,
        source_adapter=source_adapter,
    )

    n4_node = N4OutlineNode(
        llm_client=llm_client,
        template_adapter=template_adapter,
    )

    n5_node = N5StyleNode(
        llm_client=llm_client,
        source_adapter=source_adapter,
        template_adapter=template_adapter,
    )

    # 创建 StateGraph
    workflow = StateGraph(PlanningState)

    # 添加节点
    workflow.add_node("n1", n1_node)
    workflow.add_node("n2", n2_node)
    workflow.add_node("n3", n3_node)
    workflow.add_node("n4", n4_node)
    workflow.add_node("n5", n5_node)

    # 添加边（线性流）
    workflow.add_edge("n1", "n2")
    workflow.add_edge("n2", "n3")
    workflow.add_edge("n3", "n4")
    workflow.add_edge("n4", "n5")
    workflow.add_edge("n5", END)

    # 设置入口
    workflow.set_entry_point("n1")

    return workflow.compile()


def build_n1_n2_graph(
    llm_provider: str = "openai",
    llm_model: str = None,
    xfq_root: str = "C:/Users/Administrator/Desktop/XFQ-Project",
    base_url: str = None,
    api_key: str = None,
) -> StateGraph:
    """构建仅 N1-N2 的图（用于 Day 1 测试）"""
    llm_client = LLMClient(
        provider=llm_provider, model=llm_model,
        base_url=base_url, api_key=api_key,
    )
    template_adapter = TemplateAdapter(xfq_root=xfq_root)
    source_adapter = SourceDataAdapter(xfq_root=xfq_root)

    n1_node = N1ReaderPersonaNode(
        llm_client=llm_client, template_adapter=template_adapter,
        source_adapter=source_adapter,
    )
    n2_node = N2ConceptNode(
        llm_client=llm_client, source_adapter=source_adapter,
    )

    workflow = StateGraph(PlanningState)
    workflow.add_node("n1", n1_node)
    workflow.add_node("n2", n2_node)
    workflow.add_edge("n1", "n2")
    workflow.add_edge("n2", END)
    workflow.set_entry_point("n1")

    return workflow.compile()


def run_n1_n2(
    llm_provider: str = "openai",
    llm_model: str = None,
    xfq_root: str = "C:/Users/Administrator/Desktop/XFQ-Project",
    base_url: str = None,
    api_key: str = None,
) -> PlanningState:
    """运行 N1-N2 流程（Day 1）"""
    graph = build_n1_n2_graph(
        llm_provider=llm_provider, llm_model=llm_model,
        xfq_root=xfq_root, base_url=base_url, api_key=api_key,
    )

    initial_state: PlanningState = {
        "reader_persona": "", "concept": "", "world_setting": "",
        "character_cards": "", "story_graph": "", "style_fingerprint": "",
        "arc_outlines": {}, "current_node": "", "last_error": None,
    }

    print("开始运行 N1-N2 流程...")
    final_state = graph.invoke(initial_state)
    print("N1-N2 流程完成")

    return final_state


def run_n1_n5(
    llm_provider: str = "openai",
    llm_model: str = None,
    xfq_root: str = "C:/Users/Administrator/Desktop/XFQ-Project",
    base_url: str = None,
    api_key: str = None,
) -> PlanningState:
    """
    运行 N1-N5 流程

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
        "arc_outlines": {}, "chapter_outlines": {}, "chapter_drafts": {},
        "current_node": "",
        "last_error": None,
    }

    # 运行图
    print("开始运行 N1-N5 流程...")
    final_state = graph.invoke(initial_state)
    print("N1-N5 流程完成")

    return final_state


def run_n1_n7(
    llm_provider: str = "openai",
    llm_model: str = None,
    xfq_root: str = "C:/Users/Administrator/Desktop/XFQ-Project",
    base_url: str = None,
    api_key: str = None,
    max_chapters: int = 5,
) -> PlanningState:
    """
    运行 N1-N7 全流程

    Args:
        max_chapters: N7 最多写作章数（默认 5，节省 token）
    """
    llm_client = LLMClient(
        provider=llm_provider, model=llm_model,
        base_url=base_url, api_key=api_key,
    )
    template_adapter = TemplateAdapter(xfq_root=xfq_root)
    source_adapter = SourceDataAdapter(xfq_root=xfq_root)

    n1 = N1ReaderPersonaNode(llm_client=llm_client, template_adapter=template_adapter, source_adapter=source_adapter)
    n2 = N2ConceptNode(llm_client=llm_client, source_adapter=source_adapter)
    n3 = N3SettingNode(llm_client=llm_client, source_adapter=source_adapter)
    n4 = N4OutlineNode(llm_client=llm_client, template_adapter=template_adapter)
    n5 = N5StyleNode(llm_client=llm_client, source_adapter=source_adapter, template_adapter=template_adapter)
    n6 = N6ChapterOutlineNode(llm_client=llm_client, template_adapter=template_adapter, max_chapters=max_chapters)
    n7 = N7ChapterWritingNode(llm_client=llm_client, max_chapters=max_chapters)

    workflow = StateGraph(PlanningState)
    workflow.add_node("n1", n1)
    workflow.add_node("n2", n2)
    workflow.add_node("n3", n3)
    workflow.add_node("n4", n4)
    workflow.add_node("n5", n5)
    workflow.add_node("n6", n6)
    workflow.add_node("n7", n7)
    workflow.add_edge("n1", "n2")
    workflow.add_edge("n2", "n3")
    workflow.add_edge("n3", "n4")
    workflow.add_edge("n4", "n5")
    workflow.add_edge("n5", "n6")
    workflow.add_edge("n6", "n7")
    workflow.add_edge("n7", END)
    workflow.set_entry_point("n1")

    graph = workflow.compile()

    initial_state: PlanningState = {
        "reader_persona": "", "concept": "", "world_setting": "",
        "character_cards": "", "story_graph": "", "style_fingerprint": "",
        "arc_outlines": {}, "chapter_outlines": {}, "chapter_drafts": {},
        "current_node": "", "last_error": None,
    }

    print(f"开始运行 N1-N7 流程（N7 最多写 {max_chapters} 章）...")
    final_state = graph.invoke(initial_state)
    print("N1-N7 流程完成")

    return final_state
