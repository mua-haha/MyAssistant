import requests
import json
from typing import Dict, Any, List, Optional
from src.logging.setup import get_logger
from src.model.base import BaseLLMClient

logger = get_logger("OllamaClient")


class OllamaClient(BaseLLMClient):
    """Ollama 本地模型客户端"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.chat_endpoint = f"{self.base_url}/api/chat"
        self.headers = {
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "ollama"

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
            "options": {
                "num_predict": tokens,
            },
            "stream": False,
        }

        logger.debug(f"Ollama API 请求: {json.dumps(payload, ensure_ascii=False)}")

        try:
            response = requests.post(
                self.chat_endpoint,
                headers=self.headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Ollama API 响应: {json.dumps(result, ensure_ascii=False)}")

            content = result["message"]["content"]
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API 请求失败: {e}")
            raise RuntimeError(f"Ollama API 请求失败: {e}")
        except (KeyError, IndexError) as e:
            logger.error(f"Ollama API 响应格式错误: {e}")
            raise RuntimeError(f"Ollama API 响应格式错误: {e}")
