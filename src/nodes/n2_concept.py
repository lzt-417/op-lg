"""
N2 节点：概念设计（三步流程：生成方案 → 选择 → 撰写）
"""
from ..state.planning_state import PlanningState
from ..adapters.source_adapter import SourceDataAdapter
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_concept, retry_on_validation_failure, append_retry_error


class N2ConceptNode:
    """N2 节点：生成概念设计（三步流程）"""

    def __init__(
        self,
        llm_client: LLMClient,
        source_adapter: SourceDataAdapter,
    ):
        self.llm_client = llm_client
        self.source_adapter = source_adapter

    def __call__(self, state: PlanningState) -> PlanningState:
        print("N2 节点：开始生成概念设计...")

        try:
            if "reader_persona" not in state or not state["reader_persona"]:
                raise ValueError("N1 未完成，缺少 reader_persona")

            diversity_pools = self.source_adapter.get_diversity_pools()

            # Step 1: 生成 3-5 个概念方案
            print("  - Step 1: 生成概念方案...")
            proposals = self._generate_proposals(state["reader_persona"], diversity_pools)

            # Step 2: 选择最佳方案（自动模式）
            print("  - Step 2: 选择最佳方案...")
            selected = self._select_best_proposal(proposals)

            # Step 3: 基于选定方案撰写完整 concept.md
            print("  - Step 3: 撰写 concept.md...")
            concept = retry_on_validation_failure(
                self._write_concept, validate_concept, 2,
                reader_persona=state["reader_persona"],
                diversity_pools=diversity_pools,
                selected_proposal=selected,
            )

            state["concept"] = concept
            state["current_node"] = "n2"

            print("N2 节点：概念设计生成完成")
            return state

        except Exception as e:
            state["last_error"] = f"N2 节点失败：{str(e)}"
            print(f"N2 节点失败：{str(e)}")
            return state

    def _generate_proposals(self, reader_persona: str, diversity_pools: str) -> str:
        """Step 1: 生成 3-5 个概念方案"""
        system_prompt = """你是 Novelist Agent。为小说项目生成 3-5 个概念方案，供选择。

每个方案必须包含：
- 方案编号（方案 1、方案 2...）
- Logline（一句话概述）
- 题材/类型
- 目标平台
- 目标读者
- 差异化点（为什么这本书会脱颖而出）
- 预期字数（章数/字数/Arc 数量）
- Arc 规划（Hook Arc Ch1-5 + Arc 1 + Arc 2 + ... 全部列出）
- 核心冲突（主角要什么 vs 什么在阻止 vs 妥协的代价）
- 参考作品
- 爽点设计
- 差异化变量（从 diversity-pools 选 18-20 个维度）

格式：每个方案用 Markdown 分隔线分隔，不要占位符。"""

        user_prompt = f"""读者画像：
{reader_persona}

多样性池：
{diversity_pools}

请基于以上信息生成 3-5 个概念方案。
注意：全部使用中文输出（专有名词如书名、平台名、术语可保留英文）。"""

        return self.llm_client.invoke_with_system(
            system_prompt=system_prompt, user_prompt=user_prompt,
        )

    def _select_best_proposal(self, proposals: str) -> str:
        """Step 2: 自动选择最佳方案"""
        system_prompt = """你是 Novelist Agent 的决策模块。从以下概念方案中选择最佳方案。

选择标准：
1. 差异化程度（是否在市场上有独特卖点）
2. 目标读者匹配度（是否符合读者画像的偏好）
3. Arc 可扩展性（是否能支撑多 Arc 长篇故事）
4. 爽点密度（是否有足够的读者吸引力）

输出格式：
- 先简要说明选择理由（2-3 句）
- 然后输出选定方案的完整内容（原样输出，不修改）"""

        user_prompt = f"""概念方案：
{proposals}

请选择最佳方案，说明理由并输出完整内容。"""

        return self.llm_client.invoke_with_system(
            system_prompt=system_prompt, user_prompt=user_prompt,
        )

    def _write_concept(self, **kwargs) -> str:
        """Step 3: 基于选定方案撰写完整 concept.md"""
        reader_persona = kwargs["reader_persona"]
        diversity_pools = kwargs["diversity_pools"]
        selected_proposal = kwargs["selected_proposal"]

        system_prompt = append_retry_error("""你是 Novelist Agent。基于选定的概念方案，撰写完整的 concept.md。

## concept.md 必须包含
- 项目概述（基于选定方案的 Logline 扩展）
- 题材/类型
- 目标平台
- 目标读者
- 差异化点
- 预期字数（章数/字数/Arc 数量）
- Arc 规划（Hook Arc Ch1-5 + Arc 1 + Arc 2 + ... 详细列出每 Arc 的章节范围和主题）
- 核心冲突（主角要什么 vs 什么在阻止 vs 妥协的代价）
- 参考作品
- 爽点设计
- 差异化变量（18-20 个维度，每个维度的选择理由）

## 要求
- 不要占位符，全部填具体内容
- Arc 规划必须详细到章节范围
- 全部使用中文输出（专有名词可保留英文）""", **kwargs)

        user_prompt = f"""读者画像：
{reader_persona}

多样性池：
{diversity_pools}

选定方案：
{selected_proposal}

请基于选定方案撰写完整的 concept.md。"""

        return self.llm_client.invoke_with_system(
            system_prompt=system_prompt, user_prompt=user_prompt,
        )
