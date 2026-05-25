"""
N2 节点：概念设计
"""
from typing import Dict, Any
from ..state.planning_state import PlanningState
from ..adapters.source_adapter import SourceDataAdapter
from ..utils.llm_client import LLMClient


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
        """
        执行 N2 节点

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        print("N2 节点：开始生成概念设计...")

        try:
            # 检查前置条件
            if "reader_persona" not in state or not state["reader_persona"]:
                raise ValueError("N1 未完成，缺少 reader_persona")

            # 1. 读取源数据
            print("  - 读取 diversity-pools...")
            diversity_pools = self.source_adapter.get_diversity_pools()

            # 2. 构造 Prompt
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

            user_prompt = f"""Reader Persona:
{state["reader_persona"]}

Diversity Pools:
{diversity_pools}

请基于以上信息生成 3-5 个概念方案，并推荐一个最佳方案。"""

            # 3. 调用 LLM
            print("  - 调用 LLM 生成概念方案...")
            concept = self.llm_client.invoke_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            # 4. 更新 State
            state["concept"] = concept
            state["current_node"] = "n2"

            print("N2 节点：概念设计生成完成")
            return state

        except Exception as e:
            state["last_error"] = f"N2 节点失败：{str(e)}"
            print(f"N2 节点失败：{str(e)}")
            return state
