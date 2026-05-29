"""
N10 节点：编译交付（合并章节 → 输出最终文件）
"""
import os
import re
from typing import Dict
from ..state.planning_state import PlanningState
from ..utils.validators import validate_editor_review


class N10CompileNode:
    """N10 节点：验证 P0=0，合并章节正文，输出最终文件"""

    def __init__(self, output_dir: str = "novels/test-novel"):
        self.output_dir = output_dir

    def _count_p0_in_editor(self, editor_review: str) -> int:
        """统计 editor-review 中的 P0 条目数量"""
        matches = re.findall(r"P0.*?(?:必修|BLOCKER|Must)", editor_review, re.IGNORECASE)
        return len(matches)

    def _strip_html_comments(self, text: str) -> str:
        """去除 HTML 注释"""
        return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()

    def __call__(self, state: PlanningState) -> PlanningState:
        print("N10 节点：编译交付...")

        try:
            # --- 前置检查 ---
            if not state.get("editor_review"):
                raise ValueError("N9 未完成，缺少 editor_review")
            if not state.get("chapter_drafts"):
                raise ValueError("N7/N9 未完成，缺少 chapter_drafts")

            # P0 = 0 检查
            p0_count = self._count_p0_in_editor(state["editor_review"])
            if p0_count > 0:
                raise ValueError(f"editor-review 中仍有 {p0_count} 个 P0 问题未解决，禁止编译输出")

            chapter_drafts = state["chapter_drafts"]

            # 确认所有章节存在
            for ch_key in sorted(chapter_drafts.keys()):
                content = chapter_drafts[ch_key]
                if not content or len(content.strip()) < 100:
                    raise ValueError(f"{ch_key} 内容为空或过短，无法编译")

            # --- Step 1: 合并章节 ---
            print(f"  - 合并 {len(chapter_drafts)} 个章节...")
            merged_parts = []
            for ch_key in sorted(chapter_drafts.keys()):
                cleaned = self._strip_html_comments(chapter_drafts[ch_key])
                merged_parts.append(cleaned)
            merged_text = "\n\n---\n\n".join(merged_parts)

            # --- Step 2: 写入输出目录 ---
            os.makedirs(self.output_dir, exist_ok=True)
            output_file = os.path.join(self.output_dir, "novel-English.md")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(merged_text)

            # 验证输出
            if not os.path.exists(output_file):
                raise ValueError(f"输出文件未生成：{output_file}")
            file_size = os.path.getsize(output_file)
            if file_size < 1000:
                raise ValueError(f"输出文件过小（{file_size} bytes），可能合并异常")

            state["output_file"] = output_file
            state["current_node"] = "n10"

            print(f"  [OK] 输出文件：{output_file}（{file_size} bytes, {len(chapter_drafts)} 章）")
            print("N10 节点：编译交付完成")
            return state

        except Exception as e:
            state["last_error"] = f"N10 节点失败：{str(e)}"
            print(f"N10 节点失败：{str(e)}")
            return state
