"""
N2 节点测试
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters import SourceDataAdapter
from src.utils.llm_client import LLMClient
from src.nodes import N2ConceptNode
from src.state.planning_state import PlanningState


def test_n2_node(dry_run: bool = True):
    """
    测试 N2 节点

    Args:
        dry_run: 如果为 True，不实际调用 LLM
    """
    print("\n测试 N2 节点...")

    # 初始化组件
    source_adapter = SourceDataAdapter()

    if dry_run:
        print("  - Dry run 模式，不调用 LLM")

        # 模拟状态
        state: PlanningState = {
            "reader_persona": "测试读者画像内容...",
            "concept": "",
            "world_setting": "",
            "character_cards": "",
            "story_graph": "",
            "style_fingerprint": "",
            "arc_outlines": {},
            "current_node": "n1",
            "last_error": None,
        }

        # 模拟成功
        state["concept"] = "测试概念设计内容..."
        state["current_node"] = "n2"

        print(f"  [OK] N2 节点测试成功（dry run）")
        return True

    else:
        # 实际调用 LLM
        try:
            llm_client = LLMClient(provider="openai")
            n2_node = N2ConceptNode(
                llm_client=llm_client,
                source_adapter=source_adapter,
            )

            # 初始状态（已有 reader_persona）
            state: PlanningState = {
                "reader_persona": "测试读者画像内容（需要从 N1 传递）...",
                "concept": "",
                "world_setting": "",
                "character_cards": "",
                "story_graph": "",
                "style_fingerprint": "",
                "arc_outlines": {},
                "current_node": "n1",
                "last_error": None,
            }

            # 运行节点
            result = n2_node(state)

            # 验证结果
            if result["concept"] and len(result["concept"]) > 2000:
                print(f"  [OK] N2 节点测试成功（生成 {len(result['concept'])} 字符）")
                return True
            else:
                print(f"  [FAIL] N2 节点测试失败：生成内容过短")
                return False

        except Exception as e:
            print(f"  [FAIL] N2 节点测试失败：{e}")
            return False


if __name__ == "__main__":
    print("=" * 50)
    print("N2 节点测试")
    print("=" * 50)

    # 测试 N2 节点（dry run）
    n2_ok = test_n2_node(dry_run=True)

    print("\n" + "=" * 50)
    print(f"测试结果：{'[OK] 通过' if n2_ok else '[FAIL] 失败'}")
    print("=" * 50)
