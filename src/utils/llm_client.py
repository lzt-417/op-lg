"""
LLM 客户端封装
"""
import os
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


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
                "extra_body": {"enable_thinking": False},  # qwen3 需要此参数
            }
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
        调用 LLM

        Args:
            messages: 消息列表（SystemMessage, HumanMessage 等）
            **kwargs: 其他参数

        Returns:
            LLM 的响应文本
        """
        response = self.llm.invoke(messages, **kwargs)
        return response.content

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
