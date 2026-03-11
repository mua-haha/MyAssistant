import sys
from typing import Dict, Any
from src.config.loader import get_config
from src.model.llm_client import LLMClient
from src.service.intent_service import IntentService
from src.service.param_service import ParamService
from src.service.tool_executor import ToolExecutor
from src.service.response_service import ResponseService
from src.tools.open_app import OpenAppTool
from src.tools.file_manager import FileManagerTool
from src.tools.db_query import DBQueryTool
from src.session import Session
from src.logging.setup import get_logger, setup_logging

logger = get_logger("CLI")


class Assistant:
    """个人助手主类"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = get_config(config_path)
        
        log_config = self.config.get_logging_config()
        setup_logging(
            log_level=log_config.get("level", "INFO"),
            log_file=log_config.get("file", "logs/assistant.log"),
            log_format=log_config.get("format", "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg"),
        )

        logger.info("初始化个人助手...")

        self.llm_config = self.config.get_llm_config()
        self.llm_client = LLMClient(self.llm_config)

        tools_config = self.config.get_tools_config()
        supported_apps = tools_config.get("open_app", {}).get("supported_apps", ["chrome", "edge"])

        self.tools: Dict[str, Any] = {}
        if tools_config.get("open_app", {}).get("enabled", True):
            self.tools["open_app"] = OpenAppTool(supported_apps=supported_apps)

        if tools_config.get("file_manager", {}).get("enabled", True):
            root_dir = tools_config.get("file_manager", {}).get("root_dir", "workspace")
            max_size = tools_config.get("file_manager", {}).get("max_file_size", 5242880)
            self.tools["file_manager"] = FileManagerTool(root_dir=root_dir, max_file_size=max_size)

        if tools_config.get("db_query", {}).get("enabled", True):
            db_path = tools_config.get("db_query", {}).get("db_path", "dm_data/indicators.db")
            self.tools["db_query"] = DBQueryTool(db_path=db_path)

        prompts = self.config.get_prompts()
        
        self.intent_service = IntentService(self.llm_client, list(self.tools.values()), prompts.get("intent", {}))
        self.param_service = ParamService(self.llm_client, prompts.get("param", {}))
        self.tool_executor = ToolExecutor(self.tools)
        self.response_service = ResponseService(self.llm_client, prompts.get("response", {}))

        self.session = Session()

        logger.info(f"已加载工具: {list(self.tools.keys())}")
        logger.info("个人助手初始化完成")

    def run(self):
        """运行 CLI 交互循环"""
        print("=" * 50)
        print("个人助手 CLI")
        print("输入自然语言描述你的需求")
        print("命令: /new 新会话, /help 帮助, /exit 退出")
        print("=" * 50)
        print()

        while True:
            try:
                user_input = input("请输入: ").strip()
                if not user_input:
                    continue

                if user_input.lower() in ["/exit", "/quit", "exit", "quit", "q"]:
                    print("再见!")
                    break

                if user_input.lower() == "/new":
                    self.session.clear()
                    print("已开启新会话\n")
                    continue

                if user_input.lower() == "/help":
                    print("""
命令说明:
  /new   - 开始新会话，清空对话历史
  /help  - 显示帮助信息
  /exit  - 退出程序

示例:
  "打开chrome"          - 打开 Chrome 浏览器
  "再打开一次"          - 基于历史记录再次执行
  "打开百度"            - 用默认浏览器打开网页
                    """)
                    continue

                response = self.process(user_input)
                self.session.add(user_input, response)
                print(f"\n助手: {response}\n")

            except KeyboardInterrupt:
                print("\n\n再见!")
                break
            except Exception as e:
                logger.error(f"处理请求时发生错误: {e}", exc_info=True)
                print(f"\n错误: {str(e)}\n")

    def process(self, user_input: str) -> str:
        """
        处理用户输入

        流程:
        1. 意图识别 (LLM1) - 判断是闲聊还是执行工具
        2. 如果是闲聊，直接生成回复 (LLM3)
        3. 如果是工具：参数生成 (LLM2) -> 执行 Tool -> 回复生成 (LLM3)

        Args:
            user_input: 用户输入

        Returns:
            助手回复
        """
        logger.info("=" * 60)
        logger.info(f"收到用户输入: {user_input}")
        logger.info("=" * 60)

        session_history = self.session.get_history_text()

        intent, tool_name = self.intent_service.recognize(user_input, session_history)

        if intent == "chitchat":
            logger.info("识别为闲聊，跳过工具执行，直接生成回复")
            response = self.response_service.generate(user_input, "用户只是想闲聊", session_history)
            return response

        tool = self.tools.get(tool_name)
        if not tool:
            return f"抱歉，我无法处理这个请求"

        params = self.param_service.generate_params(user_input, tool, session_history)

        tool_result = self.tool_executor.execute(tool_name, params)

        response = self.response_service.generate(user_input, tool_result, session_history)

        return response
