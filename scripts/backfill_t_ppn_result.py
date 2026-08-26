#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回填 t_ppn_result 宽表数据(最终版本,字段为 varchar)

从各源表聚合 PPN 相关的指标数据:
#	名字	类型	排序规则	属性	空	默认	注释	额外
1	id  主键	bigint			否	无		AUTO_INCREMENT
2	ppn  索引	varchar(100)	utf8mb4_general_ci		否	无		
3	manu_name  索引	varchar(100)	utf8mb4_general_ci		是	NULL		
4	digikey_status	varchar(50)	utf8mb4_general_ci		是	NULL		
5	hq_m_avg  索引	varchar(20)	utf8mb4_general_ci		是	NULL		
6	hq_sup_count  索引	varchar(13)	utf8mb4_general_ci		是	NULL		
7	hq_stock	varchar(13)	utf8mb4_general_ci		否	无	华强网库存	
8	ic_sup_count	varchar(13)	utf8mb4_general_ci		是	NULL		
9	ic_stock	varchar(13)	utf8mb4_general_ci		否	无	IC交易网库存	
10	efind_all_sup	varchar(13)	utf8mb4_general_ci		是			
11	wheat_global	varchar(13)	utf8mb4_general_ci		是	NULL		
12	wheat_ru	varchar(13)	utf8mb4_general_ci		是	NULL		
13	oc_price	varchar(20)	utf8mb4_general_ci		是	NULL		
14	oc_stock	varchar(13)	utf8mb4_general_ci		是			
15	task_name  索引	varchar(100)	utf8mb4_general_ci		是	NULL		
16	update_time	datetime			是	CURRENT_TIMESTAMP		DEFAULT_GENERATED

注意:目标表所有数值字段都是 varchar,插入时统一转 str()
"""

import ast
import json
import re
import sys
import os

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

app = create_app()


def parse_month_hot(month_hot_str):
    """解析 month_hot 数组字符串,返回所有数值的平均值"""
    if not month_hot_str or not str(month_hot_str).strip():
        return 0

    all_values = []
    try:
        arr = ast.literal_eval(month_hot_str)
        if isinstance(arr, (list, tuple)):
            for v in arr:
                try:
                    all_values.append(int(v))
                except (ValueError, TypeError):
                    pass
    except (ValueError, SyntaxError):
        # 尝试 JSON 解析
        try:
            cleaned = month_hot_str.replace("'", '"')
            arr = json.loads(cleaned)
            if isinstance(arr, list):
                for v in arr:
                    try:
                        all_values.append(int(v))
                    except (ValueError, TypeError):
                        pass
        except Exception:
            pass

    if all_values:
        return round(sum(all_values) / len(all_values), 2)
    return 0


def fetch_hq_m_avg_map(conn):
    """计算每个 PPN 的 HQ 月搜索量均值"""
    result = {}
    sql = text("SELECT TRIM(ppn) AS ppn_clean, month_hot FROM t_hq_peakfire")
    for row in conn.execute(sql).fetchall():
        ppn = row[0]
        month_hot = row[1]
        avg = parse_month_hot(month_hot)
        if ppn in result:
            # 如果有多个记录,取平均
            existing = result[ppn]
            result[ppn] = round((existing + avg) / 2, 2)
        else:
            result[ppn] = avg
    print(f"  HQ_M_AVG: {len(result)} 个 PPN")
    return result


def fetch_hq_sup_and_stock_map(conn, task_name=None):
    """获取每个 PPN 的 HQ 供给记录数 + 华强网库存总和
    t_hq_stock.stock 是字符串,需 CAST AS UNSIGNED
    """
    count_map = {}
    stock_map = {}
    extra_sql = ""
    params = {}
    if task_name:
        extra_sql = " AND task_name = :task_name"
        params['task_name'] = task_name
    sql = text(f"""
        SELECT TRIM(ppn) AS ppn_clean, COUNT(*) AS cnt,
               SUM(CASE WHEN stock REGEXP '^[0-9]+$' THEN CAST(stock AS UNSIGNED) ELSE 0 END) AS total_stock
        FROM t_hq_stock
        WHERE ppn IS NOT NULL AND TRIM(ppn) != '' {extra_sql}
        GROUP BY TRIM(ppn)
    """)
    for row in conn.execute(sql, params).fetchall():
        if row[0]:
            count_map[row[0]] = int(row[1]) if row[1] else 0
            stock_map[row[0]] = int(row[2]) if row[2] else 0
    print(f"  t_hq_stock: {len(count_map)} 个 PPN (count + stock)")
    return count_map, stock_map


def fetch_ic_sup_and_stock_map(conn, task_name=None):
    """获取每个 PPN 的 IC 供给记录数 + IC交易网库存总和
    t_ic_stock.stock_num 是 Integer,直接 SUM
    """
    count_map = {}
    stock_map = {}
    extra_sql = ""
    params = {}
    if task_name:
        extra_sql = " AND task_name = :task_name"
        params['task_name'] = task_name
    sql = text(f"""
        SELECT TRIM(ppn) AS ppn_clean, COUNT(*) AS cnt, SUM(stock_num) AS total_stock
        FROM t_ic_stock
        WHERE ppn IS NOT NULL AND TRIM(ppn) != '' {extra_sql}
        GROUP BY TRIM(ppn)
    """)
    for row in conn.execute(sql, params).fetchall():
        if row[0]:
            count_map[row[0]] = int(row[1]) if row[1] else 0
            stock_map[row[0]] = int(row[2]) if row[2] else 0
    print(f"  t_ic_stock: {len(count_map)} 个 PPN (count + stock)")
    return count_map, stock_map


def fetch_count_map(conn, table_name, ppn_column="ppn", task_name=None):
    """获取每个 PPN 在指定表中的记录数"""
    result = {}
    extra_sql = ""
    params = {}
    if task_name:
        extra_sql = " AND task_name = :task_name"
        params['task_name'] = task_name
    sql = text(f"""
        SELECT TRIM({ppn_column}) AS ppn_clean, COUNT(*) FROM {table_name}
        WHERE {ppn_column} IS NOT NULL AND TRIM({ppn_column}) != '' {extra_sql}
        GROUP BY TRIM({ppn_column})
    """)
    for row in conn.execute(sql, params).fetchall():
        if row[0]:
            result[row[0]] = int(row[1])
    print(f"  {table_name} count: {len(result)} 个 PPN")
    return result


def fetch_octopart_min_price(conn):
    """获取每个 PPN 的 Octopart 最低价格"""
    result = {}
    sql = text("""
        SELECT TRIM(ppn) AS ppn_clean, MIN(CAST(price AS DECIMAL(12,2))) as min_price
        FROM t_octopart_price
        WHERE price IS NOT NULL AND price != ''
        GROUP BY TRIM(ppn)
    """)
    for row in conn.execute(sql).fetchall():
        if row[0] and row[1]:
            result[row[0]] = float(row[1])
    print(f"  Octopart price: {len(result)} 个 PPN")
    return result


def fetch_octopart_stock(conn):
    """获取每个 PPN 的 Octopart 总库存"""
    result = {}
    sql = text("""
        SELECT TRIM(ppn) AS ppn_clean, SUM(CASE
            WHEN stock REGEXP '^[0-9]+$' THEN CAST(stock AS UNSIGNED)
            ELSE 0
        END) as total_stock
        FROM t_octopart_market
        GROUP BY TRIM(ppn)
    """)
    for row in conn.execute(sql).fetchall():
        if row[0] and row[1]:
            result[row[0]] = int(row[1])
    print(f"  Octopart stock: {len(result)} 个 PPN")
    return result


def fetch_digikey_status(conn):
    """获取每个 PPN 的 DigiKey 状态"""
    result = {}
    sql = text("SELECT TRIM(ppn) AS ppn_clean, status FROM t_digikey_attr WHERE status IS NOT NULL AND status != ''")
    for row in conn.execute(sql).fetchall():
        if row[0] and row[1]:
            result[row[0]] = row[1]
    print(f"  DigiKey status: {len(result)} 个 PPN")
    return result


def main():
    with app.app_context():
        engine = db.engine

        with engine.connect() as conn:
            print("=" * 60)
            print("开始回填 t_ppn_result 数据(最终版本)")
            print("=" * 60)

            # Step 1: 获取所有 PPN 基础数据
            print("\n[1/7] 获取 PPN 基础数据...")
            ppn_sql = text("SELECT ppn, manu_name, source FROM t_ppn")
            ppn_rows = conn.execute(ppn_sql).fetchall()
            print(f"  PPN 总数: {len(ppn_rows)}")

            if not ppn_rows:
                print("没有 PPN 数据,退出")
                return

            # Step 2: 预计算 HQ_M_AVG
            print("\n[2/7] 计算 HQ 月搜索量均值...")
            hq_m_avg_map = fetch_hq_m_avg_map(conn)

            # Step 3: 预计算 HQ_SUP_COUNT + HQ_STOCK
            print("\n[3/7] 计算 HQ 供给记录数 + 华强网库存...")
            hq_sup_map, hq_stock_map = fetch_hq_sup_and_stock_map(conn)

            # Step 4: 预计算 IC_SUP_COUNT + IC_STOCK
            print("\n[4/7] 计算 IC 供给记录数 + IC交易网库存...")
            ic_sup_map, ic_stock_map = fetch_ic_sup_and_stock_map(conn)

            # Step 5: 预计算其他计数指标
            print("\n[5/7] 计算 eFind/Wheat 指标...")
            efind_sup_map = fetch_count_map(conn, "t_efind_supplier", "ppn")
            wheat_global_map = fetch_count_map(conn, "t_wheat_record", "ppn")
            wheat_ru_map = fetch_count_map(conn, "t_rusprofile", "ppn")

            # Step 6: 预计算 Octopart 指标
            print("\n[6/7] 计算 Octopart 价格和库存...")
            oc_price_map = fetch_octopart_min_price(conn)
            oc_stock_map = fetch_octopart_stock(conn)

            # Step 7: 获取 DigiKey 状态
            print("\n[7/7] 获取 DigiKey 状态...")
            digikey_status_map = fetch_digikey_status(conn)

            # 清空旧数据并插入新数据
            print("\n" + "=" * 60)
            print("清空旧数据并写入新数据...")

            # 先清空
            conn.execute(text("DELETE FROM t_ppn_result"))

            # 批量插入(字段顺序与表结构一致;所有数值转 str 适配 varchar)
            insert_sql = text("""
                INSERT INTO t_ppn_result
                (ppn, manu_name, digikey_status, hq_m_avg, hq_sup_count, hq_stock,
                 ic_sup_count, ic_stock, efind_all_sup, wheat_global, wheat_ru,
                 oc_price, oc_stock, task_name)
                VALUES
                (:ppn, :manu_name, :digikey_status, :hq_m_avg, :hq_sup_count, :hq_stock,
                 :ic_sup_count, :ic_stock, :efind_all_sup, :wheat_global, :wheat_ru,
                 :oc_price, :oc_stock, :task_name)
            """)

            batch_size = 1000
            batch = []
            total_inserted = 0

            for row in ppn_rows:
                ppn = row[0]
                manu_name = row[1] or ""
                source = row[2] or ""

                # 从 source 字段解析 task_name (格式: source = "task_name")
                task_name = ""
                m = re.search(r'source\s*=\s*[\"\']([^\"\']+)[\"\']', source)
                if m:
                    task_name = m.group(1)
                else:
                    task_name = source

                # 所有数值字段转 str(适配 varchar 列)
                params = {
                    'ppn': ppn,
                    'manu_name': manu_name if manu_name else None,
                    'digikey_status': digikey_status_map.get(ppn),
                    'hq_m_avg': str(hq_m_avg_map.get(ppn, 0)) if ppn in hq_m_avg_map else None,
                    'hq_sup_count': str(hq_sup_map.get(ppn, 0)) if ppn in hq_sup_map else None,
                    'hq_stock': str(hq_stock_map.get(ppn, 0)),
                    'ic_sup_count': str(ic_sup_map.get(ppn, 0)) if ppn in ic_sup_map else None,
                    'ic_stock': str(ic_stock_map.get(ppn, 0)),
                    'efind_all_sup': str(efind_sup_map.get(ppn, '')) if ppn in efind_sup_map else '',
                    'wheat_global': str(wheat_global_map.get(ppn)) if ppn in wheat_global_map else None,
                    'wheat_ru': str(wheat_ru_map.get(ppn)) if ppn in wheat_ru_map else None,
                    'oc_price': str(oc_price_map.get(ppn)) if ppn in oc_price_map else None,
                    'oc_stock': str(oc_stock_map.get(ppn, '')) if ppn in oc_stock_map else '',
                    'task_name': task_name if task_name else None,
                }
                batch.append(params)

                if len(batch) >= batch_size:
                    conn.execute(insert_sql, batch)
                    total_inserted += len(batch)
                    print(f"  已写入 {total_inserted} 条...")
                    batch = []

            # 写入剩余
            if batch:
                conn.execute(insert_sql, batch)
                total_inserted += len(batch)

            conn.commit()

            print(f"\n回填完成!共写入 {total_inserted} 条记录")

            # 验证
            count = conn.execute(text("SELECT COUNT(*) FROM t_ppn_result")).scalar()
            print(f"t_ppn_result 表总记录数: {count}")

            # 查看示例数据
            sample = conn.execute(text("""
                SELECT ppn, manu_name, hq_m_avg, hq_sup_count, hq_stock, ic_sup_count, ic_stock
                FROM t_ppn_result LIMIT 5
            """)).fetchall()
            if sample:
                print("\n示例数据:")
                for row in sample:
                    print(f"  ppn={row[0]}, manu={row[1]}, hq_m_avg={row[2]}, hq_sup={row[3]}, hq_stock={row[4]}, ic_sup={row[5]}, ic_stock={row[6]}")

            print("\n" + "=" * 60)
            print("回填完成!")
            print("=" * 60)


if __name__ == '__main__':
    main()
