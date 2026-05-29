"""
状态定义（N1-N10 产出）
"""
from typing import TypedDict, Dict, Optional, List


class PlanningState(TypedDict, total=False):
    """
    全流程状态

    字段说明：
    - reader_persona: 读者画像（N1）
    - concept: 概念设计（N2）
    - world_setting: 世界观设定（N3）
    - character_cards: 角色设定（N3）
    - story_graph: 剧情关系图（N3）
    - style_fingerprint: 风格指纹（N5）
    - arc_outlines: Arc 大纲（N4，key: "hook_arc", "arc_1", ...）
    - chapter_outlines: 章纲（N6，key: "ch01", "ch02", ...）
    - chapter_drafts: 正文初稿/修复稿（N7/N9，key: "ch01", "ch02", ...）
    - logic_review: 逻辑审查报告（N8 Pass 1）
    - adversarial_review: 对抗编辑报告（N8 Pass 2）
    - prose_review: 文笔审查报告（N8 Pass 3）
    - editor_review: 综合编辑审查报告（N9）
    - output_file: 最终输出文件路径（N10）
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

    # N6-N7 产出
    chapter_outlines: Dict[str, str]
    chapter_drafts: Dict[str, str]

    # Arc 循环状态
    arc_cursor: int
    current_arc_chapters: List[str]

    # N8 产出
    logic_review: str
    adversarial_review: str
    prose_review: str

    # N9 产出
    editor_review: str

    # N10 产出
    output_file: str

    # 系统状态
    current_node: str
    last_error: Optional[str]
