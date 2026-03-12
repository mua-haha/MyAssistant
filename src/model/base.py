from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 LLM 客户端

        Args:
            config: 包含 base_url, model, api_key, temperature, max_tokens 等配置
        """
        self.base_url = config.get("base_url", "")
        self.model = config.get("model", "")
        self.api_key = config.get("api_key", "")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        调用 LLM API 获取回复

        Args:
            messages: 消息列表，格式为 [{"role": "user/system/assistant", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            LLM 的回复内容
        """
        pass

    def chat_with_system_and_user(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        便捷方法：使用 system prompt 和 user prompt 调用 LLM

        Args:
            system_prompt: 系统提示
            user_prompt: 用户输入
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            LLM 的回复内容
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.chat(messages, temperature, max_tokens)

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """返回 provider 名称"""
        pass
