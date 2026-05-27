"""
N8 节点：三路并行审查（逻辑 + 对抗 + 文笔）
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict
from ..state.planning_state import PlanningState
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_review_report, retry_on_failure


class N8ReviewNode:
    """N8 节点：对 N7 正文执行三路审查"""

    def __init__(self, llm_client: LLMClient, max_chapters: int = 5):
        self.llm_client = llm_client
        self.max_chapters = max_chapters
        self.guides_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "guides")

    def _read_guide(self, filename: str) -> str:
        path = os.path.join(self.guides_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def __call__(self, state: PlanningState) -> PlanningState:
        print("N8 节点：开始三路并行审查...")

        try:
            if not state.get("chapter_drafts"):
                raise ValueError("N7 未完成，缺少 chapter_drafts")
            if not state.get("style_fingerprint"):
                raise ValueError("N5 未完成，缺少 style_fingerprint")
            if not state.get("character_cards"):
                raise ValueError("N3 未完成，缺少 character_cards")
            if not state.get("world_setting"):
                raise ValueError("N3 未完成，缺少 world_setting")
            if not state.get("story_graph"):
                raise ValueError("N3 未完成，缺少 story_graph")

            chapter_drafts = state["chapter_drafts"]
            chapter_outlines = state.get("chapter_outlines", {})
            characters = state.get("character_cards", "")
            worldbuilding = state.get("world_setting", "")
            story_graph = state.get("story_graph", "")
            style_fingerprint = state.get("style_fingerprint", "")

            # 读取审查指南
            logic_guide = self._read_guide("logic_review_guide.md")
            adversarial_guide = self._read_guide("adversarial_edit_guide.md")
            prose_guide = self._read_guide("prose_review_guide.md")
            ai_blacklist = self._read_guide("ai_patterns_blacklist.md") if os.path.exists(
                os.path.join(self.guides_dir, "ai_patterns_blacklist.md")) else ""

            # 合并所有章节内容
            all_drafts = ""
            all_outlines = ""
            for ch_key in sorted(chapter_drafts.keys()):
                all_drafts += f"\n\n=== {ch_key} ===\n{chapter_drafts[ch_key]}"
                if ch_key in chapter_outlines:
                    all_outlines += f"\n\n=== {ch_key} ===\n{chapter_outlines[ch_key]}"

            # 三路并行审查（源文件要求同时派发）
            print("  - 并行派发 3 个 Reviewer...")
            results = {}
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(retry_on_failure, self._logic_review, 2,
                                    all_drafts=all_drafts, all_outlines=all_outlines,
                                    characters=characters, worldbuilding=worldbuilding,
                                    story_graph=story_graph, logic_guide=logic_guide): "logic_review",
                    executor.submit(retry_on_failure, self._adversarial_review, 2,
                                    all_drafts=all_drafts, adversarial_guide=adversarial_guide): "adversarial_review",
                    executor.submit(retry_on_failure, self._prose_review, 2,
                                    all_drafts=all_drafts, all_outlines=all_outlines,
                                    style_fingerprint=style_fingerprint, prose_guide=prose_guide,
                                    ai_blacklist=ai_blacklist): "prose_review",
                }
                for future in as_completed(futures):
                    name = futures[future]
                    results[name] = future.result()
                    print(f"  - {name} 完成")

            logic_review = results["logic_review"]
            adversarial_review = results["adversarial_review"]
            prose_review = results["prose_review"]

            # 验证每份报告
            for name, report in [("logic_review", logic_review), ("adversarial_review", adversarial_review), ("prose_review", prose_review)]:
                ok, msg = validate_review_report(report, name)
                if not ok:
                    print(f"  [WARN] {name} 验证: {msg}")

            state["logic_review"] = logic_review
            state["adversarial_review"] = adversarial_review
            state["prose_review"] = prose_review
            state["current_node"] = "n8"

            print("N8 节点：三路审查完成")
            return state

        except Exception as e:
            state["last_error"] = f"N8 节点失败：{str(e)}"
            print(f"N8 节点失败：{str(e)}")
            return state

    def _logic_review(self, all_drafts: str, all_outlines: str,
                      characters: str, worldbuilding: str, story_graph: str,
                      logic_guide: str) -> str:
        system_prompt = f"""You are a Reviewer Agent. Perform a logic review (Pass 1).

## Review Guide
{logic_guide}

## Rules
- Check all 7 items in the checklist for each chapter
- Even if no issues found, list all 7 items as "Pass"
- Output in the exact table format specified in the guide
- Be thorough and specific: cite chapter + paragraph for each issue"""

        user_prompt = f"""Chapter Drafts:
{all_drafts[:6000]}

Chapter Outlines:
{all_outlines[:3000]}

Character Cards:
{characters[:2000]}

Worldbuilding:
{worldbuilding[:2000]}

Story Graph:
{story_graph[:2000]}

Perform the logic review. Output in English."""

        return self.llm_client.invoke_with_system(system_prompt=system_prompt, user_prompt=user_prompt)

    def _adversarial_review(self, all_drafts: str, adversarial_guide: str) -> str:
        system_prompt = f"""You are a Reviewer Agent. Perform adversarial editing (Pass 2).

## Review Guide
{adversarial_guide}

## Rules
- Do NOT read any setting files — pure text analysis only
- You MUST analyze the ENTIRE text provided. Do NOT skip any paragraphs.
- FIRST: count and report the total word count of the entire text. This number must be accurate.
- Find tightest_passage (3-5 best sentences) first
- Mark PROTECTED paragraphs
- Classify all redundancies into 6 categories
- For each: cite original text (10+ chars), type, reason, CUT or REWRITE
- Calculate total cuttable words and fat percentage
- Ensure post-cut word count >= 2200 per chapter
- Protection rules: description paragraphs max 15% cut, dialogue paragraphs max 10% cut
- CRITICAL: Your word count numbers must reflect the FULL text, not a summary or partial analysis"""

        user_prompt = f"""Chapter Drafts:
{all_drafts[:8000]}

Perform the adversarial edit analysis. Output in English."""

        return self.llm_client.invoke_with_system(system_prompt=system_prompt, user_prompt=user_prompt)

    def _prose_review(self, all_drafts: str, all_outlines: str,
                      style_fingerprint: str, prose_guide: str,
                      ai_blacklist: str) -> str:
        system_prompt = f"""You are a Reviewer Agent. Perform prose/style review (Pass 3).

## Review Guide
{prose_guide}

## AI Writing Pattern Blacklist (dimension 7 data source)
{ai_blacklist[:2000] if ai_blacklist else "See style_fingerprint for banned words."}

## Rules
- Score all 8 dimensions (1-10 or pass/fail)
- For dimension 7 (banned words): list each occurrence with chapter + original text + replacement
- Every chapter must end with all 8 dimension scores
- Be specific: cite chapter + paragraph for each issue
- Do NOT just report counts ("6 occurrences") — list each one individually

## ⚠️ Dimension 9: Language Purity Scan (MANDATORY)
After scoring the 8 dimensions, you MUST perform a language purity scan:
1. Scan the ENTIRE text for Chinese characters (Unicode range: 一-鿿)
2. Scan for Japanese characters (hiragana, katakana)
3. Scan for Korean characters (hangul)
4. Scan for Chinese full-width punctuation
5. For EACH occurrence found, report: chapter, paragraph, the exact character/text, and suggested replacement
6. If NONE found, explicitly state: 'Language purity: PASS — no non-English characters detected'
7. This scan result MUST appear at the end of your report, as a separate section titled 'Dimension 9: Language Purity'"""

        user_prompt = f"""Chapter Drafts:
{all_drafts[:6000]}

Chapter Outlines:
{all_outlines[:2000]}

Style Fingerprint:
{style_fingerprint[:3000]}

Perform the prose/style review. Output in English."""

        return self.llm_client.invoke_with_system(system_prompt=system_prompt, user_prompt=user_prompt)
