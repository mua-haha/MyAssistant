from typing import Dict, Any
from src.logging.setup import get_logger

logger = get_logger("ToolExecutor")


class ToolExecutor:
    """Tool 执行器 - 执行选中的 Tool"""

    def __init__(self, tools: Dict[str, Any]):
        """
        初始化执行器

        Args:
            tools: 工具字典，key 为工具名称，value 为工具对象
        """
        self.tools = tools

    def execute(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        执行 Tool

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            执行结果
        """
        logger.info(f"开始执行工具: {tool_name}")
        logger.debug(f"工具参数: {params}")

        tool = self.tools.get(tool_name)
        if not tool:
            error_msg = f"错误：未找到工具 {tool_name}"
            logger.error(error_msg)
            return error_msg

        try:
            result = tool.execute(**params)
            logger.info(f"工具执行成功，结果: {result}")
            return result
        except Exception as e:
            error_msg = f"工具执行失败: {str(e)}"
            logger.error(error_msg)
            return error_msg
