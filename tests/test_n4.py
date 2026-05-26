"""
N4 节点测试
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters import TemplateAdapter
from src.nodes.n4_outline import N4OutlineNode
from src.state.planning_state import PlanningState
from src.utils.validators import validate_arc_outline


def test_arc_extraction():
    """测试 Arc 列表提取"""
    print("\n测试 Arc 列表提取...")

    node = N4OutlineNode.__new__(N4OutlineNode)

    # 测试标准格式（有括号）
    sample1 = """
- **Hook Arc (Ch1-5)**: 开篇
- **Arc 1 (Ch6-30)**: 第一幕
- **Arc 2 (Ch31-75)**: 第二幕
"""
    arcs = node._extract_arc_list(sample1)
    if len(arcs) == 3 and arcs[0]["chapters"] == "Ch1-5":
        print(f"  [OK] 有括号格式：{len(arcs)} 个 Arc")
    else:
        print(f"  [FAIL] 有括号格式提取失败：{arcs}")
        return False

    # 测试无括号格式
    sample2 = """
- **Hook Arc Ch1-5**：开篇
- **Arc 1 (Ch6-15)**：第一幕
"""
    arcs = node._extract_arc_list(sample2)
    if len(arcs) == 2 and arcs[0]["chapters"] == "Ch1-5":
        print(f"  [OK] 无括号格式：{len(arcs)} 个 Arc")
    else:
        print(f"  [FAIL] 无括号格式提取失败：{arcs}")
        return False

    # 测试多方案只取第一个
    sample3 = """
## 提案 1
- **Hook Arc (Ch1-5)**: 开篇
- **Arc 1 (Ch6-30)**: 第一幕
## 提案 2
- **Hook Arc (Ch1-5)**: 另一个开篇
- **Arc 1 (Ch6-30)**: 另一幕
"""
    arcs = node._extract_arc_list(sample3)
    if len(arcs) == 2:
        print(f"  [OK] 多方案截断：{len(arcs)} 个 Arc（只取第一个提案）")
    else:
        print(f"  [FAIL] 多方案截断失败：{len(arcs)} 个 Arc")
        return False

    # 测试空内容返回默认
    arcs = node._extract_arc_list("没有 Arc 规划的内容")
    if len(arcs) == 5:
        print(f"  [OK] 空内容默认：{len(arcs)} 个 Arc")
    else:
        print(f"  [FAIL] 空内容默认失败")
        return False

    return True


def test_validators():
    """测试 Arc 大纲验证器"""
    print("\n测试 Arc 大纲验证器...")

    # Hook Arc 验证（需要 Logline + 5 个章节）
    hook_content = "Logline: 测试\nCh1\nCh2\nCh3\nCh4\nCh5"
    ok, msg = validate_arc_outline(hook_content, is_hook=True)
    print(f"  [OK] Hook Arc 通过：ok={ok}")

    hook_short = "Logline: 测试\nCh1\nCh2"
    ok, msg = validate_arc_outline(hook_short, is_hook=True)
    print(f"  [OK] Hook Arc 章节不足：ok={ok}, msg={msg}")

    # 普通 Arc 验证（需要 Logline）
    arc_content = "Logline: 测试内容"
    ok, msg = validate_arc_outline(arc_content, is_hook=False)
    print(f"  [OK] 普通 Arc 通过：ok={ok}")

    no_logline = "没有 Logline 的内容"
    ok, msg = validate_arc_outline(no_logline, is_hook=False)
    print(f"  [OK] 无 Logline 检测：ok={ok}, msg={msg}")

    return True


def test_template_adapter():
    """测试模板读取"""
    print("\n测试 Arc 大纲模板读取...")

    template_adapter = TemplateAdapter()

    try:
        template = template_adapter.get_arc_outline_template()
        print(f"  [OK] Arc 大纲模板读取成功（{len(template)} 字符）")
        return True
    except Exception as e:
        print(f"  [FAIL] Arc 大纲模板读取失败：{e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("N4 节点验证测试")
    print("=" * 50)

    extract_ok = test_arc_extraction()
    validator_ok = test_validators()
    template_ok = test_template_adapter()

    print("\n" + "=" * 50)
    print("测试总结：")
    print(f"  - Arc 提取：{'[OK] 通过' if extract_ok else '[FAIL] 失败'}")
    print(f"  - 验证器：{'[OK] 通过' if validator_ok else '[FAIL] 失败'}")
    print(f"  - 模板读取：{'[OK] 通过' if template_ok else '[FAIL] 失败'}")
    print("=" * 50)

    if all([extract_ok, validator_ok, template_ok]):
        print("\n[SUCCESS] N4 基础验证通过！")
    else:
        print("\n[ERROR] N4 验证失败，请检查错误信息")
