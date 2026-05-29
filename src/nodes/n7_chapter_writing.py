"""
N7 节点：正文写作
"""
import re
from typing import Dict
from ..state.planning_state import PlanningState
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_size, retry_on_validation_failure, append_retry_error

# POV 断裂检测：非第一人称叙事模式
POV_BREAK_PATTERN = re.compile(r"^\s*[A-Z][a-z]+\s+(sat|stood|walked|looked|turned|smiled|nodded|sighed|whispered|shouted|laughed|cried|muttered|groaned)", re.MULTILINE)


class N7ChapterWritingNode:
    """N7 节点：逐章生成正文初稿"""

    def __init__(
        self,
        llm_client: LLMClient,
        max_chapters: int = 5,
    ):
        self.llm_client = llm_client
        self.max_chapters = max_chapters

    def __call__(self, state: PlanningState) -> PlanningState:
        try:
            if not state.get("chapter_outlines"):
                raise ValueError("N6 未完成，缺少 chapter_outlines")
            if not state.get("style_fingerprint"):
                raise ValueError("N5 未完成，缺少 style_fingerprint")
            if not state.get("character_cards"):
                raise ValueError("N3 未完成，缺少 character_cards")
            if not state.get("world_setting"):
                raise ValueError("N3 未完成，缺少 world_setting")

            # 使用 current_arc_chapters（N6 设置），回退到全部 chapter_outlines
            arc_chapters = state.get("current_arc_chapters") or list(state["chapter_outlines"].keys())
            chapters_to_write = arc_chapters[:self.max_chapters]
            print(f"N7 节点：写作 {len(chapters_to_write)} 章（{', '.join(chapters_to_write)}）")

            drafts: Dict[str, str] = state.get("chapter_drafts", {}) or {}

            for i, ch_key in enumerate(chapters_to_write):
                ch_outline = state["chapter_outlines"][ch_key]
                ch_num = int(ch_key.replace("ch", ""))

                prev_chapters = self._get_previous_chapters(drafts, ch_num)

                print(f"  - 写作 {ch_key}...")
                draft = retry_on_validation_failure(
                    self._write_chapter, self._validate_chapter, 2,
                    ch_num=ch_num,
                    chapter_outline=ch_outline,
                    style_fingerprint=state["style_fingerprint"],
                    characters=state["character_cards"],
                    worldbuilding=state["world_setting"],
                    prev_chapters=prev_chapters,
                )

                drafts[ch_key] = draft

            state["chapter_drafts"] = drafts
            state["current_node"] = "n7"

            print(f"N7 节点：正文生成完成（当前 Arc {len(chapters_to_write)} 章，总计 {len(drafts)} 章）")
            return state

        except Exception as e:
            state["last_error"] = f"N7 节点失败：{str(e)}"
            print(f"N7 节点失败：{str(e)}")
            return state

    def _validate_chapter(self, draft: str, **kwargs) -> tuple:
        """验证章节质量：字数 + POV 断裂"""
        ch_num = kwargs["ch_num"]

        # 字数验证（英文 2200 words ≈ 12000 bytes）
        ok, msg = validate_size(draft, 12000, f"ch{ch_num}")
        if not ok:
            return False, f"字数不足：{msg}"

        # POV 断裂检测（源文件要求零容忍）
        pov_breaks = POV_BREAK_PATTERN.findall(draft)
        if len(pov_breaks) > 0:
            examples = pov_breaks[:3]
            return False, f"POV 断裂：{len(pov_breaks)} 处非第一人称叙事（如 '{'、'.join(examples)}'）。请用第一人称改写所有此类句子。"

        return True, ""

    def _get_previous_chapters(self, drafts: Dict[str, str], ch_num: int) -> str:
        """获取前 2 章内容用于连续性（源文件要求读取完整前章）"""
        prev = []
        for n in range(max(1, ch_num - 2), ch_num):
            key = f"ch{n:02d}"
            if key in drafts:
                prev.append(f"--- End of Chapter {n} ---\n{drafts[key][-2000:]}")
        return "\n\n".join(prev)

    def _write_chapter(self, **kwargs) -> str:
        """写作单章正文"""
        ch_num = kwargs["ch_num"]
        chapter_outline = kwargs["chapter_outline"]
        style_fingerprint = kwargs["style_fingerprint"]
        characters = kwargs["characters"]
        worldbuilding = kwargs["worldbuilding"]
        prev_chapters = kwargs.get("prev_chapters", "")
        system_prompt = f"""You are the Scribe Agent. Write the full text of Chapter {ch_num}.

## Writing Rules (from Style Fingerprint)
{style_fingerprint[:2000]}

## Rules
- Follow the chapter outline strictly
- Minimum 2200 words per chapter
- Title format: # Chapter {ch_num} — [Title]
- Signature Lines must be woven into the prose (not as comments)
- No metadata comments or notes sections
- No meta-commentary or author notes
- POV: consistent with style fingerprint
- Do not describe other characters' inner thoughts (only POV character)
- Chapter-ending hook is mandatory
- Write entirely in English (proper nouns from the worldbuilding may retain their original form)"""

        system_prompt = append_retry_error(system_prompt, **kwargs)

        user_prompt = f"""Chapter Outline:
{chapter_outline}

Character Cards:
{characters[:2000]}

Worldbuilding:
{worldbuilding[:2000]}
{"--- Previous Chapters (for continuity) ---" + chr(10) + prev_chapters if prev_chapters else ""}

Write the full text of Chapter {ch_num} in English (minimum 2200 words)."""

        return self.llm_client.invoke_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
