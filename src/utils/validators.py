"""
输出验证工具：对 LLM 产出进行质量检查
"""
import re
from typing import Optional, Tuple


def validate_size(content: str, min_bytes: int, name: str) -> Tuple[bool, str]:
    """验证内容大小"""
    size = len(content.encode("utf-8"))
    if size < min_bytes:
        return False, f"{name} 大小不足：{size} bytes < {min_bytes} bytes"
    return True, ""


def validate_keyword(content: str, keywords: list, name: str) -> Tuple[bool, str]:
    """验证内容包含指定关键词（至少匹配一个）"""
    for kw in keywords:
        if kw in content:
            return True, ""
    return False, f"{name} 缺少关键词：{keywords}"


def validate_no_placeholder(content: str, name: str) -> Tuple[bool, str]:
    """验证内容不包含占位符"""
    patterns = [r"\[填写\]", r"\[描述\]", r"\[列举\]", r"\[TODO\]", r"\[待补充\]"]
    for pattern in patterns:
        if re.search(pattern, content):
            return False, f"{name} 包含占位符：{pattern}"
    return True, ""


def validate_pattern(content: str, pattern: str, min_count: int, name: str) -> Tuple[bool, str]:
    """验证内容包含指定正则模式的最少匹配数"""
    matches = re.findall(pattern, content)
    if len(matches) < min_count:
        return False, f"{name} 模式 '{pattern}' 匹配数不足：{len(matches)} < {min_count}"
    return True, ""


def validate_reader_persona(content: str, **kwargs) -> Tuple[bool, str]:
    """验证 N1 读者画像输出"""
    ok, msg = validate_size(content, 500, "reader_persona")
    if not ok:
        return ok, msg
    ok, msg = validate_keyword(content, ["画像", "persona", "读者", "Reader"], "reader_persona")
    if not ok:
        return ok, msg
    return True, ""


def validate_concept(content: str, **kwargs) -> Tuple[bool, str]:
    """验证 N2 概念设计输出"""
    ok, msg = validate_size(content, 2000, "concept")
    if not ok:
        return ok, msg
    ok, msg = validate_keyword(content, ["Arc", "arc"], "concept")
    if not ok:
        return ok, msg
    return True, ""


def validate_worldbuilding(content: str, **kwargs) -> Tuple[bool, str]:
    """验证 N3 世界观输出"""
    return validate_size(content, 2000, "worldbuilding")


def validate_characters(content: str, **kwargs) -> Tuple[bool, str]:
    """验证 N3 角色设定输出"""
    return validate_size(content, 2000, "characters")


def validate_story_graph(content: str, **kwargs) -> Tuple[bool, str]:
    """验证 N3 剧情关系图输出"""
    ok, msg = validate_pattern(content, r"F\d{2}", 1, "story_graph")
    if not ok:
        return ok, msg
    return True, ""


def validate_arc_outline(content: str, is_hook: bool = False, **kwargs) -> Tuple[bool, str]:
    """验证 N4 Arc 大纲输出"""
    ok, msg = validate_keyword(content, ["Logline", "logline"], "arc_outline")
    if not ok:
        return ok, msg
    if is_hook:
        ok, msg = validate_pattern(content, r"Ch\d+", 5, "hook_arc")
        if not ok:
            return ok, msg
    return True, ""


def validate_style_fingerprint(content: str, **kwargs) -> Tuple[bool, str]:
    """验证 N5 风格指纹输出"""
    ok, msg = validate_size(content, 2000, "style_fingerprint")
    if not ok:
        return ok, msg
    ok, msg = validate_keyword(content, ["POV", "视角", "pov"], "style_fingerprint")
    if not ok:
        return ok, msg
    ok, msg = validate_keyword(content, ["禁用", "banned", "禁止"], "style_fingerprint")
    if not ok:
        return ok, msg
    ok, msg = validate_no_placeholder(content, "style_fingerprint")
    if not ok:
        return ok, msg
    return True, ""


def validate_chapter_outline(content: str, name: str = "chapter_outline") -> Tuple[bool, str]:
    """验证 N6 章纲输出"""
    ok, msg = validate_size(content, 200, name)
    if not ok:
        return ok, msg
    ok, msg = validate_keyword(content, ["Scene", "场景", "scene"], name)
    if not ok:
        return ok, msg
    ok, msg = validate_keyword(content, ["钩子", "hook", "悬念", "Hook"], name)
    if not ok:
        return ok, msg
    return True, ""


def validate_review_report(content: str, name: str = "review", **kwargs) -> Tuple[bool, str]:
    """验证 N8 审查报告输出"""
    ok, msg = validate_size(content, 200, name)
    if not ok:
        return ok, msg
    if name == "logic_review":
        ok, msg = validate_keyword(content, ["Chapter", "chapter", "章"], name)
        if not ok:
            return ok, msg
    elif name == "prose_review":
        ok, msg = validate_keyword(content, ["评分", "score", "Score", "维度", "dimension", "Dimension"], name)
        if not ok:
            return ok, msg
    elif name == "adversarial_review":
        ok, msg = validate_keyword(content, ["fat", "可删", "cuttable", "Cuttable", "字数"], name)
        if not ok:
            return ok, msg
    return True, ""


def validate_editor_review(content: str, **kwargs) -> Tuple[bool, str]:
    """验证 N9 综合编辑报告"""
    ok, msg = validate_size(content, 200, "editor_review")
    if not ok:
        return ok, msg
    ok, msg = validate_keyword(content, ["P0", "P1", "P2"], "editor_review")
    if not ok:
        return ok, msg
    return True, ""


def retry_on_validation_failure(generate_func, validate_func, max_retries: int = 2, **kwargs):
    """
    验证失败时重新派发：生成 → 验证 → 失败则带错误信息重新生成

    Args:
        generate_func: 生成函数
        validate_func: 验证函数 (content, **kwargs) -> (ok, msg)
        max_retries: 最大重试次数
        **kwargs: 传递给 generate_func 的参数（也会传给 validate_func）
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            result = generate_func(**kwargs)
            ok, msg = validate_func(result, **kwargs)
            if ok:
                return result
            last_error = msg
            if attempt < max_retries:
                print(f"  [RETRY] 验证失败，重新派发... ({msg})")
                # 注入错误信息到 kwargs，generate 函数应检查 _last_error 并追加到 prompt
                kwargs["_last_error"] = msg
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                print(f"  [RETRY] 第 {attempt + 1} 次失败，重试中... ({e})")
                kwargs["_last_error"] = str(e)
    raise ValueError(f"验证失败，已重试 {max_retries} 次: {last_error}")


def append_retry_error(system_prompt: str, **kwargs) -> str:
    """如果 kwargs 中有 _last_error，追加到 system_prompt 末尾"""
    error = kwargs.get("_last_error")
    if error:
        return system_prompt + f"\n\n## ⚠️ 上次输出的问题\n{error}。请修复这个问题。"
    return system_prompt
