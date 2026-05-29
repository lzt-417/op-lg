"""
Day 5 主运行脚本：运行 N1-N10 全流程（写作 + 审改 + 编译输出）
"""
import os
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.graph_builder import run_n1_n10
from src.state.planning_state import PlanningState
from src.utils.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DASHSCOPE_MODEL

REVIEW_MODEL = "glm-4.5-air"
MAX_CHAPTERS = 3
OUTPUT_DIR = "novels/test-novel"


def save_intermediate(state: PlanningState, output_dir: str):
    """保存中间产物（审查报告等）"""
    review_dir = os.path.join(output_dir, "N8-N10-review")
    os.makedirs(review_dir, exist_ok=True)
    for key, filename in [
        ("logic_review", "logic-review.md"),
        ("adversarial_review", "adversarial-review.md"),
        ("prose_review", "prose-review.md"),
        ("editor_review", "editor-review.md"),
    ]:
        if state.get(key):
            filepath = os.path.join(review_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(state[key])
            print(f"  [OK] N8-N10-review/{filename} ({len(state[key])} chars)")


def main():
    print("=" * 60)
    print(f"Day 5：N1-N10 全流程（写作 + 审改 + 编译，最多 {MAX_CHAPTERS} 章）")
    print("=" * 60)

    print(f"\n配置信息：")
    print(f"  - API: 阿里云百炼 (OpenAI 兼容)")
    print(f"  - Base URL: {DASHSCOPE_BASE_URL}")
    print(f"  - N1-N7 Model: {DASHSCOPE_MODEL}")
    print(f"  - N8-N9 Model: {REVIEW_MODEL}")
    print(f"  - Max Chapters: {MAX_CHAPTERS}")
    print(f"  - Output Dir: {OUTPUT_DIR}")

    try:
        start_time = time.time()

        final_state = run_n1_n10(
            llm_provider="openai",
            llm_model=DASHSCOPE_MODEL,
            review_model=REVIEW_MODEL,
            base_url=DASHSCOPE_BASE_URL,
            api_key=DASHSCOPE_API_KEY,
            max_chapters=MAX_CHAPTERS,
            output_dir=OUTPUT_DIR,
        )

        elapsed = time.time() - start_time

        if final_state.get("last_error"):
            print(f"\n[ERROR] 流程失败：{final_state['last_error']}")
            return

        # 保存中间产物
        print("\n保存中间产物...")
        save_intermediate(final_state, OUTPUT_DIR)

        # 性能统计
        chapter_count = len(final_state.get("chapter_drafts", {}))
        total_chars = sum(len(v) for v in final_state.get("chapter_drafts", {}).values())

        print("\n" + "=" * 60)
        print("[SUCCESS] Day 5 完成！N1-N10 全流程跑通！")
        print("=" * 60)
        print(f"\n最终输出：")
        print(f"  - 输出文件: {final_state.get('output_file', 'N/A')}")
        print(f"\n流程统计：")
        print(f"  - Arc 数量: {len(final_state.get('arc_outlines', {}))}")
        print(f"  - 章节数量: {chapter_count}")
        print(f"  - 正文总字数: {total_chars} 字符")
        print(f"  - 总耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
        print(f"\n审查状态：")
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
