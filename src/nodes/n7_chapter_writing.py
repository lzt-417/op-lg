"""
N7 节点：正文写作
"""
from typing import Dict
from ..state.planning_state import PlanningState
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_size, retry_on_failure


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
        print("N7 节点：开始生成正文...")

        try:
            if not state.get("chapter_outlines"):
                raise ValueError("N6 未完成，缺少 chapter_outlines")
            if not state.get("style_fingerprint"):
                raise ValueError("N5 未完成，缺少 style_fingerprint")

            chapters_to_write = list(state["chapter_outlines"].keys())[:self.max_chapters]
            print(f"  - 计划写作 {len(chapters_to_write)} 章（上限 {self.max_chapters}）")

            drafts: Dict[str, str] = state.get("chapter_drafts", {}) or {}

            for i, ch_key in enumerate(chapters_to_write):
                ch_outline = state["chapter_outlines"][ch_key]
                ch_num = int(ch_key.replace("ch", ""))

                prev_chapters = self._get_previous_chapters(drafts, ch_num)

                print(f"  - 写作 {ch_key}...")
                draft = retry_on_failure(
                    self._write_chapter, 2,
                    ch_num=ch_num,
                    chapter_outline=ch_outline,
                    style_fingerprint=state["style_fingerprint"],
                    characters=state["character_cards"],
                    worldbuilding=state["world_setting"],
                    prev_chapters=prev_chapters,
                )

                ok, msg = validate_size(draft, 2200 * 3, f"ch{ch_num}")
                if not ok:
                    print(f"  [WARN] {ch_key} 字数可能不足：{msg}")

                drafts[ch_key] = draft

            state["chapter_drafts"] = drafts
            state["current_node"] = "n7"

            print(f"N7 节点：正文生成完成（共 {len(drafts)} 章）")
            return state

        except Exception as e:
            state["last_error"] = f"N7 节点失败：{str(e)}"
            print(f"N7 节点失败：{str(e)}")
            return state

    def _get_previous_chapters(self, drafts: Dict[str, str], ch_num: int) -> str:
        """获取前 2 章内容用于连续性"""
        prev = []
        for n in range(max(1, ch_num - 2), ch_num):
            key = f"ch{n:02d}"
            if key in drafts:
                last_500 = drafts[key][-500:]
                prev.append(f"--- End of Chapter {n} (last 500 chars) ---\n{last_500}")
        return "\n\n".join(prev)

    def _write_chapter(
        self,
        ch_num: int,
        chapter_outline: str,
        style_fingerprint: str,
        characters: str,
        worldbuilding: str,
        prev_chapters: str,
    ) -> str:
        """写作单章正文"""
        system_prompt = f"""你是 Scribe Agent。写出第 {ch_num} 章的完整正文。

## 写作规则（来自风格指纹）
{style_fingerprint[:2000]}

## 规则
- 严格遵循章纲
- 每章不少于 2200 字
- 标题格式：# 第 {ch_num} 章 — [标题]
- 不要有元评论或作者注释
- POV：与风格指纹一致
- 不要描述其他角色的内心想法（只写 POV 角色）
- 章尾钩子是必须的
- 全部使用中文输出（专有名词可保留英文）"""

        user_prompt = f"""章纲：
{chapter_outline}

角色设定：
{characters[:1500]}

世界观设定：
{worldbuilding[:1500]}
{"--- 前文衔接 ---" + chr(10) + prev_chapters if prev_chapters else ""}

请写出第 {ch_num} 章的完整正文（不少于 2200 字）。全部使用中文输出。"""

        return self.llm_client.invoke_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
