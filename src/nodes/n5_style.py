"""
N5 节点：风格指纹
"""
from ..state.planning_state import PlanningState
from ..adapters.source_adapter import SourceDataAdapter
from ..adapters.template_adapter import TemplateAdapter
from ..utils.llm_client import LLMClient
from ..utils.validators import validate_style_fingerprint, validate_size, retry_on_validation_failure, append_retry_error


class N5StyleNode:
    """N5 节点：生成 10 维度风格指纹"""

    def __init__(
        self,
        llm_client: LLMClient,
        source_adapter: SourceDataAdapter,
        template_adapter: TemplateAdapter,
    ):
        self.llm_client = llm_client
        self.source_adapter = source_adapter
        self.template_adapter = template_adapter

    def __call__(self, state: PlanningState) -> PlanningState:
        print("N5 节点：开始生成风格指纹...")

        try:
            if "reader_persona" not in state or not state["reader_persona"]:
                raise ValueError("N1 未完成，缺少 reader_persona")

            # 验证 reader_persona 大小 > 500 bytes
            ok, msg = validate_size(state["reader_persona"], 500, "reader_persona")
            if not ok:
                raise ValueError(f"前置验证失败：{msg}")

            # 读取源数据（只读取这些，不读取故事内容）
            print("  - 读取源数据...")
            diversity_pools = self.source_adapter.get_diversity_pools()
            ai_blacklist = self.source_adapter.get_ai_patterns_blacklist()
            style_template = self.template_adapter.get_style_fingerprint_template()

            print("  - 生成风格指纹...")
            style_fingerprint = retry_on_validation_failure(
                self._generate_style, validate_style_fingerprint, 2,
                reader_persona=state["reader_persona"],
                diversity_pools=diversity_pools,
                ai_blacklist=ai_blacklist,
                style_template=style_template,
            )

            state["style_fingerprint"] = style_fingerprint
            state["current_node"] = "n5"

            print("N5 节点：风格指纹生成完成")
            return state

        except Exception as e:
            state["last_error"] = f"N5 节点失败：{str(e)}"
            print(f"N5 节点失败：{str(e)}")
            return state

    def _generate_style(self, **kwargs) -> str:
        reader_persona = kwargs["reader_persona"]
        diversity_pools = kwargs["diversity_pools"]
        ai_blacklist = kwargs["ai_blacklist"]
        style_template = kwargs["style_template"]
        system_prompt = f"""你是 Novelist Agent。为小说项目生成风格指纹（style_fingerprint.md）。

## 参考模板格式
{style_template}

## 风格指纹必须包含
1. POV / 叙事视角
2. 叙事语气（基调、幽默密度、自我意识模式）
3. 句式结构（主谓宾比例、长短句比例、段落长度规则）
4. 修辞配额（每章最大比喻/隐喻数量）
5. 感官优先级（描写顺序）
6. 对话规则（标签用法、潜台词、角色声音区分）
7. 禁用词（绝对禁止的词语/短语）
8. 章节开头规则
9. 章节结尾规则
10. 读者画像定制（根据读者耐心/偏好调整规则）

## AI 写作模式黑名单（必须遵守）
{ai_blacklist}

以上列表中的模式/词语**禁止**作为"允许的规则"、"推荐技巧"、"标志性句子"或"配额项目"出现在风格指纹中。
只能作为反面教材出现（教什么是不该做的）。

## 要求
- 不要占位符，所有规则都要填入具体内容
- 每条规则必须可执行（不是"对话要自然"，而是"用 said/asked 作标签，不要用 exclaimed/whispered"）
- 参考读者画像调整耐心/偏好
- 全部使用中文输出"""

        system_prompt = append_retry_error(system_prompt, **kwargs)

        user_prompt = f"""读者画像：
{reader_persona}

多样性池：
{diversity_pools}

请生成完整的风格指纹。全部使用中文输出。"""

        return self.llm_client.invoke_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
