"""
N2 节点：概念设计
"""
from ..state.planning_state import PlanningState
from ..adapters.source_adapter import SourceDataAdapter
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_concept, retry_on_failure


class N2ConceptNode:
    """N2 节点：生成概念设计"""

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

            system_prompt = """你是 Novelist Agent。为小说项目生成 3-5 个概念方案，供选择。

每个方案必须包含：
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

格式：
- 每个方案用 Markdown 分隔线分隔
- 不要占位符，全部填具体内容
- 在最后推荐一个最佳方案"""

            user_prompt = f"""读者画像：
{state["reader_persona"]}

多样性池：
{diversity_pools}

请基于以上信息生成 3-5 个概念方案，并推荐一个最佳方案。
注意：全部使用中文输出（专有名词如书名、平台名、术语可保留英文）。"""

            print("  - 调用 LLM 生成概念方案...")
            concept = retry_on_failure(
                self.llm_client.invoke_with_system, 2,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            # 验证输出
            ok, msg = validate_concept(concept)
            if not ok:
                raise ValueError(f"输出验证失败：{msg}")

            state["concept"] = concept
            state["current_node"] = "n2"

            print("N2 节点：概念设计生成完成")
            return state

        except Exception as e:
            state["last_error"] = f"N2 节点失败：{str(e)}"
            print(f"N2 节点失败：{str(e)}")
            return state
