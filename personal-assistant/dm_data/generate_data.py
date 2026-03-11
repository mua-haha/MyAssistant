"""
生成测试数据
"""
import sqlite3
import os
import random
from datetime import datetime, timedelta
from init_db import DB_PATH, INDICATORS


def get_month_range(start_year: int, start_month: int, end_year: int, end_month: int):
    """生成月份范围"""
    months = []
    year, month = start_year, start_month
    while (year < end_year) or (year == end_year and month <= end_month):
        months.append(f"{year}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def generate_data(start_year: int = 2023, start_month: int = 1, 
                  end_year: int = 2026, end_month: int = 3,
                  seed: int = None):
    """生成测试数据
    
    Args:
        start_year: 起始年
        start_month: 起始月
        end_year: 结束年
        end_month: 结束月
        seed: 随机种子，用于复现
    """
    if seed is not None:
        random.seed(seed)
    
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        print("请先运行 init_db.py 初始化数据库")
        return
    
    # 获取月份范围
    months = get_month_range(start_year, start_month, end_year, end_month)
    print(f"将生成 {len(months)} 个月的数据...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_records = 0
    for month in months:
        for category, indicators in INDICATORS.items():
            for indicator_name, min_val, max_val, unit in indicators:
                # 生成随机值，带小数
                value = round(random.uniform(min_val, max_val), 2)
                
                try:
                    cursor.execute("""
                        INSERT INTO dm_indicator_data (month, category, indicator_name, value)
                        VALUES (?, ?, ?, ?)
                    """, (month, category, indicator_name, value))
                    total_records += 1
                except sqlite3.IntegrityError:
                    print(f"警告: 数据已存在 {month} - {indicator_name}")
    
    conn.commit()
    conn.close()
    
    print(f"数据生成完成! 共 {total_records} 条记录")


def regenerate_data(start_year: int = 2023, start_month: int = 1,
                    end_year: int = 2026, end_month: int = 3,
                    seed: int = 42):
    """重新生成数据（清空后重新生成）"""
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        print("请先运行 init_db.py 初始化数据库")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 清空数据
    cursor.execute("DELETE FROM dm_indicator_data")
    conn.commit()
    conn.close()
    
    print("已清空现有数据")
    
    # 重新生成
    generate_data(start_year, start_month, end_year, end_month, seed)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成测试数据")
    parser.add_argument("--start", "-s", default="2023-01", help="起始月份，格式: YYYY-MM")
    parser.add_argument("--end", "-e", default="2026-03", help="结束月份，格式: YYYY-MM")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--regenerate", "-r", action="store_true", help="清空后重新生成")
    
    args = parser.parse_args()
    
    start_parts = args.start.split("-")
    end_parts = args.end.split("-")
    
    start_year, start_month = int(start_parts[0]), int(start_parts[1])
    end_year, end_month = int(end_parts[0]), int(end_parts[1])
    
    if args.regenerate:
        regenerate_data(start_year, start_month, end_year, end_month, args.seed)
    else:
        generate_data(start_year, start_month, end_year, end_month, args.seed)
