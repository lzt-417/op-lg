"""
Day 3 主运行脚本：运行 N1-N7 流程（章纲 + 正文写作）
"""
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.graph_builder import run_n1_n7
from src.state.planning_state import PlanningState
from src.utils.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DASHSCOPE_MODEL

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


def main():
    print("=" * 60)
    print(f"Day 3：N1-N7 流程（章纲 + 正文，N7 最多写 {MAX_CHAPTERS} 章）")
    print("=" * 60)

    print(f"\n配置信息：")
    print(f"  - API: 阿里云百炼 (OpenAI 兼容)")
    print(f"  - Base URL: {DASHSCOPE_BASE_URL}")
    print(f"  - Model: {DASHSCOPE_MODEL}")
    print(f"  - Max Chapters: {MAX_CHAPTERS}")

    try:
        final_state = run_n1_n7(
            llm_provider="openai",
            llm_model=DASHSCOPE_MODEL,
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
        print("[SUCCESS] Day 3 完成！")
        print("=" * 60)
        print(f"\n生成内容：")
        print(f"  - arc_outlines: {len(final_state.get('arc_outlines', {}))} 个 Arc")
        print(f"  - chapter_outlines: {len(final_state.get('chapter_outlines', {}))} 章")
        print(f"  - chapter_drafts: {len(final_state.get('chapter_drafts', {}))} 章")

    except Exception as e:
        print(f"\n[ERROR] 运行失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
