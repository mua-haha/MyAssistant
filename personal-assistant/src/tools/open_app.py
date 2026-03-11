import subprocess
import webbrowser
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.logging.setup import get_logger

logger = get_logger("OpenAppTool")


class Tool(ABC):
    """Tool 基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool 名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool 描述"""
        pass

    @property
    @abstractmethod
    def params_schema(self) -> Dict[str, Any]:
        """参数 Schema"""
        pass

    @property
    def prompt_hint(self) -> str:
        """参数生成提示词（可选）"""
        return ""

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """执行 Tool"""
        pass


class OpenAppTool(Tool):
    """打开应用程序或网页的工具"""

    def __init__(self, supported_apps=None):
        self._supported_apps = supported_apps or ["chrome", "edge"]

    @property
    def name(self) -> str:
        return "open_app"

    @property
    def description(self) -> str:
        return "打开本地应用程序或浏览器访问指定网页"

    @property
    def params_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "操作类型：open_app（打开应用）或 open_url（打开网页）",
                    "enum": ["open_app", "open_url"],
                },
                "app_name": {
                    "type": "string",
                    "description": f"应用名称，支持: {', '.join(self._supported_apps)}",
                },
                "url": {
                    "type": "string",
                    "description": "要打开的网页URL",
                },
            },
            "required": ["action"],
        }

    @property
    def prompt_hint(self) -> str:
        return """【重要】open_app 工具参数规则：
- 如果用户提到"网站"、"网址"、网页名称（如"打开百度"、"访问google"），使用 action: "open_url"，url 参数填写网址
- 如果用户明确说"打开应用"、"启动软件"（如"打开微信"、"打开记事本"），使用 action: "open_app"，app_name 参数填写应用名
- 如果用户只说了"打开"但没有指定具体内容，默认使用 action: "open_app"
"""

    def execute(self, **kwargs) -> str:
        """执行打开应用或网页的操作"""
        action = kwargs.get("action", "open_app")

        if action == "open_url":
            url = kwargs.get("url", "")
            if not url:
                return "错误：未提供网页地址"
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            logger.info(f"正在打开网页: {url}")
            webbrowser.open(url)
            return f"已成功打开网页: {url}"

        elif action == "open_app":
            app_name = kwargs.get("app_name", "").lower()
            if not app_name:
                return "错误：未提供应用名称"

            if app_name not in self._supported_apps:
                return f"错误：不支持的应用 '{app_name}'，支持的应用有: {', '.join(self._supported_apps)}"

            app_map = {
                "chrome": "chrome",
                "edge": "msedge",
            }

            exe_name = app_map.get(app_name, app_name)
            logger.info(f"正在打开应用: {app_name}")

            try:
                subprocess.Popen(["start", "", exe_name], shell=True)
                return f"已成功打开应用: {app_name}"
            except FileNotFoundError:
                return f"错误：未找到应用 '{app_name}'，请确认已安装该应用"
            except Exception as e:
                logger.error(f"打开应用失败: {e}")
                return f"错误：打开应用失败 - {str(e)}"

        return f"错误：未知的操作"
