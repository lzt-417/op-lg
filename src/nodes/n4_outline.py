"""
N4 节点：全书大纲
"""
import re
from typing import Dict, List
from ..state.planning_state import PlanningState
from ..adapters.template_adapter import TemplateAdapter
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_arc_outline, validate_keyword, retry_on_validation_failure, append_retry_error


class N4OutlineNode:
    """N4 节点：生成 Hook Arc 和各 Arc 大纲"""

    def __init__(
        self,
        llm_client: LLMClient,
        template_adapter: TemplateAdapter,
    ):
        self.llm_client = llm_client
        self.template_adapter = template_adapter

    def __call__(self, state: PlanningState) -> PlanningState:
        print("N4 节点：开始生成全书大纲...")

        try:
            if "world_setting" not in state or not state["world_setting"]:
                raise ValueError("N3 未完成，缺少 world_setting")
            if "character_cards" not in state or not state["character_cards"]:
                raise ValueError("N3 未完成，缺少 character_cards")
            if "story_graph" not in state or not state["story_graph"]:
                raise ValueError("N3 未完成，缺少 story_graph")

            # 验证 concept 包含 Arc 规划
            ok, msg = validate_keyword(state["concept"], ["Arc", "arc"], "concept")
            if not ok:
                raise ValueError(f"前置验证失败：{msg}")

            arc_template = self.template_adapter.get_arc_outline_template()
            arc_list = self._extract_arc_list(state["concept"])
            print(f"  - 检测到 {len(arc_list)} 个 Arc：{[a['name'] for a in arc_list]}")

            # 逐个生成 Arc 大纲
            arc_outlines = {}
            for arc_info in arc_list:
                print(f"  - 生成 {arc_info['name']}（{arc_info['chapters']}）...")
                is_hook = arc_info["key"] == "hook_arc"
                outline = retry_on_validation_failure(
                    self._generate_single_arc,
                    self._validate_arc_outline, 2,
                    arc_info=arc_info,
                    concept=state["concept"],
                    worldbuilding=state["world_setting"],
                    characters=state["character_cards"],
                    story_graph=state["story_graph"],
                    arc_template=arc_template,
                    previous_outlines=arc_outlines,
                    is_hook=is_hook,
                )

                arc_outlines[arc_info["key"]] = outline

            # 回写 story_graph（将伏笔计划追加到剧情图）
            print("  - 回写 story_graph（伏笔计划）...")
            updated_story_graph = self._update_story_graph(
                state["story_graph"], arc_outlines
            )

            state["arc_outlines"] = arc_outlines
            state["story_graph"] = updated_story_graph
            state["current_node"] = "n4"

            print(f"N4 节点：全书大纲生成完成（共 {len(arc_outlines)} 个 Arc）")
            return state

        except Exception as e:
            state["last_error"] = f"N4 节点失败：{str(e)}"
            print(f"N4 节点失败：{str(e)}")
            return state

    def _extract_arc_list(self, concept: str) -> List[Dict[str, str]]:
        """从 concept.md 中提取 Arc 规划列表（只取第一个方案）"""
        arcs = []

        # 如果有多个方案，只取第一个
        first_proposal_end = re.search(
            r"#{1,3}\s*.*(?:提案|方案|Proposal)\s*[2二Ⅱ]|#{1,3}\s*.*推荐",
            concept
        )
        if first_proposal_end:
            concept = concept[:first_proposal_end.start()]

        # 先清理 markdown 加粗标记
        clean_concept = re.sub(r"\*\*", "", concept)

        # 匹配 Hook Arc（兼容有括号和无括号格式）
        hook_pattern = r"Hook\s*Arc[^\n]*?(Ch[\d\-]+)"
        hook_match = re.search(hook_pattern, clean_concept, re.IGNORECASE)
        if hook_match:
            hook_line = clean_concept[hook_match.start():].split("\n")[0]
            desc = re.split(r"[:：]", hook_line, maxsplit=1)
            arcs.append({
                "key": "hook_arc",
                "name": "Hook Arc",
                "chapters": hook_match.group(1),
                "description": desc[1].strip(": ") if len(desc) > 1 else "Opening hook",
            })

        # 匹配 Arc N（兼容括号、表格、无括号等多种格式）
        arc_pattern = r"Arc\s*(\d+)[^\n]*?(Ch[\d\-]+)"
        for match in re.finditer(arc_pattern, clean_concept, re.IGNORECASE):
            arc_num = match.group(1)
            chapters = match.group(2)
            line_start = clean_concept.rfind("\n", 0, match.start()) + 1
            line_end = clean_concept.find("\n", match.end())
            if line_end == -1:
                line_end = len(clean_concept)
            full_line = clean_concept[line_start:line_end].strip("- *")
            desc_parts = re.split(r"[:：]", full_line, maxsplit=1)
            desc = desc_parts[1].strip(": ") if len(desc_parts) > 1 else ""
            arcs.append({
                "key": f"arc_{arc_num}",
                "name": f"Arc {arc_num}",
                "chapters": chapters,
                "description": desc or f"Arc {arc_num}",
            })

        # 去重
        seen = set()
        unique_arcs = []
        for a in arcs:
            if a["key"] not in seen:
                seen.add(a["key"])
                unique_arcs.append(a)
        arcs = unique_arcs

        if not arcs:
            arcs = [
                {"key": "hook_arc", "name": "Hook Arc", "chapters": "Ch1-5", "description": "Opening hook"},
                {"key": "arc_1", "name": "Arc 1", "chapters": "Ch6-30", "description": "Act 1"},
                {"key": "arc_2", "name": "Arc 2", "chapters": "Ch31-75", "description": "Act 2"},
                {"key": "arc_3", "name": "Arc 3", "chapters": "Ch76-110", "description": "Act 3"},
                {"key": "arc_4", "name": "Arc 4", "chapters": "Ch111-120", "description": "Act 4"},
            ]

        return arcs

    def _validate_arc_outline(self, outline: str, **kwargs) -> tuple:
        is_hook = kwargs.get("is_hook", False)
        return validate_arc_outline(outline, is_hook=is_hook)

    def _generate_single_arc(self, **kwargs) -> str:
        arc_info = kwargs["arc_info"]
        concept = kwargs["concept"]
        worldbuilding = kwargs["worldbuilding"]
        characters = kwargs["characters"]
        story_graph = kwargs["story_graph"]
        arc_template = kwargs["arc_template"]
        previous_outlines = kwargs["previous_outlines"]
        is_hook = arc_info["key"] == "hook_arc"

        prev_summary = ""
        if previous_outlines:
            prev_summary = "\n\n## 前序 Arc 摘要\n"
            for key, content in previous_outlines.items():
                snippet = content[:300] + "..." if len(content) > 300 else content
                prev_summary += f"\n### {key}\n{snippet}\n"

        system_prompt = f"""你是 Novelist Agent。为 **{arc_info['name']}**（{arc_info['chapters']}）生成完整大纲。

## 参考格式
{arc_template}

## 本 Arc 信息
- 名称：{arc_info['name']}
- 章节：{arc_info['chapters']}
- 描述：{arc_info['description']}

## 大纲必须包含
1. **Logline**（一句话概述）
2. **起始状态 → 终止状态**（外部/内部/信息差）
3. **核心事件**（5-8 个关键节点，按章节列出）
4. **情感曲线**（读者的情感体验）
5. **角色变化**（成长/退化）
6. **伏笔计划**（埋/推/收）
7. **"没想到"时刻**（1-2 个反转/惊喜）
8. **章节钩子类型**（动作/对话/揭示/悬念）
9. **字数计划**（每章短/中/长）

{"## Hook Arc 要求" if is_hook else "## Arc 要求"}
{"- 在 5 章内构建'日常生活 → 触发事件 → 被迫选择'" if is_hook else "- 必须在 5 章内有一次信息升级"}
{"- 每章标注钩子/爽点/悬念" if is_hook else "- 角色弧线必须细化到场景级别"}

## 要求
- 不要占位符，填入所有细节
- 与 concept.md 的 Arc 规划一致
- 与已有的世界观、角色、剧情关系图一致
- 全部使用中文输出"""

        system_prompt = append_retry_error(system_prompt, **kwargs)

        user_prompt = f"""概念设计：
{concept}

世界观设定：
{worldbuilding}

角色设定：
{characters}

剧情关系图：
{story_graph}
{prev_summary}

请为 {arc_info['name']}（{arc_info['chapters']}）生成完整大纲。全部使用中文输出。"""

        return self.llm_client.invoke_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def _update_story_graph(self, story_graph: str, arc_outlines: Dict[str, str]) -> str:
        """将 Arc 大纲中的伏笔计划和字数计划回写到 story_graph"""
        section = "\n\n---\n\n## N4 回写：伏笔计划 + 字数计划\n\n"
        keywords = ["伏笔", "foreshadow", "Foreshadowing", "字数", "word count", "Word Count",
                     "短篇", "中篇", "长篇", "short", "medium", "long"]
        for key, content in arc_outlines.items():
            lines = content.split("\n")
            in_section = False
            arc_lines = []
            for line in lines:
                if any(kw in line for kw in keywords):
                    in_section = True
                    arc_lines.append(line)
                elif in_section:
                    if line.strip() == "" or line.startswith("#"):
                        if arc_lines:
                            break
                    arc_lines.append(line)
            if arc_lines:
                section += f"### {key}\n"
                section += "\n".join(arc_lines) + "\n\n"

        if len(section) > 100:
            return story_graph + section
        return story_graph
