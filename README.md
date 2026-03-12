# Personal Assistant CLI

一个基于大模型的个人助手 CLI 工具，采用 ReAct 架构，通过自然语言调用工具执行操作。

## 功能特性

- **ReAct 模式** - 智能规划+执行循环，支持复杂任务处理
- **多模型支持** - 支持 SiliconFlow API 和本地 Ollama，一键切换
- **意图识别** - 自动判断用户意图，选择合适的工具
- **参数生成** - 根据用户输入和工具上下文生成参数
- **回复生成** - 将工具执行结果转换为自然语言
- **会话管理** - 支持上下文记忆，跨轮对话
- **可扩展工具系统** - 轻松添加新工具

**内置工具**：

| 工具 | 功能 |
|------|------|
| open_app | 打开应用程序（Chrome、Edge）或网页 |
| file_manager | 文件管理（查看、读取、创建/编辑） |
| db_query | 数据库查询（指标数据查询） |

## 技术架构

```
用户输入 → 意图识别 + 生成行动计划 → 用户确认 → 执行循环 → 返回结果
         ↓
    闲聊 → 直接回复
    工具 → 执行计划（失败可重试/跳过/终止）
```

## 目录结构

```
personal-assistant/
├── config.yaml           # 配置文件
├── prompts.yaml         # 提示词配置
├── main.py              # 入口文件
├── requirements.txt     # 依赖
├── dm_data/            # 数据库脚本
│   └── indicators.db    # SQLite 数据库
├── src/
│   ├── cli.py              # CLI 交互层
│   ├── session.py          # 会话管理
│   ├── config/loader.py    # 配置加载
│   ├── model/
│   │   ├── base.py         # LLM 客户端基类
│   │   ├── factory.py      # LLM 客户端工厂
│   │   ├── siliconflow.py # SiliconFlow 实现
│   │   └── ollama.py      # Ollama 实现
│   ├── service/
│   │   ├── intent_service.py    # 意图识别 + 计划生成
│   │   ├── param_service.py    # 参数生成
│   │   ├── response_service.py # 回复生成
│   │   └── tool_executor.py   # 工具执行器
│   ├── tools/
│   │   ├── open_app.py         # 打开应用工具
│   │   ├── file_manager.py     # 文件管理工具
│   │   └── db_query.py         # 数据库查询工具
│   └── logging/setup.py        # 日志配置
├── workspace/            # 文件管理根目录
└── logs/                # 日志目录
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`：

```yaml
llm:
  # 当前使用的 provider 和模型
  provider: "ollama"
  model: "qwen2.5:7b"
  
  # 可用的 providers 配置
  providers:
    siliconflow:
      enabled: true
      base_url: "https://api.siliconflow.cn/v1"
      api_key: "${SILICONFLOW_API_KEY}"  # 或直接填写 API Key
      models:
        - "Qwen/Qwen2.5-7B-Instruct"
        - "deepseek-ai/DeepSeek-V3"
    
    ollama:
      enabled: true
      base_url: "http://localhost:11434"
      api_key: ""
      models:
        - "qwen2.5:7b"
        - "deepseek-r1:14b"
```

设置环境变量（可选）：
```bash
# Windows
set SILICONFLOW_API_KEY=your-api-key

# Linux/Mac
export SILICONFLOW_API_KEY=your-api-key
```

### 3. 运行

```bash
python main.py
```

## 使用示例

### 模型切换

```
/model              # 查看当前模型和可用模型
/model 1            # 输入编号切换
/model ollama/qwen2.5:7b  # 切换到指定模型
```

### 打开应用/网页

```
请输入: 打开chrome
助手: 已为您打开 Chrome 浏览器

请输入: 打开百度
助手: 已为您打开 https://www.baidu.com
```

### 文件管理

```
请输入: 查看workspace目录
助手: 目录: workspace
  - test.txt

请输入: 新建文件test.txt内容是hello world
助手: 文件写入成功: test.txt

请输入: 读取test.txt
助手: 文件: test.txt
内容: hello world
```

### 数据库查询

```
请输入: 查询2026年3月的新增中标
助手: +----------+-----------------+---------+
| month   | indicator_name | value   |
+----------+-----------------+---------+
| 2026-03 | 新增中标       | 4382.46 |
+----------+-----------------+---------+
```

### 闲聊

```
请输入: 你好
助手: 你好！有什么我可以帮你的吗？
```

### 命令列表

```
/new   - 开始新会话，清空对话历史
/model - 切换模型
/help  - 显示帮助信息
/exit  - 退出程序
```

## 配置说明

### 日志配置

```yaml
logging:
  level: DEBUG           # 文件日志级别
  file: logs/assistant.log
  format: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg"
  console:
    enabled: true        # 是否显示到控制台
    level: INFO          # 控制台显示级别
```

### 工具配置

```yaml
tools:
  open_app:
    enabled: true
    supported_apps:
      - chrome
      - edge

  file_manager:
    enabled: true
    root_dir: "workspace"
    max_file_size: 5242880  # 5MB

  db_query:
    enabled: true
    db_path: "dm_data/indicators.db"
```

## ReAct 模式

当用户输入需要多个步骤完成的任务时，系统会：

1. **生成行动计划** - 分析需求，列出执行步骤
2. **用户确认** - 显示计划，用户确认后执行
3. **循环执行** - 按顺序执行每个步骤
4. **错误处理** - 失败时询问用户：
   - 重试（输入修改方案）
   - 跳过当前步骤
   - 终止整个计划

示例：
```
请输入: 帮我查下天气然后打开百度

行动计划:
  1. [ ] web_search - 查询天气
  2. [ ] open_app - 打开百度网站

确认执行以上计划? (y/n): y

执行第1步: web_search
结果: 北京今天天气：晴，25°C
执行第2步: open_app
结果: 已打开百度

助手: 根据查询结果，今天北京天气晴朗，温度25°C，已为您打开百度网站。
```

## 添加新工具

1. 在 `src/tools/` 目录下创建新的 Tool 类
2. 继承 `Tool` 基类
3. 实现 `name`、`description`、`params_schema`、`execute` 属性/方法
4. 在 `src/cli.py` 中注册工具

## 环境要求

- Python 3.10+
- Ollama（可选，用于本地模型）
- SiliconFlow API Key（可选，用于云端模型）
