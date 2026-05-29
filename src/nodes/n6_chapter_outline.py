"""
N6 节点：章纲生成（单 Arc 模式，支持 N9→N6 循环）
"""
import re
from typing import Dict, List
from ..state.planning_state import PlanningState
from ..adapters.template_adapter import TemplateAdapter
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_size, validate_chapter_outline, retry_on_validation_failure, append_retry_error


class N6ChapterOutlineNode:
    """N6 节点：为单个 Arc 生成逐章章纲（由 arc_cursor 控制处理哪个 Arc）"""

    def __init__(
        self,
        llm_client: LLMClient,
        template_adapter: TemplateAdapter,
        max_chapters: int = 0,
    ):
        self.llm_client = llm_client
        self.template_adapter = template_adapter
        self.max_chapters = max_chapters  # 0 = 不限制，>0 时按此值分批（每批 N 章）

    def __call__(self, state: PlanningState) -> PlanningState:
        try:
            if not state.get("arc_outlines"):
                raise ValueError("N4 未完成，缺少 arc_outlines")
            if not state.get("style_fingerprint"):
                raise ValueError("N5 未完成，缺少 style_fingerprint")

            arc_keys = sorted(state["arc_outlines"].keys())
            arc_cursor = state.get("arc_cursor", 0)

            if arc_cursor >= len(arc_keys):
                raise ValueError(f"arc_cursor ({arc_cursor}) 超出范围（共 {len(arc_keys)} 个 Arc）")

            arc_key = arc_keys[arc_cursor]
            arc_content = state["arc_outlines"][arc_key]

            print(f"N6 节点：处理 Arc {arc_cursor + 1}/{len(arc_keys)} ({arc_key}) ...")

            chapter_template = self.template_adapter.get_chapter_outline_template()

            chapter_range = self._extract_chapter_range(arc_content)
            if not chapter_range:
                raise ValueError(f"{arc_key} 未找到章节范围")

            start, end = chapter_range
            total_in_arc = end - start + 1

            if self.max_chapters > 0 and total_in_arc > self.max_chapters:
                batches = []
                batch_start = start
                while batch_start <= end:
                    batch_end = min(batch_start + self.max_chapters - 1, end)
                    batches.append((batch_start, batch_end))
                    batch_start = batch_end + 1
                print(f"  - {arc_key} 共 {total_in_arc} 章，分 {len(batches)} 批生成（每批 {self.max_chapters} 章）")
            else:
                batches = [(start, end)]
                print(f"  - 生成 {arc_key} 章纲（Ch{start}-Ch{end}，{total_in_arc} 章）...")

            new_outlines: Dict[str, str] = {}
            for batch_start, batch_end in batches:
                ch_count = batch_end - batch_start + 1
                if len(batches) > 1:
                    print(f"    - 批次 Ch{batch_start}-Ch{batch_end}（{ch_count} 章）...")

                outline = retry_on_validation_failure(
                    self._generate_arc_chapters,
                    self._validate_arc_chapters,
                    2,
                    arc_key=arc_key,
                    arc_content=arc_content,
                    chapter_range=(batch_start, batch_end),
                    worldbuilding=state["world_setting"],
                    characters=state["character_cards"],
                    story_graph=state["story_graph"],
                    style_fingerprint=state["style_fingerprint"],
                    chapter_template=chapter_template,
                )

                chapters = self._split_chapters(outline, batch_start)
                new_outlines.update(chapters)

            if not new_outlines:
                raise ValueError(f"N6 节点：{arc_key} 未产出章纲")

            # 追加到已有 chapter_outlines（保留前几个 Arc 的）
            existing = state.get("chapter_outlines", {}) or {}
            existing.update(new_outlines)
            state["chapter_outlines"] = existing

            # 记录当前 Arc 的章节 key 列表
            state["current_arc_chapters"] = sorted(new_outlines.keys())
            state["current_node"] = "n6"

            print(f"N6 节点：{arc_key} 章纲完成（{len(new_outlines)} 章：{', '.join(sorted(new_outlines.keys()))}）")
            return state

        except Exception as e:
            state["last_error"] = f"N6 节点失败：{str(e)}"
            print(f"N6 节点失败：{str(e)}")
            return state

    def _validate_arc_chapters(self, outline: str, **kwargs) -> tuple:
        """验证一批章纲的整体质量"""
        start, end = kwargs["chapter_range"]
        # 整体大小验证：源文件要求每批 >3000 bytes（约 600 bytes/章）
        ok, msg = validate_size(outline, max(3000, 600 * (end - start + 1)), f"Ch{start}-Ch{end}")
        if not ok:
            return ok, msg
        # 检查是否包含足够数量的章纲标记
        chapters = self._split_chapters(outline, start)
        if len(chapters) < (end - start + 1):
            return False, f"章纲数量不足：期望 {end - start + 1} 章，实际 {len(chapters)} 章"
        for ch_key, ch_content in chapters.items():
            ok, msg = validate_chapter_outline(ch_content, ch_key)
            if not ok:
                return ok, msg
        return True, ""

    def _extract_chapter_range(self, arc_content: str):
        """从 Arc 大纲中提取章节范围"""
        match = re.search(r"Ch(\d+)[\s\-–]+Ch(\d+)", arc_content)
        if match:
            return int(match.group(1)), int(match.group(2))
        match = re.search(r"Ch(\d+)[\s\-–]+(\d+)", arc_content)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None

    def _generate_arc_chapters(self, **kwargs) -> str:
        """为单个 Arc 生成全部章纲"""
        arc_key = kwargs["arc_key"]
        arc_content = kwargs["arc_content"]
        chapter_range = kwargs["chapter_range"]
        worldbuilding = kwargs["worldbuilding"]
        characters = kwargs["characters"]
        story_graph = kwargs["story_graph"]
        style_fingerprint = kwargs["style_fingerprint"]
        chapter_template = kwargs["chapter_template"]
        start, end = chapter_range

        system_prompt = f"""你是 Novelist Agent。为第 {start} 章到第 {end} 章生成章纲。

## 章纲模板
{chapter_template}

## 规则
- 每章必须包含：功能标签（推进/日常/战斗/揭示/过渡）、章节问题、状态变化、章尾钩子、伏笔任务（埋/推/收）
- 节奏：每场标注低/中/高能量
- 不要连续两章使用相同功能标签
- Hook Arc（如适用）：前 5 章必须构建'日常生活 → 触发事件 → 被迫选择'
- 每 3-5 章：一个小高潮
- 每章章纲：200-400 字，具体可执行
- 输出格式：用 ===CHXX=== 和 ===END_CHXX=== 分隔每章
- 全部使用中文输出"""

        system_prompt = append_retry_error(system_prompt, **kwargs)

        user_prompt = f"""Arc 大纲（{arc_key}）：
{arc_content}

世界观设定：
{worldbuilding[:2000]}

角色设定：
{characters[:2000]}

剧情关系图：
{story_graph[:2000]}

风格指纹（节选）：
{style_fingerprint[:2000]}

请为 Ch{start} 到 Ch{end} 生成章纲。全部使用中文输出。"""

        return self.llm_client.invoke_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def _split_chapters(self, text: str, start_num: int) -> Dict[str, str]:
        """将 LLM 输出拆分为逐章章纲"""
        chapters = {}
        pattern = r"===CH(\d+)===\s*\n(.*?)\n===END_CH\1==="
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            for ch_num, content in matches:
                key = f"ch{int(ch_num):02d}"
                chapters[key] = content.strip()
        else:
            # 降级：按 ## Chapter N 或 # Chapter N 拆分
            parts = re.split(r"(?=#+\s*(?:Chapter|Ch)\s*\d+)", text)
            ch_idx = 0
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                ch_num = start_num + ch_idx
                key = f"ch{ch_num:02d}"
                chapters[key] = part
                ch_idx += 1

        return chapters
