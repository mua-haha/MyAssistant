import os
from typing import Dict, Any, Optional, List
from src.logging.setup import get_logger
from src.model.base import BaseLLMClient
from src.model.siliconflow import SiliconFlowClient
from src.model.ollama import OllamaClient

logger = get_logger("LLMFactory")


class LLMFactory:
    """LLM 客户端工厂类"""

    PROVIDERS = {
        "siliconflow": SiliconFlowClient,
        "ollama": OllamaClient,
    }

    @staticmethod
    def _resolve_env_var(value: str) -> str:
        """解析环境变量，如 ${VAR_NAME} -> 实际值"""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            return os.environ.get(var_name, "")
        return value

    @staticmethod
    def create(config: Dict[str, Any]) -> BaseLLMClient:
        """
        根据配置创建 LLM 客户端

        Args:
            config: 包含 provider, model, providers 配置

        Returns:
            LLM 客户端实例
        """
        provider_name = config.get("provider", "ollama")
        model = config.get("model", "")

        providers_config = config.get("providers", {})
        provider_config = providers_config.get(provider_name, {})

        if not provider_config.get("enabled", False):
            raise ValueError(f"Provider '{provider_name}' 未启用")

        client_config = {
            "base_url": provider_config.get("base_url", ""),
            "model": model,
            "api_key": LLMFactory._resolve_env_var(provider_config.get("api_key", "")),
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 2000),
        }

        client_class = LLMFactory.PROVIDERS.get(provider_name)
        if not client_class:
            raise ValueError(f"不支持的 provider: {provider_name}")

        logger.info(f"创建 LLM 客户端: provider={provider_name}, model={model}")
        return client_class(client_config)

    @staticmethod
    def get_available_models(config: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        获取所有可用的模型列表

        Args:
            config: 配置

        Returns:
            {provider_name: [model1, model2, ...], ...}
        """
        result = {}
        providers_config = config.get("providers", {})

        for provider_name, provider_config in providers_config.items():
            if provider_config.get("enabled", False):
                models = provider_config.get("models", [])
                if models:
                    result[provider_name] = models

        return result
