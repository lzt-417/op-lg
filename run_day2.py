"""
Day 2 主运行脚本：运行 N1-N5 流程（设定 + 大纲 + 风格）
"""
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.graph_builder import run_n1_n5
from src.state.planning_state import PlanningState
from src.utils.config import DASHSCOPE_BASE_URL, DASHSCOPE_MODEL


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
            print(f"  [OK] {filename} ({len(state[key])} 字符)")

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
            print(f"  [OK] N3-setting/{filename} ({len(state[key])} 字符)")

    if state.get("arc_outlines"):
        n4_dir = os.path.join(output_dir, "N4-outline")
        os.makedirs(n4_dir, exist_ok=True)
        for arc_name, arc_content in state["arc_outlines"].items():
            filepath = os.path.join(n4_dir, f"outline-{arc_name}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(arc_content)
            print(f"  [OK] N4-outline/outline-{arc_name}.md ({len(arc_content)} 字符)")


def main():
    print("=" * 60)
    print("Day 2：N1-N5 流程（设定 + 大纲 + 风格）")
    print("=" * 60)

    print(f"\n配置信息：")
    print(f"  - API: 阿里云百炼 (OpenAI 兼容)")
    print(f"  - Base URL: {DASHSCOPE_BASE_URL}")
    print(f"  - Model: {DASHSCOPE_MODEL}")

    try:
        print("\n开始运行 N1-N5 流程...")

        final_state = run_n1_n5(
            llm_provider="openai",
            llm_model=DASHSCOPE_MODEL,
            base_url=DASHSCOPE_BASE_URL,
        )

        if final_state.get("last_error"):
            print(f"\n[ERROR] 流程失败：{final_state['last_error']}")
            return

        print("\n保存输出文件...")
        save_output(final_state)

        print("\n" + "=" * 60)
        print("[SUCCESS] Day 2 完成！")
        print("=" * 60)
        print(f"\n生成内容：")
        print(f"  - reader-persona.md: {len(final_state.get('reader_persona', ''))} 字符")
        print(f"  - concept.md: {len(final_state.get('concept', ''))} 字符")
        print(f"  - worldbuilding.md: {len(final_state.get('world_setting', ''))} 字符")
        print(f"  - characters.md: {len(final_state.get('character_cards', ''))} 字符")
        print(f"  - story_graph.md: {len(final_state.get('story_graph', ''))} 字符")
        print(f"  - arc_outlines: {len(final_state.get('arc_outlines', {}))} 个 Arc")
        print(f"  - style_fingerprint.md: {len(final_state.get('style_fingerprint', ''))} 字符")

    except Exception as e:
        print(f"\n[ERROR] 运行失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
