import json
import re
import yaml
from typing import Dict, Any, Optional
from src.model.base import BaseLLMClient
from src.logging.setup import get_logger

logger = get_logger("ParamService")


class ParamService:
    """参数生成服务 - LLM2：根据用户输入和 Tool 上下文生成参数"""

    def __init__(self, llm_client: BaseLLMClient, prompts: Dict[str, Any]):
        self.llm_client = llm_client
        self.prompts = prompts

    def generate_params(self, user_input: str, tool: Any, session_history: Optional[str] = None) -> Dict[str, Any]:
        """
        生成 Tool 执行所需的参数

        Args:
            user_input: 用户输入的自然语言
            tool: 选中的 Tool 对象
            session_history: 会话历史（可选）

        Returns:
            参数字典
        """
        logger.info(f"开始生成参数，工具: {tool.name}")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(user_input, tool, session_history)

        logger.info("调用 LLM 生成参数...")
        response = self.llm_client.chat_with_system_and_user(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        logger.debug(f"LLM 原始响应: {response}")

        params = self._parse_response(response, tool)
        logger.info(f"生成的参数: {json.dumps(params, ensure_ascii=False)}")

        return params

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        system_prompt = self.prompts.get("system", "")
        if system_prompt:
            return system_prompt
        
        return """你是一个参数生成助手。
你的任务是根据用户输入和工具的描述，生成工具执行所需的参数。

请根据以下信息生成参数JSON。

输出格式:
params: {"参数名": "参数值"}"""

    def _build_user_prompt(self, user_input: str, tool: Any, session_history: Optional[str] = None) -> str:
        """构建用户提示"""
        schema_str = yaml.dump(tool.params_schema, allow_unicode=True, default_flow_style=False)
        
        # 获取 tool 的 prompt_hint
        prompt_hint = getattr(tool, 'prompt_hint', '') or ''
        
        history_section = ""
        if session_history and session_history != "（无历史记录）":
            history_section = f"""【对话历史】
{session_history}

【说明】
用户可能提到"再"、"刚才"、"上一次"等，需要结合历史记录理解用户真正要执行的操作和参数。

"""
        
        user_prompt_template = self.prompts.get("user", "")
        if user_prompt_template:
            return user_prompt_template.format(
                user_input=user_input,
                tool_name=tool.name,
                tool_description=tool.description,
                schema=schema_str,
                session_history=history_section,
                prompt_hint=prompt_hint,
            )
        
        hint_section = f"\n{prompt_hint}\n" if prompt_hint else ""
        
        return f"""{history_section}用户输入: {user_input}
工具名称: {tool.name}
工具描述: {tool.description}
工具参数Schema:
{schema_str}
{hint_section}
请生成参数JSON。"""

    def _parse_response(self, response: str, tool: Any) -> Dict[str, Any]:
        """解析 LLM 响应，提取参数"""
        if "<think>" in response:
            match = re.search(r"</think>\s*(.+)", response, re.DOTALL)
            if match:
                response = match.group(1).strip()
        
        match = re.search(r"params:\s*(\{.*?\})", response, re.DOTALL)
        if match:
            try:
                params_json = match.group(1)
                params = json.loads(params_json)
                return params
            except json.JSONDecodeError as e:
                logger.warning(f"参数JSON解析失败: {e}")

        logger.warning("无法解析参数，使用空参数")
        return {}
