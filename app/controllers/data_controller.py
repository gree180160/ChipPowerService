from flask import Blueprint, request, jsonify
from app import db
from sqlalchemy import text

data_bp = Blueprint('data', __name__)


def success_response(data=None, message='Success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def error_response(message='Error', code=400):
    return jsonify({'code': code, 'message': message, 'data': None}), code


def execute_write(sql, data_list):
    """执行写入操作，支持批量"""
    try:
        with db.engine.connect() as conn:
            with conn.begin():
                conn.execute(text(sql), data_list)
        return True, f'成功写入 {len(data_list)} 条数据'
    except Exception as e:
        return False, str(e)


def execute_write_upsert(table_name, columns, data_list, conflict_cols):
    """
    高性能写入：INSERT ... ON DUPLICATE KEY UPDATE
    比 REPLACE INTO 快（不需要先DELETE再INSERT，直接UPDATE）
    :param table_name: 表名
    :param columns: 列名列表，如 ['ppn', 'manu', 'weak_hot']
    :param data_list: 字典列表数据
    :param conflict_cols: 冲突时需要更新的列名列表
    """
    try:
        col_str = ', '.join(columns)
        val_str = ', '.join([f':{c}' for c in columns])
        update_str = ', '.join([f'{c}=VALUES({c})' for c in conflict_cols])
        sql = f"INSERT INTO {table_name} ({col_str}) VALUES ({val_str}) ON DUPLICATE KEY UPDATE {update_str}"
        with db.engine.connect() as conn:
            with conn.begin():
                conn.execute(text(sql), data_list)
        return True, f'成功写入 {len(data_list)} 条数据'
    except Exception as e:
        return False, str(e)


def execute_query(sql, params=None, return_dict=False):
    """
    执行查询操作
    :param return_dict: True返回字典列表，False返回二维数组（兼容旧代码）
    """
    try:
        with db.engine.connect() as conn:
            if params:
                result = conn.execute(text(sql), params)
            else:
                result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchall()
            
            if return_dict:
                # 返回字典列表
                return True, [dict(zip(columns, row)) for row in rows]
            else:
                # 返回二维数组（按列顺序），处理时间类型
                result_list = []
                for row in rows:
                    processed_row = []
                    for val in row:
                        if hasattr(val, 'strftime'):
                            # datetime类型转字符串
                            processed_row.append(val.strftime('%Y-%m-%d %H:%M:%S'))
                        else:
                            processed_row.append(val)
                    result_list.append(processed_row)
                return True, result_list
    except Exception as e:
        return False, str(e)


def build_where_clause(filters):
    """
    构建WHERE子句
    支持两种方式：
    1. 普通字段参数: ?task_name=xxx&ppn=yyy → 自动构建 WHERE task_name = :task_name AND ppn = :ppn
    2. 自定义条件: ?filter_contend=task_name = "TBomHot" → 直接使用该字符串作为WHERE条件（兼容旧代码）
    """
    if not filters:
        return "", {}
    
    # 如果有filter_contend参数，优先使用它（自定义WHERE条件，兼容旧代码）
    if 'filter_contend' in filters and filters['filter_contend']:
        filter_str = filters['filter_contend']
        # 简单清理防止最基本的注入（完全禁用DROP/DELETE/UPDATE/INSERT/ALTER等危险操作）
        dangerous_keywords = ['DROP ', 'DELETE ', 'INSERT ', 'UPDATE ', 'ALTER ', 'TRUNCATE ', 'CREATE ', 'GRANT ', 'REVOKE ']
        for kw in dangerous_keywords:
            if kw in filter_str.upper():
                raise ValueError(f"filter_contend不允许包含危险关键字: {kw}")
        return " WHERE " + filter_str, {}
    
    # 普通字段精确匹配
    conditions = []
    params = {}
    for key, value in filters.items():
        if key == 'filter_contend':
            continue
        conditions.append(f"{key} = :{key}")
        params[key] = value
    
    if not conditions:
        return "", {}
    return " WHERE " + " AND ".join(conditions), params


def handle_table_read(table_name, select_cols="*", order_by=""):
    """
    通用表查询处理函数，统一处理异常和参数
    :param table_name: 表名
    :param select_cols: SELECT的列，默认*
    :param order_by: ORDER BY子句，例如 "ppn" 或 "st_part DESC"
    """
    try:
        where, params = build_where_clause(request.args.to_dict())
        order_sql = f" ORDER BY {order_by}" if order_by else ""
        sql = f"SELECT {select_cols} FROM {table_name}{where}{order_sql}"
        success, result = execute_query(sql, params)
        return success_response(data=result) if success else error_response(result, 500)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


# ==================== 健康检查 ====================
@data_bp.route('/health', methods=['GET'])
def health_check():
    return success_response(data={'status': 'ok', 'message': 'Data service is running'})


# ==================== Task ====================
@data_bp.route('/task/write', methods=['POST'])
def task_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_task (Tname, Tdes, Tstate, Tlevel) VALUES (:Tname, :Tdes, :Tstate, :Tlevel)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/task/read', methods=['GET'])
def task_read():
    return handle_table_read('t_task')


# ==================== IC Hot Monthly ====================
@data_bp.route('/ic_hot_m/write', methods=['POST'])
def ic_hot_m_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    months = ', '.join([f'm{i}' for i in range(1, 13)])
    placeholders = ', '.join([f':m{i}' for i in range(1, 13)])
    sql = f"REPLACE INTO t_IC_hot_m (ppn, manu, {months}, task_name) VALUES (:ppn, :manu, {placeholders}, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/ic_hot_m/read', methods=['GET'])
def ic_hot_m_read():
    return handle_table_read('t_IC_hot_m')


# ==================== IC Hot Weekly ====================
@data_bp.route('/ic_hot_w/write', methods=['POST'])
def ic_hot_w_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    weeks = ', '.join([f'w{i}' for i in range(1, 53)])
    placeholders = ', '.join([f':w{i}' for i in range(1, 53)])
    sql = f"REPLACE INTO t_IC_hot_w (ppn, manu, {weeks}, task_name) VALUES (:ppn, :manu, {placeholders}, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/ic_hot_w/read', methods=['GET'])
def ic_hot_w_read():
    return handle_table_read('t_IC_hot_w')


# ==================== IC Price Demand ====================
@data_bp.route('/ic_price_demand/write', methods=['POST'])
def ic_price_demand_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_ic_price_demand (ppn, manu, price, month_search_count, supplierCount, cp_count, rank_count, task_name) VALUES (:ppn, :manu, :price, :month_search_count, :supplierCount, :cp_count, :rank_count, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/ic_price_demand/read', methods=['GET'])
def ic_price_demand_read():
    return handle_table_read('t_ic_price_demand')


# ==================== CXYX Stock ====================
@data_bp.route('/cxyx_stock/write', methods=['POST'])
def cxyx_stock_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_cxyx_stock (supplier_name, model, brand, category, price_step, stock_num, batch_info, task_name) VALUES (:supplier_name, :model, :brand, :category, :price_step, :stock_num, :batch_info, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/cxyx_stock/read', methods=['GET'])
def cxyx_stock_read():
    return handle_table_read('t_cxyx_stock')


# ==================== IC Stock ====================
@data_bp.route('/ic_stock/write', methods=['POST'])
def ic_stock_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_ic_stock (ppn, st_manu, supplier_ppn, supplier_manu, supplier, isICCP, isSSCP, iSRanking, isHotSell, isYouXian, batch, pakaging, stock_num, task_name) VALUES (:ppn,:st_manu, :supplier_ppn, :supplier_manu, :supplier, :isICCP, :isSSCP, :iSRanking, :isHotSell, :isYouXian,:batch, :pakaging, :stock_num, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/ic_stock/read', methods=['GET'])
def ic_stock_read():
    return handle_table_read('t_ic_stock')


# ==================== IC Des ====================
@data_bp.route('/ic_des/write', methods=['POST'])
def ic_des_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_ic_des (ppn, manu, todaySearch, todaySearch_person, yesterdaySearch, yesterdaySearch_person, reference_price, week_search, market_hot, risk, mainLand_stock, international_stock, task_name) VALUES (:ppn, :manu, :todaySearch, :todaySearch_person, :yesterdaySearch, :yesterdaySearch_person, :reference_price, :week_search, :market_hot, :risk, :mainLand_stock, :international_stock, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/ic_des/read', methods=['GET'])
def ic_des_read():
    return handle_table_read('t_ic_des')


# ==================== HQ Stock ====================
@data_bp.route('/hq_stock/write', methods=['POST'])
def hq_stock_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_hq_stock (ppn, std_manu, supplier, sup_ppn, sup_manu, batch, stock, packing, param, place, instruction, publish_date, task_name) VALUES (:ppn, :std_manu, :supplier, :sup_ppn, :sup_manu, :batch, :stock, :packing, :param, :place, :instruction, :publish_date, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/hq_stock/read', methods=['GET'])
def hq_stock_read():
    return handle_table_read('t_hq_stock')


# ==================== HQ Hot ====================
@data_bp.route('/hq_hot/write', methods=['POST'])
def hq_hot_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    columns = ['ppn', 'manu', 'weak_hot', 'month_hot', 'task_name']
    success, msg = execute_write_upsert('t_hq_peakfire', columns, data_list, ['manu', 'weak_hot', 'month_hot', 'task_name'])
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/hq_hot/read', methods=['GET'])
def hq_hot_read():
    return handle_table_read('t_hq_peakfire')


@data_bp.route('/hq_hot/query_by_models', methods=['POST'])
def hq_hot_query_by_models():
    model_list = request.json.get('models', [])
    results = []
    for model in model_list:
        success, data = execute_query("SELECT * FROM t_hq_peakfire WHERE ppn = :ppn", {'ppn': model}, return_dict=True)
        if success and data:
            results.append(data[0])
        else:
            results.append({'ppn': model, 'manu': '--', 'weak_hot': '--', 'month_hot': '--'})
    return success_response(data=results)


# ==================== EFind Stock ====================
@data_bp.route('/efind_stock/write', methods=['POST'])
def efind_stock_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_efind_stock (ppn, manu, sup_manu, supplier, publish_date, info, price, stock, task_name) VALUES (:ppn, :manu, :sup_manu, :supplier, :publish_date, :info, :price, :stock, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/efind_stock/read', methods=['GET'])
def efind_stock_read():
    return handle_table_read('t_efind_stock')


# ==================== EFind Supplier ====================
@data_bp.route('/efind_supplier/write', methods=['POST'])
def efind_supplier_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_efind_supplier (ppn, manu, all_supplier, price_supplier, stock_supplier, stock, middle_price, min_price, max_price, task_name) VALUES (:ppn, :manu, :all_supplier, :price_supplier, :stock_supplier, :stock, :middle_price, :min_price, :max_price, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/efind_supplier/read', methods=['GET'])
def efind_supplier_read():
    return handle_table_read('t_efind_supplier')


# ==================== BOM Price ====================
@data_bp.route('/bom_price/write', methods=['POST'])
def bom_price_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_bom_price (ppn, manu, supplier, package, lot, quoted_price, release_time, stock_num, valid_supplier, task_name) VALUES (:ppn, :manu, :supplier, :package, :lot, :quoted_price, :release_time, :stock_num, :valid_supplier, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/bom_price/read', methods=['GET'])
def bom_price_read():
    return handle_table_read('t_bom_price')


# ==================== Octopart Price ====================
@data_bp.route('/octopart_price/write', methods=['POST'])
def octopart_price_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_octopart_price (ppn, manu, is_star, distribute, sku, stock, moq, currency_type,k_price, updated, opn, task_name) VALUES (:ppn, :manu, :is_star, :distribute, :sku, :stock, :moq, :currency_type,:k_price, :updated, :opn, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/octopart_price/read', methods=['GET'])
def octopart_price_read():
    return handle_table_read('t_octopart_price', order_by='ppn')


# ==================== Octopart Market ====================
@data_bp.route('/octopart_market/write', methods=['POST'])
def octopart_market_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_octopart_market (ppn, manu, des, distribute, stock, currency_type, k_price, stock_pic, opn, task_name) VALUES (:ppn, :manu, :des, :distribute, :stock, :currency_type, :k_price, :stock_pic, :opn, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/octopart_market/read', methods=['GET'])
def octopart_market_read():
    return handle_table_read('t_octopart_market', 
                            select_cols='ppn, manu, des, distribute, stock, currency_type, k_price, opn, task_name, update_time',
                            order_by='opn')


# ==================== Octopart Info ====================
@data_bp.route('/octopart_info/write', methods=['POST'])
def octopart_info_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_octopart_info (ppn, manu, des, distribute, stock, currency_type, k_price, opn, stock_data, tech_data, supplier_data, task_name) VALUES (:ppn, :manu, :des, :distribute, :stock, :currency_type, :k_price, :opn, :stock_data, :tech_data, :supplier_data, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/octopart_info/read', methods=['GET'])
def octopart_info_read():
    return handle_table_read('t_octopart_info', 
                            select_cols='ppn, manu, des, distribute, stock, currency_type, k_price, opn, task_name, update_time',
                            order_by='opn')


# ==================== FindChip Stock ====================
@data_bp.route('/findchip_stock/write', methods=['POST'])
def findchip_stock_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_findchips_stock (ppn, manu, supplier, authorized, part_url, stock_str, task_name) VALUES (:ppn, :manu, :supplier, :authorized, :part_url, :stock_str, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/findchip_stock/read', methods=['GET'])
def findchip_stock_read():
    return handle_table_read('t_findchips_stock', order_by='ppn')


# ==================== Digikey Attr ====================
@data_bp.route('/digikey_attr/write', methods=['POST'])
def digikey_attr_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_digikey_attr (ppn, manu, digi_key_code, manu_code, des, delivery_time, detail_des, category, serial, package, status, kind, single_channel, voltage_reverse, voltage_breakdown, voltage_ipp, peakCurrentPulse, peakPowerPulse, protect_power, apply, capacitance, operating_temperature, install_kind, shell, supplier_packeage, product_code, task_name) VALUES (:ppn, :manu, :digi_key_code, :manu_code, :des, :delivery_time, :detail_des, :category, :serial, :package, :status, :kind, :single_channel, :voltage_reverse, :voltage_breakdown, :voltage_ipp, :peakCurrentPulse, :peakPowerPulse, :protect_power, :apply, :capacitance, :operating_temperature, :install_kind, :shell, :supplier_packeage, :product_code, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/digikey_attr/read', methods=['GET'])
def digikey_attr_read():
    return handle_table_read('t_digikey_attr')


# ==================== Wheat Record ====================
@data_bp.route('/wheat_record/write', methods=['POST'])
def wheat_record_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    is_ru = request.args.get('is_ru', 'false').lower() == 'true'
    try:
        with db.engine.connect() as conn:
            with conn.begin():
                for item in data_list:
                    if is_ru:
                        sql = "INSERT INTO t_wheat_record(`keyword`, `ru_records`, `task_name`) VALUES (:keyword, :ru_records, :task_name) ON DUPLICATE KEY UPDATE `ru_records` = VALUES(`ru_records`)"
                    else:
                        sql = "INSERT INTO t_wheat_record(`keyword`, `all_records`, `task_name`) VALUES (:keyword, :all_records, :task_name) ON DUPLICATE KEY UPDATE `all_records` = VALUES(`all_records`)"
                    conn.execute(text(sql), item)
        return success_response(message=f'成功写入 {len(data_list)} 条数据')
    except Exception as e:
        return error_response(str(e), 500)


@data_bp.route('/wheat_record/read', methods=['GET'])
def wheat_record_read():
    return handle_table_read('t_wheat_record')


# ==================== Wheat Buyer ====================
@data_bp.route('/wheat_buyer/write', methods=['POST'])
def wheat_buyer_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_wheat_buyer(keyword, wheat_date, buyer, supplier, HSCode, description, buy_country, supplier_country, productContry, weight, number, totalValue, current_page, task_name) VALUES (:keyword, :wheat_date, :buyer, :supplier, :HSCode, :description, :buy_country, :supplier_country, :productContry, :weight, :number, :totalValue, :current_page, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/wheat_buyer/read', methods=['GET'])
def wheat_buyer_read():
    return handle_table_read('t_wheat_buyer')


# ==================== Rusprofile ====================
@data_bp.route('/rusprofile/write', methods=['POST'])
def rusprofile_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_rusprofile (company_name, profile_id, full_name, inn, activity, register_date, industry_rank, company_address, phone, email, website, revenue, profit, cost, task_name) VALUES (:company_name, :profile_id, :full_name, :inn, :activity, :register_date, :industry_rank, :company_address, :phone, :email,:website, :revenue, :profit, :cost, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/rusprofile/read', methods=['GET'])
def rusprofile_read():
    return handle_table_read('t_rusprofile')


# ==================== Future Info ====================
@data_bp.route('/future_info/write', methods=['POST'])
def future_info_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_futrue(st_part, st_manu, f_ppn, f_manu, OnOrder, stock, leadTime, unitPrice, task_name) VALUES (:st_part, :st_manu, :f_ppn, :f_manu, :OnOrder, :stock, :leadTime, :unitPrice, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/future_info/read', methods=['GET'])
def future_info_read():
    return handle_table_read('t_futrue', order_by='st_part')


# ==================== Arrow Info ====================
@data_bp.route('/arrow_info/write', methods=['POST'])
def arrow_info_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_arrow(st_part, st_manu, a_ppn, a_manu, stock, leadTime, price, batch, task_name) VALUES (:st_part, :st_manu, :a_ppn, :a_manu, :stock, :leadTime, :price, :batch, :task_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/arrow_info/read', methods=['GET'])
def arrow_info_read():
    return handle_table_read('t_arrow', order_by='st_part')


# ==================== PPN 型号库 ====================
@data_bp.route('/ppn/write', methods=['POST'])
def ppn_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_ppn (ppn, manu_id, manu_name, source) VALUES (:ppn, :manu_id, :manu_name, :source)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/ppn/read', methods=['GET'])
def ppn_read():
    return handle_table_read('t_ppn', select_cols='ppn')


# ==================== OPN 原厂型号 ====================
@data_bp.route('/opn/write', methods=['POST'])
def opn_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_opn (opn, manu_id, manu_name) VALUES (:opn, :manu_id, :manu_name)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/opn/read', methods=['GET'])
def opn_read():
    return handle_table_read('t_opn', select_cols='opn')


# ==================== User 用户 ====================
@data_bp.route('/user/write', methods=['POST'])
def user_write():
    data_list = request.json if isinstance(request.json, list) else [request.json]
    sql = "REPLACE INTO t_user (username, password, role) VALUES (:username, :password, :role)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/user/read', methods=['GET'])
def user_read():
    return handle_table_read('t_user')


@data_bp.route('/user/login', methods=['POST'])
def user_login():
    """用户登录验证"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return error_response('用户名和密码不能为空', 400)
    
    sql = "SELECT * FROM t_user WHERE username = :username AND password = :password"
    success, result = execute_query(sql, {'username': username, 'password': password}, return_dict=True)
    
    if not success:
        return error_response(result, 500)
    
    if len(result) == 0:
        return error_response('用户名或密码错误', 401)
    
    user = result[0]
    # 不返回密码
    if 'password' in user:
        del user['password']
    return success_response(data=user, message='登录成功')
