"""
模板适配器：读取 XFQ-Project 的模板文件
"""
from pathlib import Path


class TemplateAdapter:
    """读取 XFQ-Project 的模板"""

    def __init__(self, xfq_root: str = "C:/Users/Administrator/Desktop/XFQ-Project"):
        self.xfq_root = Path(xfq_root)
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
