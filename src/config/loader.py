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
        config_key = self.get("llm.api_key", "")
        return config_key

    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        return {
            "base_url": self.get("llm.base_url", "https://api.siliconflow.cn/v1"),
            "model": self.get("llm.model", "Qwen/Qwen2.5-7B-Instruct"),
            "temperature": self.get("llm.temperature", 0.7),
            "max_tokens": self.get("llm.max_tokens", 2000),
            "api_key": self.get_llm_api_key(),
        }

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
