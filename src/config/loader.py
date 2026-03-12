import os
import yaml
from typing import Any, Dict, Optional


class Config:
    """配置加载器，支持从配置文件和环境变量读取配置"""

    def __init__(self, config_path: str = "config.yaml", prompts_path: str = "prompts.yaml"):
        self.config_path = config_path
        self.prompts_path = prompts_path
        self._config: Dict[str, Any] = {}
        self._prompts: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        if os.path.exists(self.prompts_path):
            with open(self.prompts_path, "r", encoding="utf-8") as f:
                self._prompts = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"提示词配置文件不存在: {self.prompts_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点分隔的键，如 'llm.api_key'"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def get_llm_api_key(self) -> str:
        """获取 LLM API Key，优先从环境变量读取"""
        env_key = os.environ.get("SILICONFLOW_API_KEY", "")
        if env_key:
            return env_key
        provider = self.get("llm.provider", "ollama")
        config_key = self.get(f"llm.providers.{provider}.api_key", "")
        if config_key and config_key.startswith("${") and config_key.endswith("}"):
            var_name = config_key[2:-1]
            return os.environ.get(var_name, "")
        return config_key

    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置（包含 provider、model、providers 配置）"""
        providers = self.get("llm.providers", {})
        return {
            "provider": self.get("llm.provider", "ollama"),
            "model": self.get("llm.model", "qwen2.5:7b"),
            "providers": providers,
            "temperature": self.get("llm.temperature", 0.7),
            "max_tokens": self.get("llm.max_tokens", 2000),
        }

    def get_current_llm_config(self) -> Dict[str, Any]:
        """获取当前使用的 LLM 完整配置（供 LLMFactory 使用）"""
        return self.get_llm_config()

    def set_llm_model(self, provider: str, model: str) -> bool:
        """
        设置当前使用的 LLM 模型

        Args:
            provider: provider 名称
            model: 模型名称

        Returns:
            是否设置成功
        """
        providers = self.get("llm.providers", {})
        provider_config = providers.get(provider, {})
        available_models = provider_config.get("models", [])

        if model not in available_models:
            return False

        self._config["llm"]["provider"] = provider
        self._config["llm"]["model"] = model
        return True

    def get_tools_config(self) -> Dict[str, Any]:
        """获取工具配置"""
        return self.get("tools", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get("logging", {})

    def get_prompts(self) -> Dict[str, Any]:
        """获取提示词配置"""
        return self._prompts


_config: Optional[Config] = None


def get_config(config_path: str = "config.yaml", prompts_path: str = "prompts.yaml") -> Config:
    """获取配置单例"""
    global _config
    if _config is None:
        _config = Config(config_path, prompts_path)
    return _config
