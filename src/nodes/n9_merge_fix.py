"""
N9 节点：合并修复（合并三份审查报告 → 修复正文）
"""
import os
import re
from typing import Dict
from ..state.planning_state import PlanningState
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_editor_review, validate_size, retry_on_failure


class N9MergeFixNode:
    """N9 节点：合并三份审查报告，生成修复指令，修复正文"""

    def __init__(self, llm_client: LLMClient, max_chapters: int = 5):
        self.llm_client = llm_client
        self.max_chapters = max_chapters
        self.guides_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "guides")

    def _read_guide(self, filename: str) -> str:
        path = os.path.join(self.guides_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _count_p0_blockers(self, prose_review: str) -> int:
        """统计 prose-review 中的 P0 BLOCKER 数量"""
        patterns = [
            r"P0\s*BLOCKER",
            r"P0.*?必修",
            r"P0.*?BLOCKER",
        ]
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, prose_review, re.IGNORECASE))
        return max(count, 1) if "P0" in prose_review else 0

    def _count_p0_in_editor(self, editor_review: str) -> int:
        """统计 editor-review 中的 P0 条目数量"""
        matches = re.findall(r"P0.*?(?:必修|BLOCKER|Must)", editor_review, re.IGNORECASE)
        return len(matches)

    def __call__(self, state: PlanningState) -> PlanningState:
        print("N9 节点：开始合并修复...")

        try:
            logic_review = state.get("logic_review", "")
            adversarial_review = state.get("adversarial_review", "")
            prose_review = state.get("prose_review", "")

            if not all([logic_review, adversarial_review, prose_review]):
                raise ValueError("N8 未完成，缺少审查报告")

            chapter_drafts = state.get("chapter_drafts", {})
            style_fingerprint = state.get("style_fingerprint", "")
            merge_rules = self._read_guide("merge_rules.md")

            # Step 1: 合并三份报告
            print("  - Step 1: 合并审查报告...")
            editor_review = retry_on_failure(
                self._merge_reviews, 2,
                logic_review=logic_review,
                adversarial_review=adversarial_review,
                prose_review=prose_review,
                merge_rules=merge_rules,
            )

            # P0 交叉验证：prose-review P0 数量必须与 editor-review P0 数量一致（阻断）
            prose_p0 = self._count_p0_blockers(prose_review)
            editor_p0 = self._count_p0_in_editor(editor_review)
            if prose_p0 > 0 and editor_p0 < prose_p0:
                raise ValueError(
                    f"P0 交叉验证失败：prose-review 有 {prose_p0} 个 P0，editor-review 只有 {editor_p0} 个。"
                    f"禁止遗漏 P0 条目，不得进入 Step 2。"
                )

            # 验证 editor-review
            ok, msg = validate_editor_review(editor_review)
            if not ok:
                raise ValueError(f"editor-review 验证失败：{msg}")

            state["editor_review"] = editor_review

            # Step 2: 修复正文
            print("  - Step 2: 修复正文...")
            fixed_drafts = {}
            for ch_key in sorted(chapter_drafts.keys()):
                if len(fixed_drafts) >= self.max_chapters:
                    break
                print(f"  - 修复 {ch_key}...")
                prev_chapters = self._get_previous_chapters(chapter_drafts, ch_key)
                fixed = retry_on_failure(
                    self._fix_chapter, 2,
                    ch_key=ch_key,
                    chapter_text=chapter_drafts[ch_key],
                    editor_review=editor_review,
                    style_fingerprint=style_fingerprint,
                    prev_chapters=prev_chapters,
                )
                # 验证修复后字数
                ok, msg = validate_size(fixed, 2200 * 3, ch_key)
                if not ok:
                    print(f"  [WARN] {ch_key} 修复后字数可能不足: {msg}")
                # P0 残留检查
                p0_residue = self._check_p0_residue(fixed, editor_review)
                if p0_residue:
                    print(f"  [WARN] {ch_key} 修复后仍有 P0 残留：{p0_residue}")
                fixed_drafts[ch_key] = fixed

            state["chapter_drafts"] = fixed_drafts
            state["current_node"] = "n9"

            print("N9 节点：合并修复完成")
            return state

        except Exception as e:
            state["last_error"] = f"N9 节点失败：{str(e)}"
            print(f"N9 节点失败：{str(e)}")
            return state

    def _merge_reviews(self, logic_review: str, adversarial_review: str,
                       prose_review: str, merge_rules: str) -> str:
        system_prompt = f"""You are the COO Agent. Merge three review reports into one editor review.

## Merge Rules
{merge_rules}

## Rules
- P0 only comes from logic review (Pass 1)
- Pass 2 CUT/REWRITE → P1
- Pass 3 dimensions scored <6 → P1
- Everything else → P2
- Merge same-location issues from multiple passes
- Output in the exact format specified in merge rules"""

        user_prompt = f"""Pass 1 — Logic Review:
{logic_review[:4000]}

Pass 2 — Adversarial Review:
{adversarial_review[:4000]}

Pass 3 — Prose Review:
{prose_review[:4000]}

Merge these into one editor review report. Output in English."""

        return self.llm_client.invoke_with_system(system_prompt=system_prompt, user_prompt=user_prompt)

    def _get_previous_chapters(self, drafts: Dict[str, str], ch_key: str) -> str:
        """获取前 2 章内容用于连续性"""
        ch_num = int(ch_key.replace("ch", ""))
        prev = []
        for n in range(max(1, ch_num - 2), ch_num):
            key = f"ch{n:02d}"
            if key in drafts:
                last_500 = drafts[key][-500:]
                prev.append(f"--- End of Chapter {n} (last 500 chars) ---\n{last_500}")
        return "\n\n".join(prev)

    def _check_p0_residue(self, fixed_text: str, editor_review: str) -> str:
        """检查修复后正文是否仍有 P0 问题残留"""
        p0_pattern = r"P0.*?(?:必修|BLOCKER|Must).*?[:：]\s*(.+)"
        p0_matches = re.findall(p0_pattern, editor_review, re.IGNORECASE)
        if not p0_matches:
            return ""
        residue = []
        for desc in p0_matches[:3]:
            keywords = [w.strip() for w in re.split(r"[,，、]", desc) if len(w.strip()) > 2]
            for kw in keywords[:2]:
                if kw in fixed_text:
                    residue.append(kw)
        return "、".join(residue[:3]) if residue else ""

    def _fix_chapter(self, ch_key: str, chapter_text: str,
                     editor_review: str, style_fingerprint: str,
                     prev_chapters: str = "") -> str:
        system_prompt = f"""You are the Scribe Agent. Fix chapter text based on the editor review.

## Rules
- Only fix P0 and P1 issues, do NOT touch P2
- Do NOT modify PROTECTED paragraphs
- After fixing, word count must be >= 2200
- Preserve the original chapter title format (# Chapter X — [Title])
- Maintain writing quality and consistency with style fingerprint
- Output the full fixed chapter text (not just the changes)"""

        user_prompt = f"""Editor Review:
{editor_review[:4000]}

Original Chapter ({ch_key}):
{chapter_text}

Style Fingerprint (excerpt):
{style_fingerprint[:2000]}
{"--- Previous Chapters (for continuity) ---" + chr(10) + prev_chapters if prev_chapters else ""}

Fix the P0 and P1 issues. Output the full fixed chapter text in English."""

        return self.llm_client.invoke_with_system(system_prompt=system_prompt, user_prompt=user_prompt)
