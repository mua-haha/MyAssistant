import sys
from typing import Dict, Any, List
from src.config.loader import get_config
from src.model.factory import LLMFactory
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
        console_config = log_config.get("console", {})
        setup_logging(
            log_level=log_config.get("level", "INFO"),
            log_file=log_config.get("file", "logs/assistant.log"),
            log_format=log_config.get("format", "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg"),
            console_enabled=console_config.get("enabled", True),
            console_level=console_config.get("level", "INFO"),
        )

        logger.info("初始化个人助手...")

        self.llm_config = self.config.get_llm_config()
        self.llm_client = LLMFactory.create(self.llm_config)
        self._available_models = LLMFactory.get_available_models(self.llm_config)

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
        logger.info(f"当前模型: {self.llm_client.provider_name}/{self.llm_client.model}")
        logger.info("个人助手初始化完成")

    def switch_model(self, provider: str, model: str) -> str:
        """
        切换 LLM 模型

        Args:
            provider: provider 名称
            model: 模型名称

        Returns:
            切换结果消息
        """
        if not self.config.set_llm_model(provider, model):
            available = self._available_models.get(provider, [])
            available_str = ", ".join(available) if available else "无可用模型"
            hint = f"\n提示: /model {provider}/{available[0]}" if available else ""
            return f"模型 '{model}' 不可用。可用模型: {available_str}{hint}"

        self.llm_client = LLMFactory.create(self.config.get_llm_config())
        self.intent_service.llm_client = self.llm_client
        self.param_service.llm_client = self.llm_client
        self.response_service.llm_client = self.llm_client

        logger.info(f"已切换模型: provider={provider}, model={model}")
        return f"已切换模型: {provider}/{model}"

    def _build_model_list(self) -> List[tuple]:
        """构建模型列表，返回 [(编号, provider, model), ...]"""
        model_list = []
        idx = 1
        for provider, models in self._available_models.items():
            for model in models:
                model_list.append((idx, provider, model))
                idx += 1
        return model_list

    def show_models(self) -> str:
        """显示当前模型和可选模型列表（带编号）"""
        lines = [f"当前模型: {self.llm_client.provider_name}/{self.llm_client.model}", ""]
        lines.append("可用模型:")
        model_list = self._build_model_list()
        for idx, provider, model in model_list:
            marker = " *" if provider == self.llm_client.provider_name and model == self.llm_client.model else ""
            lines.append(f"  {idx}. {provider}: {model}{marker}")
        lines.append("")
        lines.append("使用说明:")
        lines.append(f"  /model {model_list[0][0]}              # 输入编号切换")
        lines.append(f"  /model {self.llm_client.provider_name}/模型名   # provider/model 格式")
        lines.append(f"  /model 模型名                         # 当前 provider")
        return "\n".join(lines)

    def switch_model_by_index(self, index: int) -> str:
        """按编号切换模型"""
        model_list = self._build_model_list()
        if index < 1 or index > len(model_list):
            return f"无效编号 {index}，可选: 1-{len(model_list)}"
        _, provider, model = model_list[index - 1]
        return self.switch_model(provider, model)

    def run(self):
        """运行 CLI 交互循环"""
        current_model = f"{self.llm_client.provider_name}/{self.llm_client.model}"
        print("=" * 50)
        print(f"个人助手 CLI [当前模型: {current_model}]")
        print("输入自然语言描述你的需求")
        print("命令: /new 新会话, /model 切换模型, /help 帮助, /exit 退出")
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

                if user_input.lower() in ["/model", "/m"]:
                    print(f"\n{self.show_models()}\n")
                    continue

                if user_input.lower().startswith("/model ") or user_input.lower().startswith("/m "):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) == 2:
                        model_spec = parts[1].strip()
                        if model_spec.isdigit():
                            result = self.switch_model_by_index(int(model_spec))
                            print(f"\n{result}\n")
                        elif "/" in model_spec:
                            provider, model = model_spec.split("/", 1)
                            result = self.switch_model(provider.strip(), model.strip())
                            print(f"\n{result}\n")
                        else:
                            current_provider = self.llm_client.provider_name
                            result = self.switch_model(current_provider, model_spec)
                            print(f"\n{result}\n")
                    continue

                if user_input.lower() == "/help":
                    print("""
命令说明:
  /new   - 开始新会话，清空对话历史
  /model - 显示当前模型和可选模型列表
  /m     - /model 命令的简写
  /help  - 显示帮助信息
  /exit  - 退出程序

模型切换:
  /model              - 查看当前模型和可用模型
  /model 1            - 输入编号切换（如 /model 3）
  /model ollama/qwen3.5:9b  - 切换到指定模型 (provider/model)
  /model qwen3.5:9b        - 切换当前 provider 的模型

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
        处理用户输入（ReAct 模式）

        流程:
        1. 意图识别 + 生成行动计划
        2. 如果是闲聊，直接生成回复
        3. 如果是工具：显示计划 -> 用户确认 -> 执行循环

        Args:
            user_input: 用户输入

        Returns:
            助手回复
        """
        logger.info("=" * 60)
        logger.info(f"收到用户输入: {user_input}")
        logger.info("=" * 60)

        session_history = self.session.get_history_text()

        intent, plan = self.intent_service.generate_plan(user_input, session_history)

        if intent == "chitchat":
            logger.info("识别为闲聊，跳过工具执行，直接生成回复")
            response = self.response_service.generate(user_input, "用户只是想闲聊", session_history)
            return response

        if not plan:
            return "抱歉，我无法处理这个请求"

        plan_text = self._format_plan(plan)
        print(f"\n行动计划:")
        print(plan_text)
        
        confirm = input("\n确认执行以上计划? (y/n): ").strip().lower()
        if confirm != 'y' and confirm != '是':
            return "已取消执行"
        
        results = self._execute_plan(plan, user_input, session_history)
        
        response = self.response_service.generate(user_input, results, session_history)
        return response

    def _format_plan(self, plan: list) -> str:
        """格式化行动计划"""
        lines = []
        for i, step in enumerate(plan, 1):
            lines.append(f"  {i}. [ ] {step['tool']} - {step['description']}")
        return "\n".join(lines)

    def _execute_plan(self, plan: list, user_input: str, session_history: str) -> str:
        """执行行动计划"""
        results = []
        max_steps = 10
        
        for i, step in enumerate(plan, 1):
            if i > max_steps:
                results.append(f"步骤 {i}: 已达到最大步骤数（10），停止执行")
                break
            
            tool_name = step['tool']
            description = step['description']
            
            print(f"\n执行第{i}步: {tool_name}")
            print(f"描述: {description}")
            
            tool = self.tools.get(tool_name)
            if not tool:
                error_msg = f"工具 '{tool_name}' 不存在"
                print(f"错误: {error_msg}")
                handle_choice = self._ask_error_handling(i, error_msg)
                if handle_choice == 'stop':
                    results.append(f"步骤 {i}: 失败 - {error_msg}（已终止）")
                    break
                elif handle_choice == 'skip':
                    results.append(f"步骤 {i}: 跳过 - {error_msg}")
                    continue
                else:
                    new_params = self._ask_retry_params(tool_name)
                    if new_params:
                        try:
                            tool_result = self.tool_executor.execute(tool_name, new_params)
                            print(f"重试结果: {tool_result}")
                            results.append(f"步骤 {i}: 重试成功 - {tool_result}")
                        except Exception as e2:
                            results.append(f"步骤 {i}: 重试失败 - {str(e2)}")
                    continue
            
            try:
                params = self.param_service.generate_params(description, tool, session_history)
                tool_result = self.tool_executor.execute(tool_name, params)
                print(f"结果: {tool_result}")
                results.append(f"步骤 {i}: 成功 - {tool_result}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"错误: {error_msg}")
                handle_choice = self._ask_error_handling(i, error_msg)
                
                if handle_choice == 'stop':
                    results.append(f"步骤 {i}: 失败 - {error_msg}（已终止）")
                    break
                elif handle_choice == 'skip':
                    results.append(f"步骤 {i}: 跳过 - {error_msg}")
                    continue
                else:
                    new_params = self._ask_retry_params(tool_name)
                    if new_params:
                        try:
                            tool_result = self.tool_executor.execute(tool_name, new_params)
                            print(f"重试结果: {tool_result}")
                            results.append(f"步骤 {i}: 重试成功 - {tool_result}")
                        except Exception as e2:
                            results.append(f"步骤 {i}: 重试失败 - {str(e2)}")
                    else:
                        results.append(f"步骤 {i}: 失败 - {error_msg}（用户取消重试）")
        
        return "\n".join(results)

    def _ask_error_handling(self, step_num: int, error_msg: str) -> str:
        """询问用户如何处理错误"""
        print(f"\n步骤 {step_num} 执行失败")
        print(f"错误: {error_msg}")
        print("\n如何处理?")
        print("  [1] 重试 - 请输入修改方案或参数")
        print("  [2] 跳过 - 忽略此步骤，继续下一步")
        print("  [3] 终止 - 停止整个计划")
        
        while True:
            choice = input("请选择 (1/2/3): ").strip()
            if choice == '1':
                return 'retry'
            elif choice == '2':
                return 'skip'
            elif choice == '3':
                return 'stop'
            print("无效选择，请输入 1、2 或 3")

    def _ask_retry_params(self, tool_name: str) -> dict:
        """询问用户输入重试参数"""
        import json
        params_str = input("请输入参数（JSON格式，回车跳过使用默认参数）: ").strip()
        if not params_str:
            return {}
        try:
            return json.loads(params_str)
        except json.JSONDecodeError:
            print("JSON格式错误，将使用默认参数")
            return {}
