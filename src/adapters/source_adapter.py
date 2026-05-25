"""
源数据适配器：读取 XFQ-Project 的源数据文件
"""
from pathlib import Path


class SourceDataAdapter:
    """读取 XFQ-Project 的源数据"""

    def __init__(self, xfq_root: str = "C:/Users/Administrator/Desktop/XFQ-Project"):
        self.xfq_root = Path(xfq_root)
        self.source_dir = self.xfq_root / "pipeline" / "source"

    def get_diversity_pools(self) -> str:
        """读取多样化选项池"""
        path = self.source_dir / "diversity-pools.md"
        if not path.exists():
            raise FileNotFoundError(f"源数据文件不存在：{path}")
        return path.read_text(encoding="utf-8")

    def get_ai_patterns_blacklist(self) -> str:
        """读取 AI 写作负面清单"""
        path = self.source_dir / "ai-patterns-blacklist.md"
        if not path.exists():
            raise FileNotFoundError(f"源数据文件不存在：{path}")
        return path.read_text(encoding="utf-8")

    def get_reader_persona_database(self) -> str:
        """读取读者画像数据库"""
        path = self.source_dir / "reader-persona-database.md"
        if not path.exists():
            raise FileNotFoundError(f"源数据文件不存在：{path}")
        return path.read_text(encoding="utf-8")
