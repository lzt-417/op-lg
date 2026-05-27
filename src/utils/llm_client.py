"""
LLM 客户端封装
"""
import os
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# 需要流式模式的模型
STREAM_ONLY_MODELS = ["glm-4.5-air"]


class LLMClient:
    """LLM 调用封装，支持 OpenAI 和 Anthropic（包括兼容接口）"""

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 默认模型
        if model is None:
            model = "gpt-4o" if provider == "openai" else "claude-sonnet-4-6-20250514"

        self.model = model
        self.use_stream = any(m in model.lower() for m in STREAM_ONLY_MODELS)

        # 获取 API Key
        if api_key is None:
            api_key = os.environ.get(
                "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"
            )

        # 初始化 LLM
        if provider == "openai":
            kwargs = {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "api_key": api_key,
            }
            # qwen3 系列需要此参数
            if "qwen3" in model.lower():
                kwargs["extra_body"] = {"enable_thinking": False}
            if base_url:
                kwargs["base_url"] = base_url
            self.llm = ChatOpenAI(**kwargs)
        elif provider == "anthropic":
            kwargs = {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "api_key": api_key,
            }
            if base_url:
                kwargs["base_url"] = base_url
            self.llm = ChatAnthropic(**kwargs)
        else:
            raise ValueError(f"不支持的 LLM provider: {provider}")

    def invoke(
        self,
        messages: List[BaseMessage],
        **kwargs
    ) -> str:
        """
        调用 LLM（自动选择流式或非流式）

        Args:
            messages: 消息列表（SystemMessage, HumanMessage 等）
            **kwargs: 其他参数

        Returns:
            LLM 的响应文本
        """
        if self.use_stream:
            return self._invoke_stream(messages, **kwargs)
        response = self.llm.invoke(messages, **kwargs)
        return (response.content or "").replace("\x00", "")

    def _invoke_stream(self, messages: List[BaseMessage], **kwargs) -> str:
        """流式调用 LLM，收集所有 chunks 返回完整文本"""
        full_content = ""
        for chunk in self.llm.stream(messages, **kwargs):
            if chunk.content:
                full_content += chunk.content
        # 过滤 null 字节（某些模型流式输出会带 \x00）
        return full_content.replace("\x00", "")

    def invoke_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> str:
        """
        使用 system + user prompt 调用 LLM

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            **kwargs: 其他参数

        Returns:
            LLM 的响应文本
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        return self.invoke(messages, **kwargs)
