"""
初始化数据库 - 创建表结构和指标定义
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "indicators.db")

# 指标定义：分类 -> [(指标名称, 最小值, 最大值, 单位)]
INDICATORS = {
    "研发创新指标": [
        ("研发投入强度", 3, 15, "%"),
        ("研发投入", 5000, 20000, "万元"),
        ("新产品营收占比", 20, 60, "%"),
    ],
    "市场业务指标": [
        ("国际业务新签", 1000, 5000, "万元"),
        ("国际业务收入", 3000, 8000, "万元"),
        ("国内业务新签", 2000, 10000, "万元"),
        ("国内业务收入", 5000, 15000, "万元"),
    ],
    "质量指标": [
        ("客户满意度", 80, 100, "%"),
        ("质量一次交检合格率", 90, 100, "%"),
        ("按期交付率", 85, 100, "%"),
    ],
    "运营效率指标": [
        ("应收账款周转率", 3, 12, "次"),
        ("存货周转率", 2, 8, "次"),
        ("全员劳动生产率", 20, 80, "万元/人"),
        ("年度产值", 10000, 50000, "万元"),
    ],
    "财务指标": [
        ("利润总额", 1000, 10000, "万元"),
        ("经营性现金流", -2000, 8000, "万元"),
        ("净资产收益率", 5, 25, "%"),
        ("外部营业收现率", 70, 110, "%"),
        ("资产负债率", 30, 70, "%"),
    ],
    "合同指标": [
        ("中标合同年度累计", 10000, 50000, "万元"),
        ("中标合同年度完成率", 60, 120, "%"),
        ("中标合同复合增长率", 5, 30, "%"),
        ("新增中标", 1000, 8000, "万元"),
    ],
}


def init_db():
    """初始化数据库，创建表"""
    if os.path.exists(DB_PATH):
        print(f"数据库已存在: {DB_PATH}")
        response = input("是否删除并重新创建? (y/n): ")
        if response.lower() != 'y':
            print("取消创建")
            return
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute("""
        CREATE TABLE dm_indicator_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            indicator_name TEXT NOT NULL,
            value REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(month, indicator_name)
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX idx_month ON dm_indicator_data(month)")
    cursor.execute("CREATE INDEX idx_category ON dm_indicator_data(category)")
    cursor.execute("CREATE INDEX idx_indicator_name ON dm_indicator_data(indicator_name)")
    
    conn.commit()
    conn.close()
    
    print(f"数据库初始化成功: {DB_PATH}")
    print(f"指标分类数: {len(INDICATORS)}")
    total_indicators = sum(len(v) for v in INDICATORS.values())
    print(f"指标总数: {total_indicators}")


if __name__ == "__main__":
    init_db()
