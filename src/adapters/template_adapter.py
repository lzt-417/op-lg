"""
模板适配器：读取 XFQ-Project 的模板文件
"""
import os
from pathlib import Path


def _default_xfq_root() -> str:
    """从环境变量获取 XFQ-Project 路径，未设置时使用默认值"""
    return os.getenv("XFQ_ROOT", "C:/Users/Administrator/Desktop/XFQ-Project")


class TemplateAdapter:
    """读取 XFQ-Project 的模板"""

    def __init__(self, xfq_root: str = None):
        self.xfq_root = Path(xfq_root or _default_xfq_root())
        self.template_dir = self.xfq_root / "pipeline" / "templates"

    def get_reader_persona_template(self) -> str:
        """读取读者画像模板"""
        path = self.template_dir / "reader-persona.md"
        if not path.exists():
            raise FileNotFoundError(f"模板文件不存在：{path}")
        return path.read_text(encoding="utf-8")

    def get_chapter_outline_template(self) -> str:
        """读取章纲模板"""
        path = self.template_dir / "prompt-chapter-outline.md"
        if not path.exists():
            raise FileNotFoundError(f"模板文件不存在：{path}")
        return path.read_text(encoding="utf-8")

    def get_style_fingerprint_template(self) -> str:
        """读取风格指纹模板"""
        path = self.template_dir / "prompt-style-fingerprint.md"
        if not path.exists():
            raise FileNotFoundError(f"模板文件不存在：{path}")
        return path.read_text(encoding="utf-8")

    def get_arc_outline_template(self) -> str:
        """读取 Arc 大纲模板"""
        path = self.template_dir / "prompt-arc-outline.md"
        if not path.exists():
            raise FileNotFoundError(f"模板文件不存在：{path}")
        return path.read_text(encoding="utf-8")
