from typing import Dict, Any, Optional
from src.model.llm_client import LLMClient
from src.logging.setup import get_logger

logger = get_logger("ResponseService")


class ResponseService:
    """回复生成服务 - LLM3：根据工具执行结果生成自然语言回复"""

    def __init__(self, llm_client: LLMClient, prompts: Dict[str, Any]):
        self.llm_client = llm_client
        self.prompts = prompts

    def generate(self, user_input: str, tool_result: str, session_history: Optional[str] = None) -> str:
        """
        生成自然语言回复

        Args:
            user_input: 用户原始输入
            tool_result: 工具执行结果
            session_history: 会话历史（可选）

        Returns:
            自然语言回复
        """
        logger.info("开始生成回复")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(user_input, tool_result, session_history)

        logger.info("调用 LLM 生成回复...")
        response = self.llm_client.chat_with_system_and_user(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        logger.info(f"最终回复: {response}")
        return response

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        system_prompt = self.prompts.get("system", "")
        if system_prompt:
            return system_prompt
        
        return """你是一个回复生成助手。
你的任务是根据工具执行结果，用自然、友好的语言回复用户。

请直接输出回复内容，不要添加任何格式或解释。"""

    def _build_user_prompt(self, user_input: str, tool_result: str, session_history: Optional[str] = None) -> str:
        """构建用户提示"""
        history_section = ""
        if session_history and session_history != "（无历史记录）":
            history_section = f"""【对话历史】
{session_history}

"""
        
        user_prompt_template = self.prompts.get("user", "")
        if user_prompt_template:
            return user_prompt_template.format(
                user_input=user_input,
                tool_result=tool_result,
                session_history=history_section,
            )
        
        return f"""{history_section}用户原始输入: {user_input}
工具执行结果: {tool_result}

请用自然、友好的语言回复用户："""
