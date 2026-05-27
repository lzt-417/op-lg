"""
Day 1 主运行脚本：运行 N1-N2 流程
"""
import os
import sys

# Windows GBK 编码修复
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.graph_builder import run_n1_n2
from src.state.planning_state import PlanningState


# 阿里云百炼配置
DASHSCOPE_API_KEY = "xxxxxx"
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_MODEL = "qwen3-8b"


def save_output(state: PlanningState, output_dir: str = "novels/test-novel"):
    """
    保存输出到文件

    Args:
        state: 最终状态
        output_dir: 输出目录
    """
    os.makedirs(output_dir, exist_ok=True)

    # 保存 reader-persona.md
    if state.get("reader_persona"):
        filepath = os.path.join(output_dir, "reader-persona.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state["reader_persona"])
        print(f"  [OK] 已保存 {filepath} ({len(state['reader_persona'])} 字符)")

    # 保存 concept.md
    if state.get("concept"):
        filepath = os.path.join(output_dir, "concept.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state["concept"])
        print(f"  [OK] 已保存 {filepath} ({len(state['concept'])} 字符)")


def main():
    """主函数"""
    print("=" * 60)
    print("Day 1：N1-N2 流程")
    print("=" * 60)

    print(f"\n配置信息：")
    print(f"  - API: 阿里云百炼 (OpenAI 兼容)")
    print(f"  - Base URL: {DASHSCOPE_BASE_URL}")
    print(f"  - Model: {DASHSCOPE_MODEL}")

    try:
        print("\n开始运行 N1-N2 流程...")

        # 运行图
        final_state = run_n1_n2(
            llm_provider="openai",  # 使用 OpenAI 兼容接口
            llm_model=DASHSCOPE_MODEL,
            base_url=DASHSCOPE_BASE_URL,
            api_key=DASHSCOPE_API_KEY,
        )

        # 检查结果
        if final_state.get("last_error"):
            print(f"\n[ERROR] 流程失败：{final_state['last_error']}")
            return

        # 保存输出
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
