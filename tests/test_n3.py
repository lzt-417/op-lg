"""
N3 节点测试
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters import SourceDataAdapter
from src.utils.llm_client import LLMClient
from src.nodes import N3SettingNode
from src.state.planning_state import PlanningState
from src.utils.validators import validate_worldbuilding, validate_characters, validate_story_graph


def test_source_adapter():
    """测试源数据读取"""
    print("\n测试源数据读取...")

    source_adapter = SourceDataAdapter()

    try:
        pools = source_adapter.get_diversity_pools()
        print(f"  [OK] diversity-pools 读取成功（{len(pools)} 字符）")
    except Exception as e:
        print(f"  [FAIL] diversity-pools 读取失败：{e}")
        return False

    return True


def test_validators():
    """测试输出验证器"""
    print("\n测试 N3 验证器...")

    # worldbuilding 验证
    ok, msg = validate_worldbuilding("x" * 100)
    print(f"  [OK] worldbuilding 小内容检测：ok={ok}")

    ok, msg = validate_worldbuilding("x" * 3000)
    print(f"  [OK] worldbuilding 大内容检测：ok={ok}")

    # characters 验证
    ok, msg = validate_characters("x" * 100)
    print(f"  [OK] characters 小内容检测：ok={ok}")

    # story_graph 验证
    ok, msg = validate_story_graph("F01 追踪线 F02 追踪线")
    print(f"  [OK] story_graph 追踪线检测：ok={ok}")

    ok, msg = validate_story_graph("没有追踪线")
    print(f"  [OK] story_graph 无追踪线检测：ok={ok}, msg={msg}")

    return True


def test_n3_node(dry_run: bool = True):
    """测试 N3 节点"""
    print("\n测试 N3 节点...")

    source_adapter = SourceDataAdapter()

    if dry_run:
        print("  - Dry run 模式，不调用 LLM")

        state: PlanningState = {
            "reader_persona": "测试读者画像",
            "concept": "Arc 1 (Ch1-5): 测试概念",
            "world_setting": "",
            "character_cards": "",
            "story_graph": "",
            "style_fingerprint": "",
            "arc_outlines": {},
            "current_node": "n2",
            "last_error": None,
        }

        # 验证前置条件检查
        n3_node = N3SettingNode.__new__(N3SettingNode)
        n3_node.llm_client = None
        n3_node.source_adapter = source_adapter

        # 测试空 concept 会报错
        empty_state = {**state, "concept": ""}
        result = n3_node(empty_state)
        if result.get("last_error") and "N2 未完成" in result["last_error"]:
            print("  [OK] 前置条件检查正确（空 concept 报错）")
        else:
            print("  [FAIL] 前置条件检查失败")
            return False

        print("  [OK] N3 节点测试成功（dry run）")
        return True

    else:
        try:
            llm_client = LLMClient(provider="openai")
            n3_node = N3SettingNode(
                llm_client=llm_client,
                source_adapter=source_adapter,
            )

            state: PlanningState = {
                "reader_persona": "测试读者画像",
                "concept": "测试概念设计，包含 Arc 1 (Ch1-5)",
                "world_setting": "", "character_cards": "", "story_graph": "",
                "style_fingerprint": "", "arc_outlines": {},
                "current_node": "n2", "last_error": None,
            }

            result = n3_node(state)

            if result.get("last_error"):
                print(f"  [FAIL] N3 节点失败：{result['last_error']}")
                return False

            wb_ok, _ = validate_worldbuilding(result["world_setting"])
            ch_ok, _ = validate_characters(result["character_cards"])
            sg_ok, _ = validate_story_graph(result["story_graph"])

            if wb_ok and ch_ok and sg_ok:
                print(f"  [OK] N3 节点测试成功")
                return True
            else:
                print(f"  [FAIL] N3 输出验证失败 wb={wb_ok} ch={ch_ok} sg={sg_ok}")
                return False

        except Exception as e:
            print(f"  [FAIL] N3 节点测试失败：{e}")
            return False


if __name__ == "__main__":
    print("=" * 50)
    print("N3 节点验证测试")
    print("=" * 50)

    adapter_ok = test_source_adapter()
    validator_ok = test_validators()
    n3_ok = test_n3_node(dry_run=True)

    print("\n" + "=" * 50)
    print("测试总结：")
    print(f"  - 源数据读取：{'[OK] 通过' if adapter_ok else '[FAIL] 失败'}")
    print(f"  - 验证器：{'[OK] 通过' if validator_ok else '[FAIL] 失败'}")
    print(f"  - N3 节点（dry run）：{'[OK] 通过' if n3_ok else '[FAIL] 失败'}")
    print("=" * 50)

    if all([adapter_ok, validator_ok, n3_ok]):
        print("\n[SUCCESS] N3 基础验证通过！")
    else:
        print("\n[ERROR] N3 验证失败，请检查错误信息")
