"""
规划阶段状态定义（N1-N5 产出）
"""
from typing import TypedDict, Dict, Optional


class PlanningState(TypedDict, total=False):
    """
    规划阶段状态（N1-N5 产出，全局只读）

    字段说明：
    - reader_persona: 读者画像
    - concept: 概念设计
    - world_setting: 世界观设定
    - character_cards: 角色设定
    - story_graph: 剧情关系图
    - style_fingerprint: 风格指纹
    - arc_outlines: Arc 大纲（key: "hook_arc", "arc_1", ...）
    - current_node: 当前所在节点
    - last_error: 最后一次错误信息
    """
    # N1-N5 产出
    reader_persona: str
    concept: str
    world_setting: str
    character_cards: str
    story_graph: str
    style_fingerprint: str
    arc_outlines: Dict[str, str]

    # 系统状态
    current_node: str
    last_error: Optional[str]
