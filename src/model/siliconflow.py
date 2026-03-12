import requests
import json
from typing import Dict, Any, List, Optional
from src.logging.setup import get_logger
from src.model.base import BaseLLMClient

logger = get_logger("SiliconFlowClient")


class SiliconFlowClient(BaseLLMClient):
    """SiliconFlow API 客户端"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not self.api_key:
            raise ValueError("SiliconFlow API Key 未配置，请设置环境变量 SILICONFLOW_API_KEY 或在配置文件中设置")

        self.chat_endpoint = f"{self.base_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "siliconflow"

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }

        logger.debug(f"SiliconFlow API 请求: {json.dumps(payload, ensure_ascii=False)}")

        try:
            response = requests.post(
                self.chat_endpoint,
                headers=self.headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

            result = response.json()
            logger.debug(f"SiliconFlow API 响应: {json.dumps(result, ensure_ascii=False)}")

            content = result["choices"][0]["message"]["content"]
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"SiliconFlow API 请求失败: {e}")
            raise RuntimeError(f"SiliconFlow API 请求失败: {e}")
        except (KeyError, IndexError) as e:
            logger.error(f"SiliconFlow API 响应格式错误: {e}")
            raise RuntimeError(f"SiliconFlow API 响应格式错误: {e}")
