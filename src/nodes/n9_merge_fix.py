"""
N9 节点：合并修复（合并三份审查报告 → 修复正文）
"""
import os
import re
from typing import Dict
from ..state.planning_state import PlanningState
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_editor_review, validate_size, retry_on_validation_failure, append_retry_error


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
        # 单一正则避免重复计数：P0 后跟 BLOCKER 或 必修
        matches = re.findall(r"P0\s*(?:BLOCKER|必修)", prose_review, re.IGNORECASE)
        return len(matches)

    def _count_p0_in_editor(self, editor_review: str) -> int:
        """统计 editor-review 中的 P0 条目数量"""
        matches = re.findall(r"P0.*?(?:必修|BLOCKER|Must)", editor_review, re.IGNORECASE)
        return len(matches)

    def __call__(self, state: PlanningState) -> PlanningState:
        try:
            logic_review = state.get("logic_review", "")
            adversarial_review = state.get("adversarial_review", "")
            prose_review = state.get("prose_review", "")

            if not all([logic_review, adversarial_review, prose_review]):
                raise ValueError("N8 未完成，缺少审查报告")
            if not state.get("chapter_drafts"):
                raise ValueError("N7 未完成，缺少 chapter_drafts")
            if not state.get("style_fingerprint"):
                raise ValueError("N5 未完成，缺少 style_fingerprint")

            # 限定修复范围：当前 Arc 的章节
            arc_chapters = state.get("current_arc_chapters") or sorted(state["chapter_drafts"].keys())
            chapter_drafts = state["chapter_drafts"]
            style_fingerprint = state["style_fingerprint"]
            merge_rules = self._read_guide("merge_rules.md")

            # 确定 Arc 名称
            arc_cursor = state.get("arc_cursor", 0)
            arc_keys = sorted(state.get("arc_outlines", {}).keys())
            arc_name = arc_keys[arc_cursor] if arc_cursor < len(arc_keys) else "unknown"
            total_arcs = len(arc_keys)

            print(f"N9 节点：修复 {arc_name}（{', '.join(arc_chapters)}）...")

            # Step 1: 合并当前 Arc 的审查报告（带验证重试）
            print("  - Step 1: 合并审查报告...")
            # 只取当前 Arc 的审查内容（按 Arc 标题头分割）
            arc_logic = self._extract_arc_review(logic_review, arc_name)
            arc_adversarial = self._extract_arc_review(adversarial_review, arc_name)
            arc_prose = self._extract_arc_review(prose_review, arc_name)

            prose_p0 = self._count_p0_blockers(arc_prose)
            editor_review = retry_on_validation_failure(
                self._merge_reviews, self._validate_editor_review, 2,
                logic_review=arc_logic,
                adversarial_review=arc_adversarial,
                prose_review=arc_prose,
                merge_rules=merge_rules,
                prose_p0_count=prose_p0,
            )

            # 追加 editor_review（带 Arc 标题头）
            arc_header = f"\n\n--- Arc: {arc_name} ---\n"
            state["editor_review"] = (state.get("editor_review") or "") + arc_header + editor_review

            # Step 2: 修复当前 Arc 的正文
            print("  - Step 2: 修复正文...")
            fixed_drafts = {}
            for ch_key in arc_chapters:
                if ch_key not in chapter_drafts:
                    continue
                if len(fixed_drafts) >= self.max_chapters:
                    break
                print(f"  - 修复 {ch_key}...")
                prev_chapters = self._get_previous_chapters(chapter_drafts, ch_key)
                fixed = retry_on_validation_failure(
                    self._fix_chapter, self._validate_fixed_chapter, 2,
                    ch_key=ch_key,
                    chapter_text=chapter_drafts[ch_key],
                    editor_review=editor_review,
                    style_fingerprint=style_fingerprint,
                    prev_chapters=prev_chapters,
                )
                fixed_drafts[ch_key] = fixed

            # 合并：保留未修复的章节，只替换已修复的
            merged = dict(chapter_drafts)
            merged.update(fixed_drafts)
            state["chapter_drafts"] = merged

            # 推进 arc_cursor
            state["arc_cursor"] = arc_cursor + 1
            state["current_node"] = "n9"

            remaining = total_arcs - arc_cursor - 1
            if remaining > 0:
                print(f"N9 节点：{arc_name} 修复完成，剩余 {remaining} 个 Arc")
            else:
                print(f"N9 节点：{arc_name} 修复完成，所有 Arc 处理完毕")
            return state

        except Exception as e:
            state["last_error"] = f"N9 节点失败：{str(e)}"
            print(f"N9 节点失败：{str(e)}")
            return state

    def _extract_arc_review(self, full_review: str, arc_name: str) -> str:
        """从追加式审查报告中提取指定 Arc 的内容"""
        if not full_review:
            return ""
        # 按 "--- Arc: xxx ---" 分割
        pattern = rf"--- Arc: {re.escape(arc_name)} ---"
        parts = re.split(pattern, full_review, maxsplit=1)
        if len(parts) < 2:
            # 未找到 Arc 标记，返回全部（兼容首次运行或无标记的情况）
            return full_review
        # 取该 Arc 标记后的内容，截止到下一个 Arc 标记
        arc_content = parts[1]
        next_arc = re.search(r"\n--- Arc: \S+ ---", arc_content)
        if next_arc:
            arc_content = arc_content[:next_arc.start()]
        return arc_content.strip()

    def _validate_editor_review(self, editor_review: str, **kwargs) -> tuple:
        """验证 editor-review：格式 + P0 交叉验证"""
        # 格式验证
        ok, msg = validate_editor_review(editor_review)
        if not ok:
            return False, f"editor-review 格式验证失败：{msg}"
        # P0 交叉验证
        prose_p0 = kwargs.get("prose_p0_count", 0)
        if prose_p0 > 0:
            editor_p0 = self._count_p0_in_editor(editor_review)
            if editor_p0 < prose_p0:
                return False, f"P0 交叉验证失败：prose-review 有 {prose_p0} 个 P0，editor-review 只有 {editor_p0} 个。禁止遗漏 P0 条目。"
        return True, ""

    def _merge_reviews(self, logic_review: str, adversarial_review: str,
                       prose_review: str, merge_rules: str, **kwargs) -> str:
        prose_p0 = kwargs.get("prose_p0_count", 0)
        system_prompt = f"""You are the COO Agent. Merge three review reports into one editor review.

## Merge Rules
{merge_rules}

## Rules
- P0 comes from logic review (Pass 1) AND prose-review P0 BLOCKER items
- All P0 BLOCKER items from prose-review must be listed individually in the P0 table
- Do NOT omit any P0 item, even if it needs author decision
- Pass 2 CUT/REWRITE → P1
- Pass 3 dimensions scored <6 → P1
- Everything else → P2
- Merge same-location issues from multiple passes
- Output in the exact format specified in merge rules

## ⚠️ P0 Count Requirement
Prose-review contains {prose_p0} P0 BLOCKER item(s). Your editor-review MUST include at least {prose_p0} P0 entry/entries. This will be cross-validated — if your output has fewer P0 items, it will be rejected."""

        system_prompt = append_retry_error(system_prompt, **kwargs)

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
                prev.append(f"--- End of Chapter {n} ---\n{drafts[key][-2000:]}")
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

    def _validate_fixed_chapter(self, fixed: str, **kwargs) -> tuple:
        """验证修复后章节：字数"""
        ch_key = kwargs["ch_key"]

        # 字数验证（英文 2200 words ≈ 12000 bytes）
        ok, msg = validate_size(fixed, 12000, ch_key)
        if not ok:
            return False, f"字数不足：{msg}"

        return True, ""

    def _fix_chapter(self, **kwargs) -> str:
        ch_key = kwargs["ch_key"]
        chapter_text = kwargs["chapter_text"]
        editor_review = kwargs["editor_review"]
        style_fingerprint = kwargs["style_fingerprint"]
        prev_chapters = kwargs.get("prev_chapters", "")
        system_prompt = f"""You are the Scribe Agent. Fix chapter text based on the editor review.

## Rules
- Only fix P0 and P1 issues, do NOT touch P2
- Do NOT modify PROTECTED paragraphs
- After fixing, word count must be >= 2200
- Preserve the original chapter title format (# Chapter X — [Title])
- Maintain writing quality and consistency with style fingerprint
- Output the full fixed chapter text (not just the changes)"""

        system_prompt = append_retry_error(system_prompt, **kwargs)

        user_prompt = f"""Editor Review:
{editor_review[:4000]}

Original Chapter ({ch_key}):
{chapter_text}

Style Fingerprint:
{style_fingerprint}
{"--- Previous Chapters (for continuity) ---" + chr(10) + prev_chapters if prev_chapters else ""}

Fix the P0 and P1 issues. Output the full fixed chapter text in English."""

        return self.llm_client.invoke_with_system(system_prompt=system_prompt, user_prompt=user_prompt)
