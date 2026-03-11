"""
查询数据示例
"""
import sqlite3
import os
from init_db import DB_PATH


def query_by_month(month: str):
    """按月份查询"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT month, category, indicator_name, value
        FROM dm_indicator_data
        WHERE month = ?
        ORDER BY category, indicator_name
    """, (month,))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print(f"没有找到 {month} 的数据")
        return
    
    print(f"\n{'='*60}")
    print(f"月份: {month}")
    print(f"{'='*60}")
    
    current_category = None
    for month, category, indicator_name, value in results:
        if category != current_category:
            print(f"\n【{category}】")
            current_category = category
        
        # 获取单位
        unit = ""
        for cat, inds in get_indicators().items():
            for name, _, _, u in inds:
                if name == indicator_name:
                    unit = u
                    break
        
        print(f"  {indicator_name}: {value} {unit}")


def query_by_category(category: str):
    """按分类查询"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT month, indicator_name, value
        FROM dm_indicator_data
        WHERE category = ?
        ORDER BY month, indicator_name
    """, (category,))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print(f"没有找到分类 '{category}' 的数据")
        return
    
    print(f"\n{'='*60}")
    print(f"分类: {category}")
    print(f"{'='*60}")
    
    current_month = None
    for month, indicator_name, value in results:
        if month != current_month:
            print(f"\n{month}")
            current_month = month
        
        print(f"  {indicator_name}: {value}")


def query_by_indicator(indicator_name: str):
    """按指标查询"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT month, category, value
        FROM dm_indicator_data
        WHERE indicator_name LIKE ?
        ORDER BY month
    """, (f"%{indicator_name}%",))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print(f"没有找到指标 '{indicator_name}' 的数据")
        return
    
    print(f"\n{'='*60}")
    print(f"指标: {indicator_name}")
    print(f"{'='*60}")
    
    for month, category, value in results:
        print(f"  {month} [{category}]: {value}")


def query_all_categories():
    """查询所有分类"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT category FROM dm_indicator_data ORDER BY category")
    results = cursor.fetchall()
    conn.close()
    
    print("\n所有指标分类:")
    for (category,) in results:
        print(f"  - {category}")


def query_all_indicators():
    """查询所有指标"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT indicator_name, category FROM dm_indicator_data ORDER BY category, indicator_name")
    results = cursor.fetchall()
    conn.close()
    
    print("\n所有指标:")
    current_category = None
    for indicator_name, category in results:
        if category != current_category:
            print(f"\n【{category}】")
            current_category = category
        print(f"  - {indicator_name}")


def query_stats():
    """查询统计信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 总记录数
    cursor.execute("SELECT COUNT(*) FROM dm_indicator_data")
    total = cursor.fetchone()[0]
    
    # 月份数
    cursor.execute("SELECT COUNT(DISTINCT month) FROM dm_indicator_data")
    months = cursor.fetchone()[0]
    
    # 分类数
    cursor.execute("SELECT COUNT(DISTINCT category) FROM dm_indicator_data")
    categories = cursor.fetchone()[0]
    
    # 指标数
    cursor.execute("SELECT COUNT(DISTINCT indicator_name) FROM dm_indicator_data")
    indicators = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"""
数据库统计:
  总记录数: {total}
  月份数: {months}
  分类数: {categories}
  指标数: {indicators}
""")


def get_indicators():
    """获取指标定义"""
    return {
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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="查询数据")
    parser.add_argument("--month", "-m", help="按月份查询，如 2026-03")
    parser.add_argument("--category", "-c", help="按分类查询，如 财务指标")
    parser.add_argument("--indicator", "-i", help="按指标查询，如 年度产值")
    parser.add_argument("--list-categories", "-lc", action="store_true", help="列出所有分类")
    parser.add_argument("--list-indicators", "-li", action="store_true", help="列出所有指标")
    parser.add_argument("--stats", "-s", action="store_true", help="统计信息")
    
    args = parser.parse_args()
    
    if args.month:
        query_by_month(args.month)
    elif args.category:
        query_by_category(args.category)
    elif args.indicator:
        query_by_indicator(args.indicator)
    elif args.list_categories:
        query_all_categories()
    elif args.list_indicators:
        query_all_indicators()
    elif args.stats:
        query_stats()
    else:
        query_stats()
