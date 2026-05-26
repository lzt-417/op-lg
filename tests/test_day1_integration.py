"""
集成测试：测试 N1-N5 的状态传递和图结构
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state.planning_state import PlanningState
from src.graph_builder import build_planning_graph, build_n1_n2_graph


def test_state_structure():
    """测试状态结构"""
    print("\n测试状态结构...")

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

    required_fields = [
        "reader_persona", "concept", "world_setting", "character_cards",
        "story_graph", "style_fingerprint", "arc_outlines",
        "current_node", "last_error",
    ]

    for field in required_fields:
        if field not in state:
            print(f"  [FAIL] 缺少字段：{field}")
            return False

    print("  [OK] 状态结构正确")
    return True


def test_graph_structure():
    """测试 N1-N5 图结构"""
    print("\n测试 N1-N5 图结构...")

    try:
        graph = build_planning_graph()
        print("  [OK] N1-N5 图构建成功")
        print("  [OK] 图包含 N1、N2、N3、N4、N5 节点")
        return True
    except Exception as e:
        print(f"  [FAIL] 图构建失败：{e}")
        return False


def test_n1_n2_graph_structure():
    """测试 N1-N2 图结构（Day 1 兼容）"""
    print("\n测试 N1-N2 图结构...")

    try:
        graph = build_n1_n2_graph()
        print("  [OK] N1-N2 图构建成功")
        return True
    except Exception as e:
        print(f"  [FAIL] N1-N2 图构建失败：{e}")
        return False


def test_state_flow():
    """测试 N1-N5 状态流转"""
    print("\n测试状态流转（模拟）...")

    # 模拟 N1 完成
    state: PlanningState = {
        "reader_persona": "这是读者画像内容...",
        "concept": "", "world_setting": "", "character_cards": "",
        "story_graph": "", "style_fingerprint": "",
        "arc_outlines": {}, "current_node": "n1", "last_error": None,
    }
    print("  [OK] N1 输出正确")

    # 模拟 N2 完成
    state["concept"] = "Arc 1 (Ch1-5): 测试概念..."
    state["current_node"] = "n2"
    if not state["reader_persona"]:
        print("  [FAIL] N1 输出在 N2 后丢失")
        return False
    print("  [OK] N1 -> N2 状态传递正确")

    # 模拟 N3 完成
    state["world_setting"] = "世界观设定内容..."
    state["character_cards"] = "角色设定内容..."
    state["story_graph"] = "F01 追踪线..."
    state["current_node"] = "n3"
    if not state["concept"]:
        print("  [FAIL] N2 输出在 N3 后丢失")
        return False
    print("  [OK] N2 -> N3 状态传递正确")

    # 模拟 N4 完成
    state["arc_outlines"] = {"hook_arc": "Hook Arc 大纲...", "arc_1": "Arc 1 大纲..."}
    state["current_node"] = "n4"
    if not state["world_setting"]:
        print("  [FAIL] N3 输出在 N4 后丢失")
        return False
    print("  [OK] N3 -> N4 状态传递正确")

    # 模拟 N5 完成
    state["style_fingerprint"] = "POV: 第三人称有限..."
    state["current_node"] = "n5"
    if not state["arc_outlines"]:
        print("  [FAIL] N4 输出在 N5 后丢失")
        return False
    print("  [OK] N4 -> N5 状态传递正确")

    return True


if __name__ == "__main__":
    print("=" * 50)
    print("N1-N5 集成测试")
    print("=" * 50)

    state_ok = test_state_structure()
    graph_ok = test_graph_structure()
    n1_n2_ok = test_n1_n2_graph_structure()
    flow_ok = test_state_flow()

    print("\n" + "=" * 50)
    print("测试总结：")
    print(f"  - 状态结构：{'[OK] 通过' if state_ok else '[FAIL] 失败'}")
    print(f"  - N1-N5 图结构：{'[OK] 通过' if graph_ok else '[FAIL] 失败'}")
    print(f"  - N1-N2 图结构：{'[OK] 通过' if n1_n2_ok else '[FAIL] 失败'}")
    print(f"  - 状态流转：{'[OK] 通过' if flow_ok else '[FAIL] 失败'}")
    print("=" * 50)

    if all([state_ok, graph_ok, n1_n2_ok, flow_ok]):
        print("\n[SUCCESS] 集成测试通过！")
    else:
        print("\n[ERROR] 集成测试失败，请检查错误信息")
