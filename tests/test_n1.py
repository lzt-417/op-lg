"""
N1 节点测试
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters import TemplateAdapter, SourceDataAdapter
from src.utils.llm_client import LLMClient
from src.nodes import N1ReaderPersonaNode
from src.state.planning_state import PlanningState


def test_adapters():
    """测试 Adapter 层"""
    print("\n测试 Adapter 层...")

    template_adapter = TemplateAdapter()
    source_adapter = SourceDataAdapter()

    # 测试读取模板
    try:
        template = template_adapter.get_reader_persona_template()
        print(f"  [OK] 读者画像模板读取成功（{len(template)} 字符）")
    except Exception as e:
        print(f"  [FAIL] 读者画像模板读取失败：{e}")
        return False

    # 测试读取源数据
    try:
        database = source_adapter.get_reader_persona_database()
        print(f"  [OK] 读者画像数据库读取成功（{len(database)} 字符）")
    except Exception as e:
        print(f"  [FAIL] 读者画像数据库读取失败：{e}")
        return False

    return True


def test_n1_node(dry_run: bool = True):
    """
    测试 N1 节点

    Args:
        dry_run: 如果为 True，不实际调用 LLM
    """
    print("\n测试 N1 节点...")

    # 初始化组件
    template_adapter = TemplateAdapter()
    source_adapter = SourceDataAdapter()

    if dry_run:
        print("  - Dry run 模式，不调用 LLM")

        # 模拟状态更新
        state: PlanningState = {
            "reader_persona": "",
            "concept": "",
            "world_setting": "",
            "character_cards": "",
            "story_graph": "",
            "style_fingerprint": "",
            "arc_outlines": {},
            "current_node": "",
            "last_error": None,
        }

        # 模拟成功
        state["reader_persona"] = "测试读者画像内容..."
        state["current_node"] = "n1"

        print(f"  [OK] N1 节点测试成功（dry run）")
        return True

    else:
        # 实际调用 LLM（需要设置 API Key）
        try:
            llm_client = LLMClient(provider="openai")
            n1_node = N1ReaderPersonaNode(
                llm_client=llm_client,
                template_adapter=template_adapter,
                source_adapter=source_adapter,
            )

            # 初始状态
            state: PlanningState = {
                "reader_persona": "",
                "concept": "",
                "world_setting": "",
                "character_cards": "",
                "story_graph": "",
                "style_fingerprint": "",
                "arc_outlines": {},
                "current_node": "",
                "last_error": None,
            }

            # 运行节点
            result = n1_node(state)

            # 验证结果
            if result["reader_persona"] and len(result["reader_persona"]) > 500:
                print(f"  [OK] N1 节点测试成功（生成 {len(result['reader_persona'])} 字符）")
                return True
            else:
                print(f"  [FAIL] N1 节点测试失败：生成内容过短")
                return False

        except Exception as e:
            print(f"  [FAIL] N1 节点测试失败：{e}")
            return False


if __name__ == "__main__":
    print("=" * 50)
    print("Day 1 验证测试")
    print("=" * 50)

    # 测试 Adapter 层
    adapter_ok = test_adapters()

    # 测试 N1 节点（dry run）
    n1_ok = test_n1_node(dry_run=True)

    # 总结
    print("\n" + "=" * 50)
    print("测试总结：")
    print(f"  - Adapter 层：{'[OK] 通过' if adapter_ok else '[FAIL] 失败'}")
    print(f"  - N1 节点（dry run）：{'[OK] 通过' if n1_ok else '[FAIL] 失败'}")
    print("=" * 50)

    if adapter_ok and n1_ok:
        print("\n[SUCCESS] Day 1 基础验证通过！")
        print("提示：设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 环境变量后，可以运行实际 LLM 测试")
    else:
        print("\n[ERROR] Day 1 验证失败，请检查错误信息")
