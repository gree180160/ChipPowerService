import time

import mysql.connector
from mysql.connector import pooling
from Manager import AccManage
from WRTools import ExcelHelp, PathHelp, LogHelper


def singleton(cls):
    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper

@singleton
# 建立数据库连接
class DBRecommandChip:

    cnx = mysql.connector.connect(
        host=AccManage.mys['h'],
        user=AccManage.mys['n'],
        password=AccManage.mys['p'],
        database="yjcx_recommended",
        ssl_disabled=True,  # 忽略 SSL 验证
        connection_timeout=120
    )

    def __init__(self):
        config = {
            "host": AccManage.mys['h'],
            "user": AccManage.mys['n'],
            "password": AccManage.mys['p'],
            "database": "yjcx_recommended",
        }
        self.connection_pool = pooling.MySQLConnectionPool(pool_name="my_pool", pool_size=20, **config)

    def sql_write(self, sql, data, needLog):
        # 创建游标对象
        # 从连接池获取连接
        try:
            cnx = self.connection_pool.get_connection()
            print(f'write data:\n {data}')
            cursor = cnx.cursor()
            # 执行插入操作
            cursor.executemany(sql, data)
            # 提交事务
            cnx.commit()
            # 关闭游标和数据库连接
            cursor.close()
            cnx.close()
            return True
        except Exception as e:
            if needLog:
                print(f"{e}")
                LogHelper.write_log(log_file_name=PathHelp.get_file_path('WRTools', 'MySqlHelpLog.txt'),
                                content=f'yjcx_recommended wirte error: {data}')
                # 关闭游标和数据库连接
                cursor.close()
                cnx.close()
            return False

    def sql_write_twice(self, sql, data):
        result = self.sql_write(sql, data, False)
        if not result:
            self.sql_write(sql, data, True)

    def sql_read(self, sql):
        # 从连接池获取连接
        cnx = self.connection_pool.get_connection()
        # 创建游标对象
        cursor = cnx.cursor()
        # 查询数据的SQL语句
        query = sql
        # 执行查询操作
        cursor.execute(query)
        # 获取查询结果
        result = cursor.fetchall()
        # 将结果转换为列表
        data_list = list(result)
        # 打印查询结果
        # 关闭游标和数据库连接
        cursor.close()
        cnx.close()
        print(f'read data:\n {data_list}')
        return data_list

    # task manager
    def task_write(self, data: list):
        sql_str = "REPLACE INTO t_task (Tname, Tdes, Tstate, Tlevel) VALUES (%s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def task_read(self, filter_contend):
        query = f"SELECT * FROM t_task where {filter_contend}"
        result = self.sql_read(query)
        print(result)
        return result

    # 输入二维数组
    def IC_hot_m_write(self, data: list):
        # 插入数据的SQL语句
        # 插入数据的SQL语句
        sql_str = "REPLACE INTO t_IC_hot_m (ppn, manu"
        for index in range(1, 13):
            sql_str += f', m{index}'
        sql_str += ',task_name) VALUES (%s, %s '
        for index in range(1, 13):
            sql_str += ', %s'
        sql_str += ", %s)"
        self.sql_write_twice(sql=sql_str, data=data)

    def IC_hot_m_read(self, filter_contend):
        query = f"SELECT * FROM t_IC_hot_m where {filter_contend}"
        result = self.sql_read(query)
        print(result)
        return result

    def IC_hot_w_write(self, data: list):
        # 插入数据的SQL语句
        sql_str = "REPLACE INTO t_IC_hot_w (ppn, manu"
        for index in range(1, 53):
            sql_str += f', w{index}'
        sql_str += ',task_name) VALUES (%s, %s '
        for index in range(1, 53):
            sql_str += ', %s'
        sql_str += ", %s)"
        self.sql_write_twice(sql_str, data)

    def IC_hot_w_read(self, filter_contend):
        query = f"SELECT * FROM t_IC_hot_w where {filter_contend}"
        result = self.sql_read(query)
        print(result)
        return result

    def ic_price_demand_write(self, data: list):
        sql_str = "REPLACE INTO t_ic_price_demand (ppn, manu, price, month_search_count, supplierCount, cp_count, rank_count, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def ic_price_demand_read(self, filter_contend):
        query = f"SELECT * FROM t_ic_price_demand where {filter_contend}"
        result = self.sql_read(query)
        print(result)
        return result

    def ic_cxyx_stock_write(self, data: list):
        sql_str = "REPLACE INTO t_cxyx_stock (supplier_name, model, brand, category, price_step, stock_num, batch_info, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def ic_cxyx_stock_read(self, filter_contend):
        query = f"SELECT * FROM t_cxyx_stock where {filter_contend}"
        result = self.sql_read(query)
        print(result)
        return result

    def ic_stock(self, data: list):
        sql_str = "REPLACE INTO t_ic_stock (ppn, st_manu, supplier_ppn, supplier_manu, supplier, isICCP, isSSCP, iSRanking, isHotSell, isYouXian, batch, pakaging, stock_num, task_name) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def ic_stock_read(self, filter_contend):
        query = f"SELECT * FROM t_ic_stock where {filter_contend}"
        result = self.sql_read(query)
        return result

    def ic_des_write(self, data:list):
        sql_str = "REPLACE INTO t_ic_des (ppn, manu, todaySearch, todaySearch_person, yesterdaySearch, yesterdaySearch_person, reference_price, week_search, market_hot, risk, mainLand_stock, international_stock, task_name)  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def hq_stock_write(self, data: list):
        sql_str = "REPLACE INTO t_hq_stock (ppn, std_manu, supplier, sup_ppn, sup_manu, batch, stock, packing, param, place, instruction, publish_date, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def hq_stock_read(self, filter_contend):
        query = f"SELECT * FROM t_hq_stock where {filter_contend}"
        result = self.sql_read(query)
        return result

    def hq_hot_write(self, data: list):
        sql_str = "REPLACE INTO t_hq_peakfire (ppn, manu, weak_hot, month_hot, task_name) VALUES (%s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def hq_hot_read(self, filter_contend):
        query = f"SELECT * FROM t_hq_peakfire where {filter_contend}"
        result = self.sql_read(query)
        return result

    # efind
    def efind_stock_write(self, data: list):
        sql_str = "REPLACE INTO t_efind_stock (ppn, manu, sup_manu, supplier, publish_date, info, price, stock, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def efind_supplier_write(self, data: list):
        sql_str = "REPLACE INTO t_efind_supplier (ppn, manu, all_supplier, price_supplier, stock_supplier,stock, middle_price, min_price, max_price, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def efind_supplier_read(self, filter_contend):
        query = f"SELECT * FROM t_efind_supplier where {filter_contend}"
        result = self.sql_read(query)
        return result

    # bom
    def bom_price_write(self, data: list):
        sql_str = "REPLACE INTO t_bom_price (ppn, manu, supplier, package, lot, quoted_price, release_time, stock_num, valid_supplier, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def bom_price_read(self, filter_contend):
        query = f"SELECT * FROM t_bom_price where {filter_contend}"
        result = self.sql_read(query)
        return result

    def octopart_price_write(self, data: list):
        sql_str = "REPLACE INTO t_octopart_price (ppn, manu, is_star, distribute, sku, stock, moq, currency_type,k_price, updated, opn, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def octopart_price_read(self, filter_contend):
        query = f"SELECT * FROM t_octopart_price where {filter_contend} order by ppn"
        result = self.sql_read(query)
        return result

    def octopart_market_write(self, data: list):
        sql_str = "REPLACE INTO t_octopart_market (ppn, manu, des, distribute, stock, currency_type, k_price, stock_pic, opn, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def octopart_market_read(self, filter_contend):
        query = f"SELECT ppn, manu, des, distribute, stock, currency_type, k_price, opn, task_name, update_time  FROM t_octopart_market WHERE {filter_contend} order by opn"
        result = self.sql_read(query)
        return result

    def octopart_info_write(self, data: list):
        sql_str = "REPLACE INTO t_octopart_info (ppn, manu, des, distribute, stock, currency_type, k_price, opn, stock_data, tech_data, supplier_data, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def octopart_info_read(self, filter_contend):
        query = f"SELECT ppn, manu, des, distribute, stock, currency_type, k_price, opn, task_name, update_time  FROM t_octopart_info WHERE {filter_contend} order by opn"
        result = self.sql_read(query)
        return result

    def findchip_stock_write(self, data: list):
        sql_str = "REPLACE INTO t_findchips_stock (ppn, manu, supplier, authorized, part_url, stock_str, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def findchip_stock_read(self, filter_contend):
        query = f"SELECT * FROM t_findchips_stock where {filter_contend} order by ppn"
        result = self.sql_read(query)
        return result

    def digikey_attr_write(self, data: list):
        # 假设您已经建立了与 MySQL 数据库的连接，并创建了一个名为 cursor 的游标对象
        sql_str = "REPLACE INTO t_digikey_attr (ppn, manu, digi_key_code, manu_code, des, delivery_time, detail_des, category, serial, package, status, kind, single_channel, voltage_reverse, voltage_breakdown, voltage_ipp, peakCurrentPulse, peakPowerPulse, protect_power, apply, capacitance, operating_temperature, install_kind, shell, supplier_packeage, product_code, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    #WHEAT
    def wheat_record_write(self, data: list, isRU: bool):
        if isRU:
            sql_str = "INSERT INTO t_wheat_record(`keyword`, `ru_records`, `task_name`) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE `ru_records` = VALUES(`ru_records`)"
        else:
            sql_str = "INSERT INTO t_wheat_record(`keyword`, `all_records`, `task_name`) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE `all_records` = VALUES(`all_records`)"
        self.sql_write_twice(sql_str, data)

    def wheat_record_read(self, filter_contend):
        query = f"SELECT * FROM t_wheat_record where {filter_contend}"
        result = self.sql_read(query)
        print(result)
        return result

    def wheat_buyer_write(self, data: list):
        sql_str = "REPLACE INTO t_wheat_buyer(keyword, wheat_date, buyer, supplier, HSCode, description, buy_country, supplier_country, productContry, weight, number, totalValue, current_page, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def wheat_buyer_read(self, filter_contend):
        query = f"SELECT * FROM t_wheat_buyer where {filter_contend}"
        result = self.sql_read(query)
        print(result)
        return result

    #RUSPROFILE
    def rusprofile_write(self, data: list):
        sql_str = "REPLACE INTO t_rusprofile (company_name, profile_id, full_name, inn, activity, register_date, industry_rank, company_address, phone, email, website, revenue, profit, cost, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def rusprofile_read(self, filter_contend):
        query = f"SELECT * FROM t_rusprofile where {filter_contend}"
        result = self.sql_read(query)
        print(result)
        return result

    def future_info_write(self, data: list):
        sql_str = "REPLACE INTO t_futrue(st_part, st_manu, f_ppn, f_manu, OnOrder, stock, leadTime, unitPrice, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def future_info_read(self, filter_contend):
        query = f"SELECT * FROM t_futrue where {filter_contend} order by st_part"
        result = self.sql_read(query)
        return result

    def arrow_info_write(self, data: list):
        sql_str = "REPLACE INTO t_arrow(st_part, st_manu, a_ppn, a_manu, stock, leadTime, price, batch, task_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def arrow_info_read(self, filter_contend):
        query = f"SELECT * FROM t_arrow where {filter_contend} order by st_part"
        result = self.sql_read(query)
        return result

    def ppn_write(self, data: list):
        sql_str = "REPLACE INTO t_ppn (ppn, manu_id, manu_name, source) VALUES (%s, %s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def ppn_read(self, filter_contend):
        query = f"SELECT ppn FROM t_ppn where {filter_contend}"
        result = self.sql_read(query)
        print(result)
        return result

    def opn_write(self, data: list):
        sql_str = "REPLACE INTO t_opn (opn, manu_id, manu_name) VALUES (%s, %s, %s)"
        self.sql_write_twice(sql_str, data)

    def opn_read(self, filter_contend):
        query = f"SELECT opn FROM t_opn where {filter_contend}"
        result = self.sql_read(query)
        print(result)
        return result

    def IC_hot_adjust(self):
        cnx = self.connection_pool.get_connection()
        cursor = cnx.cursor()
        # 定义要修改的数组和新的manu值
        array1 = ExcelHelp.read_col_content(file_name=PathHelp.get_file_path(None, 'TTI.xlsx'), sheet_name='ppn',
                                            col_index=1)[800:900]
        new_manu = 'Texas Instruments'

        # 循环遍历数组中的值，逐行进行修改
        for ppn in array1:
            # 构建更新语句
            update_query = f"UPDATE t_ic_hot_m SET manu = '{new_manu}' WHERE ppn = '{ppn}'"
            # 执行更新语句
            cursor.execute(update_query)
            # 提交更改
            cnx.commit()
        # 关闭连接
        cursor.close()
        cnx.close()


def query_ppn_by_models(model_list):
        # 连接数据库
        conn = mysql.connector.connect(
            host=AccManage.mys['h'],
            user=AccManage.mys['n'],
            password=AccManage.mys['p'],
            database="yjcx_recommended",
            ssl_disabled=True,  # 忽略 SSL 验证
            buffered=True, # 添加缓冲参数
            connection_timeout=120
        )

        cursor = conn.cursor()

        results = []
        for model in model_list:
            # 查询每个元素
            query = "SELECT * FROM t_hq_peakfire WHERE ppn = %s"
            cursor.execute(query, (model,))
            record = cursor.fetchone()
            if record:
                results.append(record)
            else:
                results.append([model, '--', '--'])

        cursor.close()
        conn.close()
        return results


if __name__ == "__main__":
    manager = DBRecommandChip()
    # # (name, age, address, hot, qq, tel, phone)
    # arr1 = [["ATMEGA88PA-MU", "MICROCHIP", "¥6.836", "175", "443"]]
    arr1 = manager.bom_price_read(f'task_name = "TFL_ICStock1"')
    print(f"result: {arr1}")
    # manager.ic_price_demand(arr1)

