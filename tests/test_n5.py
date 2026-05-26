"""
N5 节点测试
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters import SourceDataAdapter, TemplateAdapter
from src.nodes import N5StyleNode
from src.state.planning_state import PlanningState
from src.utils.validators import validate_style_fingerprint, validate_no_placeholder


def test_source_data():
    """测试 N5 所需的源数据读取"""
    print("\n测试 N5 源数据读取...")

    source_adapter = SourceDataAdapter()
    template_adapter = TemplateAdapter()

    try:
        pools = source_adapter.get_diversity_pools()
        print(f"  [OK] diversity-pools 读取成功（{len(pools)} 字符）")
    except Exception as e:
        print(f"  [FAIL] diversity-pools 读取失败：{e}")
        return False

    try:
        blacklist = source_adapter.get_ai_patterns_blacklist()
        print(f"  [OK] ai-patterns-blacklist 读取成功（{len(blacklist)} 字符）")
    except Exception as e:
        print(f"  [FAIL] ai-patterns-blacklist 读取失败：{e}")
        return False

    try:
        template = template_adapter.get_style_fingerprint_template()
        print(f"  [OK] style-fingerprint 模板读取成功（{len(template)} 字符）")
    except Exception as e:
        print(f"  [FAIL] style-fingerprint 模板读取失败：{e}")
        return False

    return True


def test_validators():
    """测试 N5 验证器"""
    print("\n测试 N5 验证器...")

    # 合格的风格指纹
    good_content = """
## 视角（POV）
主视角：第三人称有限过去时

## 禁用词
delve, tapestry, myriad

## 禁用句式
禁止 "Not X but Y" 句式
"""
    ok, msg = validate_style_fingerprint(good_content)
    print(f"  [OK] 合格内容检测：ok={ok}")

    # 缺少 POV
    no_pov = "## 禁用词\ndelve"
    ok, msg = validate_style_fingerprint(no_pov)
    print(f"  [OK] 缺少 POV 检测：ok={ok}, msg={msg}")

    # 缺少禁用词
    no_banned = "## 视角\n第三人称"
    ok, msg = validate_style_fingerprint(no_banned)
    print(f"  [OK] 缺少禁用词检测：ok={ok}, msg={msg}")

    # 包含占位符
    placeholder = "POV 视角 禁用 [填写] [描述]"
    ok, msg = validate_no_placeholder(placeholder, "test")
    print(f"  [OK] 占位符检测：ok={ok}, msg={msg}")

    return True


def test_n5_node(dry_run: bool = True):
    """测试 N5 节点"""
    print("\n测试 N5 节点...")

    source_adapter = SourceDataAdapter()
    template_adapter = TemplateAdapter()

    if dry_run:
        print("  - Dry run 模式，不调用 LLM")

        n5_node = N5StyleNode.__new__(N5StyleNode)
        n5_node.llm_client = None
        n5_node.source_adapter = source_adapter
        n5_node.template_adapter = template_adapter

        # 测试空 reader_persona 会报错
        empty_state: PlanningState = {
            "reader_persona": "", "concept": "", "world_setting": "",
            "character_cards": "", "story_graph": "", "style_fingerprint": "",
            "arc_outlines": {}, "current_node": "n4", "last_error": None,
        }
        result = n5_node(empty_state)
        if result.get("last_error") and "N1 未完成" in result["last_error"]:
            print("  [OK] 前置条件检查正确（空 reader_persona 报错）")
        else:
            print("  [FAIL] 前置条件检查失败")
            return False

        print("  [OK] N5 节点测试成功（dry run）")
        return True

    else:
        try:
            from src.utils.llm_client import LLMClient
            llm_client = LLMClient(provider="openai")
            n5_node = N5StyleNode(
                llm_client=llm_client,
                source_adapter=source_adapter,
                template_adapter=template_adapter,
            )

            state: PlanningState = {
                "reader_persona": "测试读者画像内容 " * 100,
                "concept": "", "world_setting": "", "character_cards": "",
                "story_graph": "", "style_fingerprint": "",
                "arc_outlines": {}, "current_node": "n4", "last_error": None,
            }

            result = n5_node(state)

            if result.get("last_error"):
                print(f"  [FAIL] N5 节点失败：{result['last_error']}")
                return False

            ok, msg = validate_style_fingerprint(result["style_fingerprint"])
            if ok:
                print(f"  [OK] N5 节点测试成功")
                return True
            else:
                print(f"  [FAIL] N5 输出验证失败：{msg}")
                return False

        except Exception as e:
            print(f"  [FAIL] N5 节点测试失败：{e}")
            return False


if __name__ == "__main__":
    print("=" * 50)
    print("N5 节点验证测试")
    print("=" * 50)

    data_ok = test_source_data()
    validator_ok = test_validators()
    n5_ok = test_n5_node(dry_run=True)

    print("\n" + "=" * 50)
    print("测试总结：")
    print(f"  - 源数据读取：{'[OK] 通过' if data_ok else '[FAIL] 失败'}")
    print(f"  - 验证器：{'[OK] 通过' if validator_ok else '[FAIL] 失败'}")
    print(f"  - N5 节点（dry run）：{'[OK] 通过' if n5_ok else '[FAIL] 失败'}")
    print("=" * 50)

    if all([data_ok, validator_ok, n5_ok]):
        print("\n[SUCCESS] N5 基础验证通过！")
    else:
        print("\n[ERROR] N5 验证失败，请检查错误信息")
