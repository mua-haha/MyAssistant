# Personal Assistant CLI

一个基于大模型的个人助手 CLI 工具，通过自然语言调用工具执行操作。

## 功能特性

- 意图识别（LLM1）- 判断用户意图，选择合适的工具
- 参数生成（LLM2）- 根据用户输入和工具上下文生成参数
- 回复生成（LLM3）- 将工具执行结果转换为自然语言
- 会话管理 - 支持上下文记忆，跨轮对话
- 工具系统 - 可扩展的工具架构

**内置工具**：

| 工具 | 功能 |
|------|------|
| open_app | 打开应用程序（Chrome、Edge）或网页 |
| file_manager | 文件管理（查看、读取、创建/编辑） |
| db_query | 数据库查询（指标数据查询） |

## 技术架构

```
用户输入 → 意图识别(LLM1) → 参数生成(LLM2) → 执行工具 → 回复生成(LLM3) → 用户
```

## 目录结构

```
personal-assistant/
├── config.yaml           # 配置文件
├── prompts.yaml         # 提示词配置
├── main.py              # 入口文件
├── requirements.txt     # 依赖
├── dm_data/            # 数据库脚本
│   ├── init_db.py          # 初始化数据库
│   ├── generate_data.py    # 生成测试数据
│   ├── query_data.py       # 查询数据
│   └── indicators.db        # SQLite 数据库
├── src/
│   ├── cli.py              # CLI 交互层
│   ├── session.py          # 会话管理
│   ├── config/loader.py    # 配置加载
│   ├── model/llm_client.py # LLM API 调用
│   ├── service/
│   │   ├── intent_service.py     # 意图识别 (LLM1)
│   │   ├── param_service.py      # 参数生成 (LLM2)
│   │   ├── response_service.py   # 回复生成 (LLM3)
│   │   └── tool_executor.py      # 工具执行器
│   ├── tools/
│   │   ├── open_app.py           # 打开应用工具
│   │   ├── file_manager.py       # 文件管理工具
│   │   └── db_query.py           # 数据库查询工具
│   └── logging/setup.py          # 日志配置
├── workspace/            # 文件管理根目录
└── logs/               # 日志目录
```

## 快速开始

### 1. 安装依赖

```bash
cd personal-assistant
pip install -r requirements.txt
```

### 2. 配置 API Key

设置环境变量（推荐）：
```bash
# Windows
set SILICONFLOW_API_KEY=your-api-key

# Linux/Mac
export SILICONFLOW_API_KEY=your-api-key
```

或者编辑 `config.yaml`：
```yaml
llm:
  api_key: "your-api-key"
```

### 3. 运行

```bash
python main.py
```

## 使用示例

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
----------------------------------------
  [DIR]  test.txt/

请输入: 新建文件test.txt内容是hello world
助手: 文件写入成功: test.txt

请输入: 读取test.txt
助手: 文件: test.txt
大小: 11 bytes
----------------------------------------
hello world
```

### 数据库查询

```
请输入: 查询2026年3月的新增中标
助手: +----------+-----------------+---------+
| month   | indicator_name | value   |
+----------+-----------------+---------+
| 2026-03 | 新增中标       | 4382.46 |
+----------+-----------------+---------+

请输入: 2026年新增中标的明细
助手: +----------+-----------------+---------+
| month   | indicator_name | value   |
+----------+-----------------+---------+
| 2026-01 | 新增中标       | 2156.78 |
| 2026-02 | 新增中标       | 3892.34 |
| 2026-03 | 新增中标       | 4382.46 |
+----------+-----------------+---------+

请输入: 2026年新增中标总共多少
助手: +-------+
| total  |
+-------+
| 10431 |
+-------+
```

### 闲聊

```
请输入: 你好
助手: 你好！有什么我可以帮你的吗？

请输入: 讲个笑话
助手: 好的，那我来给你讲个笑话吧...
```

### 会话命令

```
/new   - 开始新会话，清空对话历史
/help  - 显示帮助信息
/exit  - 退出程序
```

## 配置说明

### LLM 配置

```yaml
llm:
  provider: siliconflow
  base_url: "https://api.siliconflow.cn/v1"
  model: "Qwen/Qwen2.5-7B-Instruct"
  temperature: 0.7
  max_tokens: 2000
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

## 添加新工具

1. 在 `src/tools/` 目录下创建新的 Tool 类
2. 继承 `Tool` 基类
3. 实现 `name`、`description`、`params_schema`、`prompt_hint` 和 `execute` 属性/方法
4. 在 `src/cli.py` 中注册工具

## 日志

日志同时输出到控制台和文件 `logs/assistant.log`，格式如下：

```
2026-03-11 21:00:00 [MainThread] INFO  IntentService   - 开始意图识别，用户输入: "打开浏览器"
2026-03-11 21:00:00 [MainThread] INFO  IntentService   - 识别结果: intent=tool, tool=open_app
2026-03-11 21:00:01 [MainThread] INFO  ParamService    - 生成的参数: {"action": "open_app", "app_name": "chrome"}
2026-03-11 21:00:01 [MainThread] INFO  ToolExecutor    - 开始执行工具: open_app
2026-03-11 21:00:02 [MainThread] INFO  ToolExecutor    - 工具执行成功
2026-03-11 21:00:02 [MainThread] INFO  ResponseService - 最终回复: 已为您打开 Chrome 浏览器
```

## 环境要求

- Python 3.10+
- SiliconFlow API Key
