import requests
import json
from typing import Dict, Any, List, Optional
from src.logging.setup import get_logger

logger = get_logger("LLMClient")


class LLMClient:
    """LLM API 客户端，封装 SiliconFlow API 调用"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 LLM 客户端

        Args:
            config: 包含 base_url, model, api_key, temperature, max_tokens 等配置
        """
        self.base_url = config.get("base_url", "https://api.siliconflow.cn/v1")
        self.model = config.get("model", "Qwen/Qwen2.5-7B-Instruct")
        self.api_key = config.get("api_key", "")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)

        if not self.api_key:
            raise ValueError("API Key 未配置，请设置环境变量 SILICONFLOW_API_KEY 或在配置文件中设置")

        self.chat_endpoint = f"{self.base_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }

        logger.debug(f"LLM API 请求: {json.dumps(payload, ensure_ascii=False)}")

        try:
            response = requests.post(
                self.chat_endpoint,
                headers=self.headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

            result = response.json()
            logger.debug(f"LLM API 响应: {json.dumps(result, ensure_ascii=False)}")

            content = result["choices"][0]["message"]["content"]
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API 请求失败: {e}")
            raise RuntimeError(f"LLM API 请求失败: {e}")
        except (KeyError, IndexError) as e:
            logger.error(f"LLM API 响应格式错误: {e}")
            raise RuntimeError(f"LLM API 响应格式错误: {e}")

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
