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


def validate_reader_persona(content: str) -> Tuple[bool, str]:
    """验证 N1 读者画像输出"""
    ok, msg = validate_size(content, 500, "reader_persona")
    if not ok:
        return ok, msg
    ok, msg = validate_keyword(content, ["画像", "persona", "读者", "Reader"], "reader_persona")
    if not ok:
        return ok, msg
    return True, ""


def validate_concept(content: str) -> Tuple[bool, str]:
    """验证 N2 概念设计输出"""
    ok, msg = validate_size(content, 2000, "concept")
    if not ok:
        return ok, msg
    ok, msg = validate_keyword(content, ["Arc", "arc"], "concept")
    if not ok:
        return ok, msg
    return True, ""


def validate_worldbuilding(content: str) -> Tuple[bool, str]:
    """验证 N3 世界观输出"""
    return validate_size(content, 2000, "worldbuilding")


def validate_characters(content: str) -> Tuple[bool, str]:
    """验证 N3 角色设定输出"""
    return validate_size(content, 2000, "characters")


def validate_story_graph(content: str) -> Tuple[bool, str]:
    """验证 N3 剧情关系图输出"""
    ok, msg = validate_pattern(content, r"F\d{2}", 1, "story_graph")
    if not ok:
        return ok, msg
    return True, ""


def validate_arc_outline(content: str, is_hook: bool = False) -> Tuple[bool, str]:
    """验证 N4 Arc 大纲输出"""
    ok, msg = validate_keyword(content, ["Logline", "logline"], "arc_outline")
    if not ok:
        return ok, msg
    if is_hook:
        ok, msg = validate_pattern(content, r"Ch\d+", 5, "hook_arc")
        if not ok:
            return ok, msg
    return True, ""


def validate_style_fingerprint(content: str) -> Tuple[bool, str]:
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


def retry_on_failure(func, max_retries: int = 2, *args, **kwargs):
    """
    重试包装器：失败时重试最多 max_retries 次

    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        *args, **kwargs: 传递给 func 的参数

    Returns:
        func 的返回值

    Raises:
        最后一次尝试的异常
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                print(f"  [RETRY] 第 {attempt + 1} 次失败，重试中... ({e})")
    raise last_error
