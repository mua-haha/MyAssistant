import json
import re
from typing import Dict, Any, List, Tuple, Optional
from src.model.base import BaseLLMClient
from src.logging.setup import get_logger

logger = get_logger("IntentService")


class IntentService:
    """意图识别服务 - LLM1：识别用户意图，选择使用哪个 Tool"""

    def __init__(self, llm_client: BaseLLMClient, tools: List[Any], prompts: Dict[str, Any]):
        self.llm_client = llm_client
        self.tools = tools
        self.prompts = prompts

    def recognize(self, user_input: str, session_history: Optional[str] = None) -> Tuple[str, str]:
        """
        识别用户意图，返回意图类型和工具名称

        Args:
            user_input: 用户输入的自然语言
            session_history: 会话历史（可选）

        Returns:
            (intent_type, tool_name): 意图类型("tool"/"chitchat") 和 工具名称
        """
        logger.info(f"开始意图识别，用户输入: {user_input}")

        tool_list = self._build_tool_list()
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(user_input, session_history)

        logger.info("调用 LLM 进行意图识别...")
        response = self.llm_client.chat_with_system_and_user(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        logger.debug(f"LLM 原始响应: {response}")

        intent, tool_name = self._parse_response(response)
        logger.info(f"识别结果: intent={intent}, tool={tool_name}")

        return intent, tool_name

    def _build_tool_list(self) -> str:
        """构建工具列表描述"""
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        return "\n".join(tool_descriptions)

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        tool_list = self._build_tool_list()
        
        system_prompt_template = self.prompts.get("system", "")
        if system_prompt_template:
            return system_prompt_template.format(tool_list=tool_list)
        
        return f"""你是一个意图识别助手。
你的任务是从用户输入中识别用户的意图，并选择最合适的工具来执行操作。

可选意图：
1. chitchat - 用户只是想闲聊、聊天、问候等，不需要执行具体操作
2. tool - 用户想要执行某个操作，需要调用工具

工具列表：
{tool_list}

如果用户只是想闲聊（如问候、聊天、问候天气等），输出：
intent: chitchat

如果用户想要执行操作，从工具列表中选择一个最合适的工具，输出：
intent: tool
tool: 工具名称

请根据用户输入判断是闲聊还是需要执行工具。"""

    def _build_user_prompt(self, user_input: str, session_history: Optional[str] = None) -> str:
        """构建用户提示"""
        history_section = ""
        if session_history and session_history != "（无历史记录）":
            history_section = f"""【对话历史】
{session_history}

【说明】
用户可能提到"再"、"刚才"、"上一次"等，需要结合历史记录理解用户的真实意图。

"""
        
        return f"""{history_section}用户输入: {user_input}"""

    def _parse_response(self, response: str) -> tuple:
        """解析 LLM 响应，提取意图和工具名称
        
        Returns:
            (intent, tool_name): 意图类型和工具名称
        """
        response_lower = response.lower()
        
        if "<think>" in response_lower:
            match = re.search(r"</think>\s*(.+)", response, re.DOTALL)
            if match:
                response = match.group(1).strip()
                response_lower = response.lower()
        
        if "chitchat" in response_lower or "闲聊" in response:
            return ("chitchat", None)
        
        match = re.search(r"tool:\s*(\w+)", response, re.IGNORECASE)
        if match:
            tool_name = match.group(1)
            for tool in self.tools:
                if tool.name.lower() == tool_name.lower():
                    return ("tool", tool.name)
        
        for tool in self.tools:
            if tool.name.lower() in response_lower:
                return ("tool", tool.name)
        
        if self.tools:
            logger.warning(f"无法解析工具名称，使用默认工具: {self.tools[0].name}")
            return ("tool", self.tools[0].name)
        
        return ("chitchat", None)

    def generate_plan(self, user_input: str, session_history: Optional[str] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        生成行动计划

        Args:
            user_input: 用户输入
            session_history: 会话历史

        Returns:
            (intent, plan): 意图类型和行动计划列表
        """
        logger.info(f"开始生成行动计划，用户输入: {user_input}")

        tool_list = self._build_tool_list()
        
        system_prompt = self._build_plan_system_prompt(tool_list)
        user_prompt = self._build_user_prompt(user_input, session_history)

        logger.info("调用 LLM 生成行动计划...")
        response = self.llm_client.chat_with_system_and_user(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        logger.debug(f"LLM 原始响应: {response}")

        intent, plan = self._parse_plan_response(response)
        logger.info(f"识别结果: intent={intent}, plan={plan}")

        return intent, plan

    def _build_plan_system_prompt(self, tool_list: str) -> str:
        """构建生成计划用的系统提示"""
        return f"""你是一个任务规划助手。
你的任务是根据用户需求，分析需要执行的步骤，并生成行动计划。

可用工具：
{tool_list}

【重要规则】
- 每个步骤必须使用上述工具之一
- 如果用户只需要闲聊，不需要执行任何工具，输出 "intent: chitchat"
- 如果需要执行工具，输出行动计划
- 最多生成10个步骤
- 步骤要具体、明确

输出格式：
如果是闲聊：
intent: chitchat

如果需要执行工具：
intent: tool
plan:
1. [步骤序号]. [工具名称] - [步骤描述]
2. [步骤序号]. [工具名称] - [步骤描述]
...

请生成行动计划："""

    def _parse_plan_response(self, response: str) -> tuple:
        """解析 LLM 响应，提取意图和行动计划"""
        response_lower = response.lower()
        
        if "<think>" in response_lower:
            match = re.search(r"</think>\s*(.+)", response, re.DOTALL)
            if match:
                response = match.group(1).strip()
                response_lower = response.lower()
        
        if "chitchat" in response_lower or "闲聊" in response:
            return ("chitchat", [])
        
        plan = []
        lines = response.split('\n')
        for line in lines:
            match = re.match(r"\d+\.\s*(\w+)\s*-\s*(.+)", line.strip())
            if match:
                tool_name = match.group(1).strip()
                description = match.group(2).strip()
                plan.append({
                    "tool": tool_name,
                    "description": description,
                })
        
        if plan:
            return ("tool", plan)
        
        return ("chitchat", [])
