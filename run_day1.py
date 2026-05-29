"""
Day 1 主运行脚本：运行 N1-N2 流程
"""
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.graph_builder import run_n1_n2
from src.state.planning_state import PlanningState
from src.utils.config import DASHSCOPE_BASE_URL, DASHSCOPE_MODEL


def save_output(state: PlanningState, output_dir: str = "novels/test-novel"):
    """保存输出到文件"""
    os.makedirs(output_dir, exist_ok=True)

    if state.get("reader_persona"):
        filepath = os.path.join(output_dir, "reader-persona.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state["reader_persona"])
        print(f"  [OK] 已保存 {filepath} ({len(state['reader_persona'])} 字符)")

    if state.get("concept"):
        filepath = os.path.join(output_dir, "concept.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state["concept"])
        print(f"  [OK] 已保存 {filepath} ({len(state['concept'])} 字符)")


def main():
    print("=" * 60)
    print("Day 1：N1-N2 流程")
    print("=" * 60)

    print(f"\n配置信息：")
    print(f"  - API: 阿里云百炼 (OpenAI 兼容)")
    print(f"  - Base URL: {DASHSCOPE_BASE_URL}")
    print(f"  - Model: {DASHSCOPE_MODEL}")

    try:
        print("\n开始运行 N1-N2 流程...")

        final_state = run_n1_n2(
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
        print("[SUCCESS] Day 1 完成！")
        print("=" * 60)
        print(f"\n生成内容：")
        print(f"  - reader-persona.md: {len(final_state.get('reader_persona', ''))} 字符")
        print(f"  - concept.md: {len(final_state.get('concept', ''))} 字符")

    except Exception as e:
        print(f"\n[ERROR] 运行失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
