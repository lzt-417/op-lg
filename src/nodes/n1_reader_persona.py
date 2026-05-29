"""
N1 节点：读者画像生成
"""
from ..state.planning_state import PlanningState
from ..adapters.template_adapter import TemplateAdapter
from ..adapters.source_adapter import SourceDataAdapter
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_reader_persona, retry_on_validation_failure


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
        print("N1 节点：开始生成读者画像...")

        try:
            database = self.source_adapter.get_reader_persona_database()
            template = self.template_adapter.get_reader_persona_template()

            system_prompt = template
            user_prompt = f"""读者调研数据库：
{database}

请基于以上调研数据，生成一个完整的读者画像。严格遵循模板格式，不要使用占位符，全部填入具体内容。
注意：全部使用中文输出（专有名词如书名、平台名可保留英文）。"""

            print("  - 调用 LLM 生成读者画像...")
            reader_persona = retry_on_validation_failure(
                self._generate, validate_reader_persona, 2,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            state["reader_persona"] = reader_persona
            state["current_node"] = "n1"

            print("N1 节点：读者画像生成完成")
            return state

        except Exception as e:
            state["last_error"] = f"N1 节点失败：{str(e)}"
            print(f"N1 节点失败：{str(e)}")
            return state

    def _generate(self, **kwargs) -> str:
        system_prompt = kwargs.get("system_prompt", "")
        user_prompt = kwargs.get("user_prompt", "")
        return self.llm_client.invoke_with_system(system_prompt=system_prompt, user_prompt=user_prompt)
