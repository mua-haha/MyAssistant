# 个人助手 CLI 开发规划

## 一、项目概述

- **项目名称**: personal-assistant
- **项目类型**: Python CLI 工具
- **核心功能**: 用户输入自然语言，通过大模型识别意图并调用tool执行操作
- **目标用户**: 个人用户，需要自动化桌面操作

## 二、技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 语言 | Python 3.10+ |  |
| LLM API | SiliconFlow | Qwen/Qwen2.5-7B-Instruct |
| 日志 | logging | 自定义 Formatter 实现 slf4j 风格 |
| 配置 | yaml | config.yaml |
| HTTP请求 | requests | 调用 SiliconFlow API |

## 三、系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      CLI Layer                          │
│                    (main.py / cli.py)                   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   Service Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ IntentService│  │ToolExecService│ │ResponseService│   │
│  │ (意图识别)    │  │ (执行tool)    │  │ (生成回复)    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    Model Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   LLMClient  │  │    Tool      │  │    Config    │   │
│  │ (API调用)     │  │  (tool定义)   │  │   (配置)      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 四、目录结构

```
personal-assistant/
├── config.yaml              # 配置文件
├── main.py                  # 入口文件
├── requirements.txt         # 依赖
├── src/
│   ├── __init__.py
│   ├── cli.py               # CLI 交互层
│   ├── config/
│   │   ├── __init__.py
│   │   └── loader.py        # 配置加载
│   ├── model/
│   │   ├── __init__.py
│   │   └── llm_client.py    # LLM API 调用
│   ├── service/
│   │   ├── __init__.py
│   │   ├── intent_service.py    # 意图识别 (LLM1)
│   │   ├── param_service.py     # 参数生成 (LLM2)
│   │   ├── response_service.py  # 回复生成 (LLM3)
│   │   └── tool_executor.py     # Tool 执行器
│   ├── tools/
│   │   ├── __init__.py
│   │   └── open_app.py      # 打开应用 Tool
│   └── logging/
│       ├── __init__.py
│       └── setup.py         # 日志配置
└── logs/                    # 日志目录
```

## 五、模块设计

### 1. 配置模块 (config)

**config.yaml**:
```yaml
llm:
  provider: siliconflow
  # API Key 从环境变量 SILICONFLOW_API_KEY 获取，也可配置在此
  api_key: ""
  base_url: "https://api.siliconflow.cn/v1"
  model: "Qwen/Qwen2.5-7B-Instruct"
  temperature: 0.7
  max_tokens: 2000

tools:
  open_app:
    enabled: true
    description: "打开本地应用程序或网页"

logging:
  level: INFO
  file: logs/assistant.log
```

**loader.py**:
- 加载 YAML 配置
- 优先从环境变量读取 API Key
- 提供配置访问接口
- 支持默认值

### 2. 日志模块 (logging)

**slf4j 风格格式**:
```
2026-03-11 21:00:00 [main] INFO  IntentService   - 开始意图识别，用户输入: "打开浏览器"
2026-03-11 21:00:00 [main] INFO  IntentService   - 选中工具: open_app
2026-03-11 21:00:01 [main] INFO  ParamService    - 开始生成参数
2026-03-11 21:00:01 [main] INFO  ParamService    - 生成的参数: {"app_name": "chrome"}
2026-03-11 21:00:01 [main] INFO  ToolExecutor    - 开始执行工具: open_app
2026-03-11 21:00:02 [main] INFO  ToolExecutor    - 工具执行成功
2026-03-11 21:00:02 [main] INFO  ResponseService - 开始生成回复
2026-03-11 21:00:02 [main] INFO  ResponseService - 最终回复: "已为您打开浏览器"
```

**实现要点**:
- 自定义 Formatter
- 同时输出到控制台和文件
- 记录每个流程步骤

### 3. LLM 模型层 (model)

**llm_client.py**:
- 封装 SiliconFlow API 调用
- 支持 chat/completion
- 处理错误和重试

### 4. Tool 定义 (tools)

**open_app.py**:
- 支持打开应用: chrome, edge
- 支持打开网页: 直接用浏览器打开指定URL

### 5. Service 层

| 服务 | 职责 | LLM调用 |
|------|------|---------|
| IntentService | 意图识别，选择用哪个tool | LLM1 |
| ParamService | 生成tool参数 | LLM2 |
| ResponseService | 生成自然语言回复 | LLM3 |
| ToolExecutor | 执行tool | - |

**意图识别 Prompt (LLM1)**:
```
你是一个意图识别助手。
用户输入: {user_input}
可选工具: {tool_list}
请从工具列表中选择最合适的一个，只输出工具名称，不要输出其他内容。

输出格式:
tool: 工具名称
```

**参数生成 Prompt (LLM2)**:
```
你是一个参数生成助手。
用户输入: {user_input}
工具名称: {tool_name}
工具描述: {tool_description}
工具参数Schema: {params_schema}

请根据用户输入生成参数JSON。

输出格式:
params: {"参数名": "参数值"}
```

**回复生成 Prompt (LLM3)**:
```
你是一个回复生成助手。
用户原始输入: {user_input}
工具执行结果: {tool_result}

请用自然、友好的语言回复用户。

回复:
```

## 六、开发步骤

### Phase 1: 基础框架

1. 创建目录结构
2. 配置模块 - config.yaml + loader.py
3. 日志模块 - logging setup
4. LLM 客户端 - llm_client.py

### Phase 2: Tool 系统

1. 定义 Tool 基类/接口
2. 实现 OpenAppTool

### Phase 3: Service 层

1. IntentService (LLM1)
2. ParamService (LLM2)
3. ToolExecutor
4. ResponseService (LLM3)

### Phase 4: CLI 集成

1. main.py 入口
2. cli.py 交互循环
3. 整合测试
