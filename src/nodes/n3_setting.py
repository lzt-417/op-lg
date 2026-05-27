"""
N3 节点：世界观与角色设定
"""
from ..state.planning_state import PlanningState
from ..adapters.source_adapter import SourceDataAdapter
from ..utils.llm_client import LLMClient
from ..utils.validators import (
    validate_worldbuilding, validate_characters, validate_story_graph,
    validate_keyword, retry_on_validation_failure,
)


class N3SettingNode:
    """N3 节点：生成世界观、角色设定、剧情关系图"""

    def __init__(
        self,
        llm_client: LLMClient,
        source_adapter: SourceDataAdapter,
    ):
        self.llm_client = llm_client
        self.source_adapter = source_adapter

    def __call__(self, state: PlanningState) -> PlanningState:
        print("N3 节点：开始生成世界观与角色设定...")

        try:
            if "concept" not in state or not state["concept"]:
                raise ValueError("N2 未完成，缺少 concept")

            # 验证前置输入包含 Arc 规划
            ok, msg = validate_keyword(state["concept"], ["Arc", "arc"], "concept")
            if not ok:
                raise ValueError(f"前置验证失败：{msg}")

            diversity_pools = self.source_adapter.get_diversity_pools()

            # Step 1: 生成世界观 + 角色设定（带验证重试）
            print("  - Step 1: 生成世界观与角色设定...")
            result = retry_on_validation_failure(
                self._generate_world_and_characters, self._validate_world_characters, 2,
                concept=state["concept"], diversity_pools=diversity_pools,
            )
            worldbuilding = self._extract_section(result, "WORLDBUILDING")
            characters = self._extract_section(result, "CHARACTERS")

            if not worldbuilding or not characters:
                parts = result.split("---")
                if len(parts) >= 2:
                    worldbuilding = worldbuilding or parts[0].strip()
                    characters = characters or parts[1].strip()
                else:
                    worldbuilding = worldbuilding or result
                    characters = characters or result

            # Step 2: 生成剧情关系图（带验证重试）
            print("  - Step 2: 生成剧情关系图...")
            story_graph = retry_on_validation_failure(
                self._generate_story_graph, validate_story_graph, 2,
                concept=state["concept"], worldbuilding=worldbuilding, characters=characters,
            )

            state["world_setting"] = worldbuilding
            state["character_cards"] = characters
            state["story_graph"] = story_graph
            state["current_node"] = "n3"

            print("N3 节点：世界观与角色设定生成完成")
            return state

        except Exception as e:
            state["last_error"] = f"N3 节点失败：{str(e)}"
            print(f"N3 节点失败：{str(e)}")
            return state

    def _generate_world_and_characters(self, **kwargs) -> str:
        concept = kwargs["concept"]
        diversity_pools = kwargs["diversity_pools"]

        system_prompt = """你是 Novelist Agent。为小说项目生成世界观设定和角色设定。

## worldbuilding.md 必须包含
- 世界观设定（地理、政治、经济、文化、科技、关键地点、历史设定）
- 力量体系（谁在掌权、如何运作、规则是什么）
- 社会/阶层的结构和冲突

## characters.md 必须包含
- 主角：性格内核、行为模式、口头禅、人际关系、成长弧
- 主要配角：3-5 个，每个有名字、角色功能、与主角的关系
- 反派/阻力：谁在对抗主角、他们的动机是什么
- 标注 diversity-pools 中的选项

## 要求
- 不要占位符，全部填具体内容
- 设定要自洽，与 concept.md 中的 Arc 规划一致
- 角色名字要符合 concept.md 中的命名体系

请用以下格式输出：

===WORLDBUILDING_START===
（worldbuilding.md 的完整内容）
===WORLDBUILDING_END===

===CHARACTERS_START===
（characters.md 的完整内容）
===CHARACTERS_END==="""

        user_prompt = f"""概念设计：
{concept}

多样性池：
{diversity_pools}

请基于以上信息生成世界观设定和角色设定。全部使用中文输出。"""

        return self.llm_client.invoke_with_system(
            system_prompt=system_prompt, user_prompt=user_prompt,
        )

    def _validate_world_characters(self, result: str, **kwargs) -> tuple:
        """验证世界观+角色设定的输出"""
        worldbuilding = self._extract_section(result, "WORLDBUILDING")
        characters = self._extract_section(result, "CHARACTERS")

        if not worldbuilding or not characters:
            parts = result.split("---")
            if len(parts) >= 2:
                worldbuilding = worldbuilding or parts[0].strip()
                characters = characters or parts[1].strip()
            else:
                worldbuilding = worldbuilding or result
                characters = characters or result

        ok, msg = validate_worldbuilding(worldbuilding)
        if not ok:
            return False, f"worldbuilding: {msg}"
        ok, msg = validate_characters(characters)
        if not ok:
            return False, f"characters: {msg}"
        return True, ""

    def _generate_story_graph(self, **kwargs) -> str:
        concept = kwargs["concept"]
        worldbuilding = kwargs["worldbuilding"]
        characters = kwargs["characters"]

        system_prompt = """你是 Novelist Agent。为小说项目生成剧情关系图。

## story_graph.md 必须包含
- 剧情追踪线（F01, F02... 编号，每行：ID + 描述 + 起始章节 + 结束章节）
- 角色关系变化时标注
- 信息差追踪（谁知道什么、什么时候知道、主角不知道什么）

## 要求
- 追踪线编号用 F01, F02, F03... 格式
- 每条追踪线要有明确的起止章节
- 信息差部分要标注清楚时间节点"""

        user_prompt = f"""概念设计：
{concept}

世界观设定：
{worldbuilding}

角色设定：
{characters}

请基于以上信息生成剧情关系图。全部使用中文输出。"""

        return self.llm_client.invoke_with_system(
            system_prompt=system_prompt, user_prompt=user_prompt,
        )

    def _extract_section(self, text: str, tag: str) -> str:
        start_marker = f"==={tag}_START==="
        end_marker = f"==={tag}_END==="
        start_idx = text.find(start_marker)
        end_idx = text.find(end_marker)
        if start_idx != -1 and end_idx != -1:
            return text[start_idx + len(start_marker):end_idx].strip()
        return ""
