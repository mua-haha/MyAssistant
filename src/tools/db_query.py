import sqlite3
import os
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.logging.setup import get_logger

logger = get_logger("DBQueryTool")


class Tool(ABC):
    """Tool 基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool 名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool 描述"""
        pass

    @property
    @abstractmethod
    def params_schema(self) -> Dict[str, Any]:
        """参数 Schema"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """执行 Tool"""
        pass


class DBQueryTool(Tool):
    """数据库查询工具"""

    def __init__(self, db_path: str = "dm_data/indicators.db"):
        self.db_path = db_path

    @property
    def name(self) -> str:
        return "db_query"

    @property
    def description(self) -> str:
        return "查询指标数据库，可以查询各种指标数据"

    @property
    def params_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "要执行的 SQL 查询语句，只支持 SELECT 查询",
                },
            },
            "required": ["sql"],
        }

    @property
    def prompt_hint(self) -> str:
        return """【重要】db_query 工具参数规则：

数据库类型：SQLite
表名：dm_indicator_data
日期格式：YYYY-MM（如 2026-03）
列名：id, month(月份), category(分类), indicator_name(指标名称), value(指标值), created_at

【示例数据】
| month    | category   | indicator_name | value   |
|----------|------------|---------------|---------|
| 2026-03  | 合同指标   | 新增中标      | 4382.46 |
| 2026-03  | 财务指标   | 利润总额      | 8560.12 |
| 2026-03  | 研发创新指标 | 研发投入    | 14295.66 |

【关键词解读】
- "明细"：列出所有相关数据，不做汇总，使用 SELECT *
- "汇总/总计/一共/总共"：使用 SUM() 聚合函数
- "查一年/2026年"：使用 month LIKE '2026%'
- "查某月/3月份"：使用 month='2026-03'
- "最近几个月"：使用 ORDER BY month DESC LIMIT N

【SQL限制】
- 只允许 SELECT 查询

【常用SQL模式】
- 查单月数据: SELECT * FROM dm_indicator_data WHERE month='2026-03' AND indicator_name='新增中标'
- 查年度明细: SELECT * FROM dm_indicator_data WHERE month LIKE '2026%' AND indicator_name='新增中标' ORDER BY month
- 查年度汇总: SELECT SUM(value) as total FROM dm_indicator_data WHERE month LIKE '2026%' AND indicator_name='新增中标'
- 查分类数据: SELECT * FROM dm_indicator_data WHERE category='财务指标'
- 排序 LIMIT: SELECT * FROM dm_indicator_data WHERE indicator_name='年度产值' ORDER BY month DESC LIMIT 3
"""

    def _validate_sql(self, sql: str) -> str:
        """验证 SQL 安全性
        
        Returns:
            清理后的 SQL
            
        Raises:
            ValueError: SQL 不安全
        """
        sql = sql.strip()
        sql_upper = sql.upper()
        
        # 检查是否包含危险关键词
        dangerous_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
            "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE",
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError(f"SQL 包含危险关键词 '{keyword}'，只允许 SELECT 查询")
        
        # 必须以 SELECT 开头
        if not sql_upper.startswith("SELECT"):
            raise ValueError("只支持 SELECT 查询语句")
        
        # 只允许查询 dm_indicator_data 表
        if "dm_indicator_data" not in sql and "DM_INDICATOR_DATA" not in sql_upper:
            raise ValueError("只允许查询 dm_indicator_data 表")
        
        return sql

    def _execute_query(self, sql: str) -> str:
        """执行查询并返回表格形式的结果"""
        if not os.path.exists(self.db_path):
            return f"数据库不存在: {self.db_path}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 限制返回条数
            if "LIMIT" not in sql.upper():
                sql = sql.rstrip().rstrip(";") + " LIMIT 1000"
            
            cursor.execute(sql)
            results = cursor.fetchall()
            
            # 获取列名
            column_names = [description[0] for description in cursor.description]
            
            conn.close()
            
            if not results:
                return "查询结果为空"
            
            return self._format_table(column_names, results)
            
        except sqlite3.Error as e:
            conn.close()
            return f"SQL 执行错误: {str(e)}"

    def _format_table(self, columns: List[str], rows: List[tuple]) -> str:
        """格式化表格输出"""
        # 计算每列宽度
        col_widths = [len(col) for col in columns]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))
        
        # 格式化字符串
        separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
        header = "|" + "|".join([f" {col:<{col_widths[i]}} " for i, col in enumerate(columns)]) + "|"
        
        lines = [separator, header, separator]
        for row in rows:
            row_line = "|" + "|".join([f" {str(val):<{col_widths[i]}} " for i, val in enumerate(row)]) + "|"
            lines.append(row_line)
        lines.append(separator)
        
        return "\n".join(lines)

    def execute(self, **kwargs) -> str:
        """执行数据库查询"""
        sql = kwargs.get("sql", "").strip()
        
        if not sql:
            return "错误：未提供 SQL 查询语句"
        
        try:
            sql = self._validate_sql(sql)
            logger.info(f"执行查询 SQL: {sql}")
            return self._execute_query(sql)
        except ValueError as e:
            return f"错误: {str(e)}"
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return f"查询失败: {str(e)}"
