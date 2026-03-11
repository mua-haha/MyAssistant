# personal-assistant/src/session.py
from typing import Dict, List, Any
from src.logging.setup import get_logger

logger = get_logger("Session")


class Session:
    """会话管理类，管理当前会话的上下文"""

    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def add(self, user_input: str, assistant_output: str):
        """添加对话记录"""
        self.history.append({
            "user": user_input,
            "assistant": assistant_output,
        })
        logger.debug(f"添加对话记录，当前历史条数: {len(self.history)}")

    def clear(self):
        """清空会话历史"""
        self.history.clear()
        logger.info("会话历史已清空")

    def get_history_text(self) -> str:
        """获取格式化的历史记录，供 LLM 使用"""
        if not self.history:
            return "（无历史记录）"

        history_parts = []
        for i, item in enumerate(self.history, 1):
            history_parts.append(
                f"第{i}轮对话\n"
                f"用户: {item['user']}\n"
                f"助手: {item['assistant']}"
            )
        return "\n\n".join(history_parts)

    def get_last_interaction(self) -> Dict[str, str]:
        """获取上一轮对话"""
        if self.history:
            return self.history[-1]
        return {}

    def __len__(self):
        return len(self.history)
