"""
N1 节点：读者画像生成
"""
from typing import Dict, Any
from ..state.planning_state import PlanningState
from ..adapters.template_adapter import TemplateAdapter
from ..adapters.source_adapter import SourceDataAdapter
from ..utils.llm_client import LLMClient


class N1ReaderPersonaNode:
    """N1 节点：生成读者画像"""

    def __init__(
        self,
        llm_client: LLMClient,
        template_adapter: TemplateAdapter,
        source_adapter: SourceDataAdapter,
    ):
        self.llm_client = llm_client
        self.template_adapter = template_adapter
        self.source_adapter = source_adapter

    def __call__(self, state: PlanningState) -> PlanningState:
        """
        执行 N1 节点

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        print("N1 节点：开始生成读者画像...")

        try:
            # 1. 读取模板和源数据
            print("  - 读取读者画像数据库...")
            database = self.source_adapter.get_reader_persona_database()

            print("  - 读取模板...")
            template = self.template_adapter.get_reader_persona_template()

            # 2. 构造 Prompt
            system_prompt = template
            user_prompt = f"""Reader Persona Database:
{database}

请基于以上调研数据，生成一个完整的读者画像。严格遵循模板格式，不要使用占位符，全部填入具体内容。"""

            # 3. 调用 LLM
            print("  - 调用 LLM 生成读者画像...")
            reader_persona = self.llm_client.invoke_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            # 4. 更新 State
            state["reader_persona"] = reader_persona
            state["current_node"] = "n1"

            print("N1 节点：读者画像生成完成")
            return state

        except Exception as e:
            state["last_error"] = f"N1 节点失败：{str(e)}"
            print(f"N1 节点失败：{str(e)}")
            return state
