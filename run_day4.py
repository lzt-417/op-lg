"""
Day 4 主运行脚本：运行 N1-N9 流程（写作 + 审改）
"""
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.graph_builder import run_n1_n9
from src.state.planning_state import PlanningState
from src.utils.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DASHSCOPE_MODEL

REVIEW_MODEL = "glm-4.5-air"
MAX_CHAPTERS = 3


def save_output(state: PlanningState, output_dir: str = "novels/test-novel"):
    """保存输出到文件"""
    os.makedirs(output_dir, exist_ok=True)

    for key, filename in [
        ("reader_persona", "reader-persona.md"),
        ("concept", "concept.md"),
        ("style_fingerprint", "style_fingerprint.md"),
    ]:
        if state.get(key):
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(state[key])
            print(f"  [OK] {filename} ({len(state[key])} chars)")

    n3_dir = os.path.join(output_dir, "N3-setting")
    os.makedirs(n3_dir, exist_ok=True)
    for key, filename in [
        ("world_setting", "worldbuilding.md"),
        ("character_cards", "characters.md"),
        ("story_graph", "story_graph.md"),
    ]:
        if state.get(key):
            filepath = os.path.join(n3_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(state[key])
            print(f"  [OK] N3-setting/{filename} ({len(state[key])} chars)")

    if state.get("arc_outlines"):
        n4_dir = os.path.join(output_dir, "N4-outline")
        os.makedirs(n4_dir, exist_ok=True)
        for arc_name, content in state["arc_outlines"].items():
            filepath = os.path.join(n4_dir, f"outline-{arc_name}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  [OK] N4-outline/outline-{arc_name}.md ({len(content)} chars)")

    if state.get("chapter_outlines"):
        n6_dir = os.path.join(output_dir, "N6-chapter-outlines")
        os.makedirs(n6_dir, exist_ok=True)
        for ch_key, content in state["chapter_outlines"].items():
            filepath = os.path.join(n6_dir, f"{ch_key}-outline.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  [OK] N6-chapter-outlines/{ch_key}-outline.md ({len(content)} chars)")

    if state.get("chapter_drafts"):
        n7_dir = os.path.join(output_dir, "N7-chapters")
        os.makedirs(n7_dir, exist_ok=True)
        for ch_key, content in state["chapter_drafts"].items():
            filepath = os.path.join(n7_dir, f"{ch_key}-draft.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  [OK] N7-chapters/{ch_key}-draft.md ({len(content)} chars)")

    review_dir = os.path.join(output_dir, "N8-N10-review")
    os.makedirs(review_dir, exist_ok=True)
    for key, filename in [
        ("logic_review", "logic-review.md"),
        ("adversarial_review", "adversarial-review.md"),
        ("prose_review", "prose-review.md"),
    ]:
        if state.get(key):
            filepath = os.path.join(review_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(state[key])
            print(f"  [OK] N8-N10-review/{filename} ({len(state[key])} chars)")

    if state.get("editor_review"):
        filepath = os.path.join(review_dir, "editor-review.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state["editor_review"])
        print(f"  [OK] N8-N10-review/editor-review.md ({len(state['editor_review'])} chars)")


def main():
    print("=" * 60)
    print(f"Day 4：N1-N9 流程（写作 + 审改，最多 {MAX_CHAPTERS} 章）")
    print("=" * 60)

    print(f"\n配置信息：")
    print(f"  - API: 阿里云百炼 (OpenAI 兼容)")
    print(f"  - Base URL: {DASHSCOPE_BASE_URL}")
    print(f"  - N1-N7 Model: {DASHSCOPE_MODEL}")
    print(f"  - N8-N9 Model: {REVIEW_MODEL}")
    print(f"  - Max Chapters: {MAX_CHAPTERS}")

    try:
        final_state = run_n1_n9(
            llm_provider="openai",
            llm_model=DASHSCOPE_MODEL,
            review_model=REVIEW_MODEL,
            base_url=DASHSCOPE_BASE_URL,
            api_key=DASHSCOPE_API_KEY,
            max_chapters=MAX_CHAPTERS,
        )

        if final_state.get("last_error"):
            print(f"\n[ERROR] 流程失败：{final_state['last_error']}")
            return

        print("\n保存输出文件...")
        save_output(final_state)

        print("\n" + "=" * 60)
        print("[SUCCESS] Day 4 完成！")
        print("=" * 60)
        print(f"\n生成内容：")
        print(f"  - arc_outlines: {len(final_state.get('arc_outlines', {}))} 个 Arc")
        print(f"  - chapter_outlines: {len(final_state.get('chapter_outlines', {}))} 章")
        print(f"  - chapter_drafts: {len(final_state.get('chapter_drafts', {}))} 章")
        print(f"  - logic_review: {'有' if final_state.get('logic_review') else '无'}")
        print(f"  - adversarial_review: {'有' if final_state.get('adversarial_review') else '无'}")
        print(f"  - prose_review: {'有' if final_state.get('prose_review') else '无'}")
        print(f"  - editor_review: {'有' if final_state.get('editor_review') else '无'}")

    except Exception as e:
        print(f"\n[ERROR] 运行失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
