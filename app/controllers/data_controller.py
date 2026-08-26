import ast
import json
from flask import Blueprint, request, jsonify
from app import db
from sqlalchemy import text

data_bp = Blueprint('data', __name__)


def success_response(data=None, message='Success', code=200):
    return jsonify({'code': code, 'message': message, 'data': data}), code


def error_response(message='Error', code=400):
    return jsonify({'code': code, 'message': message, 'data': None}), code


def execute_write(sql, data_list, bind=None):
    """执行写入操作，支持批量。bind=None用主库，bind='monitor'用监控库"""
    try:
        engine = db.engines.get(bind) if bind else db.engine
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text(sql), data_list)
        return True, f'成功写入 {len(data_list)} 条数据'
    except Exception as e:
        return False, str(e)


def execute_write_upsert(table_name, columns, data_list, conflict_cols, bind=None):
    """
    高性能写入：INSERT ... ON DUPLICATE KEY UPDATE
    比 REPLACE INTO 快（不需要先DELETE再INSERT，直接UPDATE）
    :param bind: None用主库，'monitor'用监控库
    """
    try:
        col_str = ', '.join(columns)
        val_str = ', '.join([f':{c}' for c in columns])
        update_str = ', '.join([f'{c}=VALUES({c})' for c in conflict_cols])
        sql = f"INSERT INTO {table_name} ({col_str}) VALUES ({val_str}) ON DUPLICATE KEY UPDATE {update_str}"
        engine = db.engines.get(bind) if bind else db.engine
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text(sql), data_list)
        return True, f'成功写入 {len(data_list)} 条数据'
    except Exception as e:
        return False, str(e)


def execute_query(sql, params=None, return_dict=False, bind=None):
    """
    执行查询操作
    :param return_dict: True返回字典列表，False返回二维数组（兼容旧代码）
    :param bind: None用主库，'monitor'用监控库
    """
    try:
        engine = db.engines.get(bind) if bind else db.engine
        with engine.connect() as conn:
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
    sql = "REPLACE INTO t_task (Tname, Tdes, Tstate, Tlevel, tkind) VALUES (:Tname, :Tdes, :Tstate, :Tlevel, :tkind)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/task/read', methods=['GET'])
def task_read():
    return handle_table_read('t_task')


@data_bp.route('/task/update', methods=['POST'])
def task_update():
    """更新任务字段。请求体: {TID, Tname, Tdes, Tstate, Tlevel, tkind, TstartDate, TendDate}(部分字段可选)"""
    data = request.json or {}
    tid = data.get('TID')
    if not tid:
        return error_response('TID 不能为空', 400)
    # 可更新字段(白名单)
    updatable = ['Tname', 'Tdes', 'Tstate', 'Tlevel', 'tkind', 'TstartDate', 'TendDate']
    set_clauses = []
    params = {'TID': tid}
    for col in updatable:
        if col in data:
            set_clauses.append(f"{col} = :{col}")
            params[col] = data[col]
    if not set_clauses:
        return error_response('没有需要更新的字段', 400)
    try:
        engine = db.engine
        with engine.connect() as conn:
            with conn.begin():
                result = conn.execute(
                    text(f"UPDATE t_task SET {', '.join(set_clauses)} WHERE TID = :TID"),
                    params
                )
                if result.rowcount == 0:
                    return error_response(f'未找到 TID={tid} 的任务', 404)
        return success_response(message=f'任务 TID={tid} 更新成功')
    except Exception as e:
        return error_response(str(e), 500)


@data_bp.route('/task/delete', methods=['POST'])
def task_delete():
    """删除任务。请求体: {TID}"""
    data = request.json or {}
    tid = data.get('TID')
    if not tid:
        return error_response('TID 不能为空', 400)
    try:
        engine = db.engine
        with engine.connect() as conn:
            with conn.begin():
                result = conn.execute(
                    text("DELETE FROM t_task WHERE TID = :TID"),
                    {'TID': tid}
                )
                if result.rowcount == 0:
                    return error_response(f'未找到 TID={tid} 的任务', 404)
        return success_response(message=f'任务 TID={tid} 已删除')
    except Exception as e:
        return error_response(str(e), 500)


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


def _parse_int_array(raw):
    """解析数组字符串为 int 列表(兼容 Python 字面量与 JSON 数组)。
    非数组(标量/无法解析)返回 [] → 前端显示 '--',便于暴露数据问题。"""
    if not raw or not str(raw).strip():
        return []
    s = str(raw).strip()
    parsed = None
    try:
        parsed = ast.literal_eval(s)
    except (ValueError, SyntaxError):
        try:
            parsed = json.loads(s.replace("'", '"'))
        except Exception:
            parsed = None
    if isinstance(parsed, (list, tuple)):
        result = []
        for v in parsed:
            try:
                result.append(int(float(v)))
            except (ValueError, TypeError):
                pass
        return result
    return []


def _parse_stock_points(raw):
    """解析 t_octopart_info.stock_data JSON 字符串为 [{date, stock}] 库存波动点位。
    非法条目(缺 date/totalInventory 或非 dict)跳过,保证前端拿到干净数据;无法解析返回 []。"""
    if not raw or not str(raw).strip():
        return []
    try:
        arr = json.loads(str(raw))
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(arr, list):
        return []
    points = []
    for item in arr:
        if not isinstance(item, dict):
            continue
        d = item.get('date')
        s = item.get('totalInventory')
        if d is None or s is None:
            continue
        try:
            points.append({'date': d, 'stock': int(s)})
        except (TypeError, ValueError):
            continue
    return points


def _to_int(raw):
    """解析字符串/数字为 int;空、0 或无法解析返回 None(→ 前端显示 --,避免 0 误导用户)。"""
    if raw is None or str(raw).strip() == '':
        return None
    try:
        n = int(float(raw))
        return n if n != 0 else None
    except (ValueError, TypeError):
        return None


@data_bp.route('/hq_hot/by_ppn', methods=['GET'])
def hq_hot_by_ppn():
    """按 ppn 查询 t_hq_peakfire 最新记录(按 update_time 倒序取第一条),返回 month_hot/weak_hot 的 int 数组及其均值。
    查询参数:
      - ppn: PPN 型号 (必填)
    返回: { code, data: { month_hot_array, month_hot_avg, weak_hot_array, weak_hot_avg, update_time } | null }
    """
    ppn = request.args.get('ppn', '').strip()
    if not ppn:
        return error_response('ppn 不能为空', 400)

    try:
        engine = db.engine
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT month_hot, weak_hot, update_time
                FROM t_hq_peakfire
                WHERE ppn = :ppn
                ORDER BY update_time DESC
                LIMIT 1
            """), {'ppn': ppn}).fetchone()

            if not row:
                return jsonify({'code': 200, 'message': 'Success', 'data': None}), 200

            month_hot_array = _parse_int_array(row[0])
            weak_hot_array = _parse_int_array(row[1])
            month_hot_avg = round(sum(month_hot_array) / len(month_hot_array), 2) if month_hot_array else None
            weak_hot_avg = round(sum(weak_hot_array) / len(weak_hot_array), 2) if weak_hot_array else None

            data = {
                'month_hot_array': month_hot_array,
                'month_hot_avg': month_hot_avg,
                'weak_hot_array': weak_hot_array,
                'weak_hot_avg': weak_hot_avg,
                'update_time': row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else None,
            }
            return jsonify({'code': 200, 'message': 'Success', 'data': data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f'查询 hq_hot 失败: {str(e)}', 500)


@data_bp.route('/ic_price_demand/by_ppn', methods=['GET'])
def ic_price_demand_by_ppn():
    """按 ppn 查询 t_ic_price_demand 最新记录(按 update_time 倒序取第一条),返回 month_search_count。
    查询参数:
      - ppn: PPN 型号 (必填)
    返回: { code, data: { month_search_count: int|null, update_time } | null }
    注:0/空/无法解析返回 None → 前端显示 --,避免 0 误导用户。
    """
    ppn = request.args.get('ppn', '').strip()
    if not ppn:
        return error_response('ppn 不能为空', 400)

    try:
        engine = db.engine
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT month_search_count, update_time
                FROM t_ic_price_demand
                WHERE ppn = :ppn
                ORDER BY update_time IS NULL, update_time DESC
                LIMIT 1
            """), {'ppn': ppn}).fetchone()

            if not row:
                return jsonify({'code': 200, 'message': 'Success', 'data': None}), 200

            data = {
                'month_search_count': _to_int(row[0]),
                'update_time': row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else None,
            }
            return jsonify({'code': 200, 'message': 'Success', 'data': data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f'查询 ic_price_demand 失败: {str(e)}', 500)


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


@data_bp.route('/octopart_info/by_ppn', methods=['GET'])
def octopart_info_by_ppn():
    """按 ppn 查询 t_octopart_info 最新记录(按 update_time 倒序取第一条),返回 stock_data 解析后的库存波动点位。
    查询参数:
      - ppn: PPN 型号 (必填)
    返回: { code, data: { points: [{date, stock}, ...], update_time } | null }
    (stock_data 为 JSON 字符串 [{"date":"September 10, 2024","totalInventory":15332}, ...],逐条解析为点位)
    """
    ppn = request.args.get('ppn', '').strip()
    if not ppn:
        return error_response('ppn 不能为空', 400)

    try:
        engine = db.engine
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT stock_data, update_time
                FROM t_octopart_info
                WHERE ppn = :ppn
                ORDER BY update_time DESC
                LIMIT 1
            """), {'ppn': ppn}).fetchone()

            if not row:
                return jsonify({'code': 200, 'message': 'Success', 'data': None}), 200

            # 解析 stock_data JSON → [{date, stock}](复用 _parse_stock_points,与 /ppn_result/detail 一致)
            data = {
                'points': _parse_stock_points(row[0]),
                'update_time': row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else None,
            }
            return jsonify({'code': 200, 'message': 'Success', 'data': data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f'查询 octopart_info 失败: {str(e)}', 500)


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


@data_bp.route('/digikey_attr/by_ppn', methods=['GET'])
def digikey_attr_by_ppn():
    """按 ppn 查询 t_digikey_attr 最新记录(按 update_time 倒序取第一条),返回 category 等属性。
    查询参数:
      - ppn: PPN 型号 (必填)
    返回: { code, data: { category, update_time } | null }
    (category 为多行层级字符串,前端按 \n 拆分为 分类/子分类/系列 展示)
    """
    ppn = request.args.get('ppn', '').strip()
    if not ppn:
        return error_response('ppn 不能为空', 400)

    try:
        engine = db.engine
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT category, update_time
                FROM t_digikey_attr
                WHERE ppn = :ppn
                ORDER BY update_time DESC
                LIMIT 1
            """), {'ppn': ppn}).fetchone()

            if not row:
                return jsonify({'code': 200, 'message': 'Success', 'data': None}), 200

            data = {
                'category': row[0] if row[0] else None,
                'update_time': row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else None,
            }
            return jsonify({'code': 200, 'message': 'Success', 'data': data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f'查询 digikey_attr 失败: {str(e)}', 500)


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
    sql = "REPLACE INTO t_ppn (ppn, manu_id, manu_name, source, note) VALUES (:ppn, :manu_id, :manu_name, :source, :note)"
    success, msg = execute_write(sql, data_list)
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/ppn/read', methods=['GET'])
def ppn_read():
    # 返回完整字段: ppn, manu_id, manu_name, source, note, upload_date
    return handle_table_read('t_ppn', select_cols='ppn, manu_id, manu_name, source, note, upload_date', order_by='ppn')


@data_bp.route('/ppn/with_hq', methods=['GET'])
def ppn_with_hq():
    """
    返回 PPN 列表,附带 HQ_M_AV(月搜索均热)和 HQ_SUP(供给记录数)等指标。
    从 t_ppn_result 宽表查询,支持 SQL 层直接筛选和分页。
    注意:t_ppn_result 的数值字段均为 varchar,筛选时用 CAST 转数值比较。
    查询参数:
      - filter_contend: 过滤条件(如 task_name = "TBomHot")
      - order_by: 排序(默认 ppn)
      - page: 页码(1 起,默认 1)
      - page_count: 每页条数(默认 50)
      - hq_m_av_min: 仅保留 HQ_M_AV >= 该值的记录(可选,不传则不过滤)
      - hq_sup_max: 仅保留 HQ_SUP <= 该值的记录(可选,不传则不过滤)
      - ic_sup_max: 仅保留 IC_SUP <= 该值的记录(可选,不传则不过滤)
      - sort_field: 排序字段(可选,白名单: ppn/manu_name/hq_m_avg/hq_sup_count/hq_stock/ic_sup_count/ic_stock)
      - sort_order: 排序方向 asc/desc(可选,不传或空=不排序)
    返回: { code, data: [...], total: N }
    返回字段: ppn, manu_name, task_name, digikey_status, hq_m_avg, hq_sup_count,
             hq_stock, ic_sup_count, ic_stock, efind_all_sup, wheat_global, wheat_ru,
             oc_price, oc_stock
    """
    import re
    filter_contend = request.args.get('filter_contend', '').strip()
    page_str = request.args.get('page', '1').strip()
    page_count_str = request.args.get('page_count', '50').strip()
    hq_m_av_min_str = request.args.get('hq_m_av_min', '').strip()
    hq_sup_max_str = request.args.get('hq_sup_max', '').strip()
    ic_sup_max_str = request.args.get('ic_sup_max', '').strip()
    sort_field = request.args.get('sort_field', '').strip()
    sort_order = request.args.get('sort_order', '').strip().lower()

    # 解析分页参数
    try:
        page = int(page_str) if page_str else 1
        page_count = int(page_count_str) if page_count_str else 50
        if page < 1:
            page = 1
        if page_count < 1:
            page_count = 50
    except (ValueError, TypeError):
        return error_response('page / page_count 必须是正整数', 400)

    # 解析 HQ/IC 筛选参数
    hq_m_av_min = None
    hq_sup_max = None
    ic_sup_max = None
    try:
        if hq_m_av_min_str:
            hq_m_av_min = float(hq_m_av_min_str)
        if hq_sup_max_str:
            hq_sup_max = int(hq_sup_max_str)
        if ic_sup_max_str:
            ic_sup_max = int(ic_sup_max_str)
    except (ValueError, TypeError):
        return error_response('hq_m_av_min / hq_sup_max / ic_sup_max 必须是数字', 400)

    # 排序字段白名单(防止 SQL 注入)
    # 数值字段用 CAST 保证 varchar 列正确排序
    # 每个 tuple: (列名, CAST 类型) → 用于生成"空值最后"前导排序 + 主排序
    SORTABLE_FIELDS = {
        'ppn': ('ppn', None),
        'manu_name': ('manu_name', None),
        'hq_m_avg': ('hq_m_avg', 'DECIMAL(10,2)'),
        'hq_sup_count': ('hq_sup_count', 'SIGNED'),
        'hq_stock': ('hq_stock', 'SIGNED'),
        'ic_sup_count': ('ic_sup_count', 'SIGNED'),
        'ic_stock': ('ic_stock', 'SIGNED'),
    }
    order_clause = ''
    if sort_field and sort_field in SORTABLE_FIELDS:
        col_name, cast_type = SORTABLE_FIELDS[sort_field]
        # "空值最后":CASE 把 NULL/空串映射为 1,非空映射为 0,ASC 排序让非空(0)在前
        # 注意 MySQL 中 CAST('' AS SIGNED) 会变 0,空串与数值 0 混淆,所以先用 CASE 隔离
        null_last_expr = f"CASE WHEN ({col_name} IS NULL OR TRIM({col_name})='') THEN 1 ELSE 0 END"
        main_expr = f"CAST({col_name} AS {cast_type})" if cast_type else col_name
        if sort_order == 'asc':
            order_clause = f' ORDER BY {null_last_expr} ASC, {main_expr} ASC'
        elif sort_order == 'desc':
            # 降序时前导表达式仍用 ASC,确保空值始终排最后(不受主排序方向影响)
            order_clause = f' ORDER BY {null_last_expr} ASC, {main_expr} DESC'
        # 其他值或空=不排序

    try:
        engine = db.engine
        with engine.connect() as conn:
            # 构建 WHERE 条件
            where_clauses = []
            params = {}

            # 从 filter_contend 解析 task_name 过滤
            m = re.search(r'task_name\s*=\s*[\"\']([^\"\']+)[\"\']', filter_contend)
            if m:
                where_clauses.append("task_name = :task_name")
                params['task_name'] = m.group(1)

            # HQ_M_AV 筛选:varchar 字段必须 CAST AS DECIMAL 才能数值比较
            if hq_m_av_min is not None:
                where_clauses.append("CAST(hq_m_avg AS DECIMAL(10,2)) >= :hq_m_av_min")
                params['hq_m_av_min'] = hq_m_av_min

            # HQ_SUP 筛选:varchar 字段必须 CAST AS SIGNED 才能数值比较(<= 小于等于)
            if hq_sup_max is not None:
                where_clauses.append("CAST(hq_sup_count AS SIGNED) <= :hq_sup_max")
                params['hq_sup_max'] = hq_sup_max

            # IC_SUP 筛选:varchar 字段必须 CAST AS SIGNED 才能数值比较(<= 小于等于)
            if ic_sup_max is not None:
                where_clauses.append("CAST(ic_sup_count AS SIGNED) <= :ic_sup_max")
                params['ic_sup_max'] = ic_sup_max

            # 组合 WHERE 子句
            where_sql = ""
            if where_clauses:
                where_sql = " WHERE " + " AND ".join(where_clauses)

            # 计算总数
            count_sql = f"SELECT COUNT(*) FROM t_ppn_result{where_sql}"
            total = conn.execute(text(count_sql), params).scalar() or 0

            # 分页查询(字段顺序与表结构一致,首位 id 用于收藏功能定位记录)
            offset = (page - 1) * page_count
            query_sql = f"""
                SELECT id, ppn, manu_name, task_name, digikey_status,
                       hq_m_avg, hq_sup_count, hq_stock,
                       ic_sup_count, ic_stock, efind_all_sup,
                       wheat_global, wheat_ru, oc_price, oc_stock
                FROM t_ppn_result
                {where_sql}
                {order_clause}
                LIMIT :limit OFFSET :offset
            """
            params['limit'] = page_count
            params['offset'] = offset

            rows = conn.execute(text(query_sql), params).fetchall()

            # 转换为列表格式(varchar 转数值,便于前端显示)
            def _to_float(v):
                try:
                    return float(v) if v is not None and str(v).strip() != '' else 0
                except (ValueError, TypeError):
                    return 0

            def _to_int(v):
                try:
                    return int(float(v)) if v is not None and str(v).strip() != '' else 0
                except (ValueError, TypeError):
                    return 0

            result = []
            for row in rows:
                result.append({
                    'id': row[0],  # t_ppn_result 主键,收藏功能定位记录用
                    'ppn': row[1],
                    'manu_name': row[2] or '',
                    'task_name': row[3] or '',
                    'digikey_status': row[4] or '',
                    'hq_m_avg': _to_float(row[5]),
                    'hq_sup_count': _to_int(row[6]),
                    'hq_stock': _to_int(row[7]),
                    'ic_sup_count': _to_int(row[8]),
                    'ic_stock': _to_int(row[9]),
                    'efind_all_sup': _to_int(row[10]),
                    'wheat_global': _to_int(row[11]),
                    'wheat_ru': _to_int(row[12]),
                    'oc_price': row[13] if row[13] else None,  # 价格保留原值(已含货币单位)
                    'oc_stock': _to_int(row[14]),
                })

            return jsonify({'code': 200, 'message': 'Success', 'data': result, 'total': total}), 200
    except Exception as e:
        return error_response(str(e), 500)


@data_bp.route('/ppn/count_by_source', methods=['GET'])
def ppn_count_by_source():
    """返回每个 source 的 PPN 数量统计,用于任务列表显示型号数"""
    try:
        sql = "SELECT source, COUNT(*) FROM t_ppn GROUP BY source"
        success, result = execute_query(sql, return_dict=False)
        if not success:
            return error_response(result, 500)
        # 转成 { source: count } 字典
        count_map = {row[0]: row[1] for row in result}
        return success_response(data=count_map)
    except Exception as e:
        return error_response(str(e), 500)


@data_bp.route('/ppn/delete', methods=['POST'])
def ppn_delete():
    """批量删除 PPN。请求体: [{ppn, manu_name}, ...]"""
    data_list = request.json if isinstance(request.json, list) else [request.json]
    if not data_list:
        return error_response('删除数据不能为空', 400)
    try:
        engine = db.engine
        with engine.connect() as conn:
            with conn.begin():
                for row in data_list:
                    if not row.get('ppn') or not row.get('manu_name'):
                        continue
                    conn.execute(text(
                        "DELETE FROM t_ppn WHERE ppn = :ppn AND manu_name = :manu_name"
                    ), {'ppn': row['ppn'], 'manu_name': row['manu_name']})
        return success_response(message=f'成功删除 {len(data_list)} 条 PPN')
    except Exception as e:
        return error_response(str(e), 500)


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

    # 登录成功,更新 last_login_date 为当前时间
    try:
        update_sql = "UPDATE t_user SET last_login_date = NOW() WHERE id = :uid"
        execute_write(update_sql, [{'uid': user['id']}])
    except Exception as e:
        # 更新失败不阻塞登录流程,仅记录日志
        print(f'[user/login] 更新 last_login_date 失败: {e}')

    # 重新查询用户数据(包含更新后的 last_login_date)
    success2, result2 = execute_query(
        "SELECT id, username, role, "
        "DATE_FORMAT(last_login_date, '%Y-%m-%d %H:%i:%s') as last_login_date, "
        "DATE_FORMAT(create_time, '%Y-%m-%d %H:%i:%s') as create_time "
        "FROM t_user WHERE id = :uid",
        {'uid': user['id']}, return_dict=True
    )
    if success2 and len(result2) > 0:
        user = result2[0]
    else:
        # 兜底:从原数据中删除 password 字段
        if 'password' in user:
            del user['password']

    return success_response(data=user, message='登录成功')


# ==================== monitor_market 数据库接口 (bind='monitor') ====================

# ---------- monitor_ic 表 ----------

@data_bp.route('/monitor_ic/read', methods=['GET'])
def monitor_ic_read():
    """查询 monitor_ic 表"""
    try:
        where, params = build_where_clause(request.args.to_dict())
        sql = f"SELECT st_ppn, st_manu, supplier, sup_ppn, sup_manu, sup_stock, m_date FROM monitor_ic{where}"
        success, result = execute_query(sql, params, bind='monitor')
        return success_response(data=result) if success else error_response(result, 500)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


@data_bp.route('/monitor_ic/write', methods=['POST'])
def monitor_ic_write():
    """写入 monitor_ic 表（主键冲突时更新）"""
    data_list = request.json if isinstance(request.json, list) else [request.json]
    columns = ['st_ppn', 'st_manu', 'supplier', 'sup_ppn', 'sup_manu', 'sup_stock', 'm_date']
    success, msg = execute_write_upsert(
        'monitor_ic', columns, data_list,
        ['sup_ppn', 'sup_manu', 'sup_stock'], bind='monitor'
    )
    return success_response(message=msg) if success else error_response(msg, 500)


# ---------- IC_supplier_info 表 ----------

@data_bp.route('/ic_supplier_info/read', methods=['GET'])
def ic_supplier_info_read():
    """查询 IC_supplier_info 表"""
    try:
        where, params = build_where_clause(request.args.to_dict())
        sql = f"SELECT id, name, age, address, hot, qq, tel, phone FROM IC_supplier_info{where}"
        success, result = execute_query(sql, params, bind='monitor')
        return success_response(data=result) if success else error_response(result, 500)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


@data_bp.route('/ic_supplier_info/write', methods=['POST'])
def ic_supplier_info_write():
    """写入 IC_supplier_info 表（name唯一键冲突时更新）"""
    data_list = request.json if isinstance(request.json, list) else [request.json]
    columns = ['name', 'age', 'address', 'hot', 'qq', 'tel', 'phone']
    success, msg = execute_write_upsert(
        'IC_supplier_info', columns, data_list,
        ['age', 'address', 'hot', 'qq', 'tel', 'phone'], bind='monitor'
    )
    return success_response(message=msg) if success else error_response(msg, 500)


# ==================== tender_info 数据库接口 (bind='tender') ====================

# t_rts_tender_a 和 t_rts_tender_b 字段完全相同
_TENDER_COLUMNS = [
    'No', 'title_ru', 'starting_price', 'application_security', 'contract_security',
    'status', 'published', 'apply_data', 'show_data', 'org_name', 'org_TinKpp',
    'org_contact', 'cus_name', 'cus_TinKppReg', 'cus_contact', 'cus_address',
    'detail_url', 'page', 'update_time'
]
_TENDER_SELECT = ', '.join([f'`{c}`' for c in _TENDER_COLUMNS])


@data_bp.route('/rts_tender_a/read', methods=['GET'])
def rts_tender_a_read():
    """查询 t_rts_tender_a 表"""
    try:
        where, params = build_where_clause(request.args.to_dict())
        sql = f"SELECT {_TENDER_SELECT} FROM t_rts_tender_a{where}"
        success, result = execute_query(sql, params, bind='tender')
        return success_response(data=result) if success else error_response(result, 500)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


@data_bp.route('/rts_tender_a/write', methods=['POST'])
def rts_tender_a_write():
    """写入 t_rts_tender_a 表（无主键，直接INSERT）"""
    data_list = request.json if isinstance(request.json, list) else [request.json]
    col_str = ', '.join([f'`{c}`' for c in _TENDER_COLUMNS])
    val_str = ', '.join([f':{c}' for c in _TENDER_COLUMNS])
    sql = f"INSERT INTO t_rts_tender_a ({col_str}) VALUES ({val_str})"
    success, msg = execute_write(sql, data_list, bind='tender')
    return success_response(message=msg) if success else error_response(msg, 500)


@data_bp.route('/rts_tender_b/read', methods=['GET'])
def rts_tender_b_read():
    """查询 t_rts_tender_b 表"""
    try:
        where, params = build_where_clause(request.args.to_dict())
        sql = f"SELECT {_TENDER_SELECT} FROM t_rts_tender_b{where}"
        success, result = execute_query(sql, params, bind='tender')
        return success_response(data=result) if success else error_response(result, 500)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)


@data_bp.route('/rts_tender_b/write', methods=['POST'])
def rts_tender_b_write():
    """写入 t_rts_tender_b 表（无主键，直接INSERT）"""
    data_list = request.json if isinstance(request.json, list) else [request.json]
    col_str = ', '.join([f'`{c}`' for c in _TENDER_COLUMNS])
    val_str = ', '.join([f':{c}' for c in _TENDER_COLUMNS])
    sql = f"INSERT INTO t_rts_tender_b ({col_str}) VALUES ({val_str})"
    success, msg = execute_write(sql, data_list, bind='tender')
    return success_response(message=msg) if success else error_response(msg, 500)


# ============================================================================
# PPN Result Excel 上传/解析
# ============================================================================

def _read_excel_sheet(filepath, sheet_name, **kwargs):
    """安全读取 Excel sheet,返回 list[dict] (空单元格用 None)"""
    import pandas as pd
    import math
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl', **kwargs)
        # 把 nan / NaN 全部转成 None,避免后续判空失效
        df = df.astype(object).where(df.notna(), None)
        rows = df.to_dict('records')
        # 防御性清理:任何残留的 float('nan') 转 None
        cleaned = []
        for r in rows:
            clean_row = {}
            for k, v in r.items():
                if isinstance(v, float) and math.isnan(v):
                    clean_row[k] = None
                else:
                    clean_row[k] = v
            cleaned.append(clean_row)
        return cleaned
    except Exception:
        return []


def _to_str(val):
    """将任意值安全转为字符串(varchar 列存储)"""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _to_float(val):
    """将任意值安全转为 float (供前端显示用)"""
    if val is None:
        return 0
    try:
        return round(float(str(val).replace(',', '')), 2)
    except (ValueError, TypeError):
        return 0


def _to_int(val):
    """将任意值安全转为 int"""
    if val is None:
        return 0
    try:
        return int(float(str(val).replace(',', '')))
    except (ValueError, TypeError):
        return 0


@data_bp.route('/ppn_result/upload', methods=['POST'])
def ppn_result_upload():
    """
    上传 Excel 文件解析并导入 t_ppn_result 表。
    Excel 多 sheet 映射规则:
      ppn:           sheet "ppn",         col1=ppn, col2=manu_name, col3=digikey_status
      hq_m_avg:      sheet "HQ_hot_result", col7 (index 6)
      hq_sup_count:  sheet "HQ_stock_sum",  col3 (index 2)
      hq_stock:      sheet "HQ_stock_sum",  col4 (index 3)
      ic_sup_count:  sheet "IC_stock_sum",  col3 (index 2)
      ic_stock:      sheet "IC_stock_sum",  col5 (index 4)
      efind_all_sup: sheet "efind_supplier", col3 (index 2)
      wheat_global:  sheet "wheat_record",   col2 (index 1)
      wheat_ru:      sheet "wheat_record",   col3 (index 2)
      oc_price:      sheet "octopart",       col by name "oc_price" or 搜索 price 列
      oc_stock:      sheet "octopart",       col5 (index 4)
    表单参数:
      - file: Excel 文件(.xlsx)
      - task_name: 关联任务名(必填)
      - confirm: 'true'/'false'(默认 false,仅预览)
    """
    import os
    import tempfile

    # --- 参数校验 ---
    if 'file' not in request.files:
        return error_response('未上传文件', 400)
    file = request.files['file']
    if not file or not file.filename.endswith(('.xlsx', '.xls')):
        return error_response('请上传 .xlsx 或 .xls 文件', 400)

    task_name = (request.form.get('task_name') or '').strip()
    if not task_name:
        return error_response('task_name(任务名)不能为空', 400)

    confirm = (request.form.get('confirm') or 'false').lower() == 'true'

    # --- 保存到临时文件 ---
    tmpdir = tempfile.mkdtemp(prefix='ppn_result_')
    tmp_path = os.path.join(tmpdir, file.filename)
    try:
        file.save(tmp_path)

        # ================================================================
        # Step 1: 解析 ppn sheet (基础数据)
        # ================================================================
        ppn_rows = _read_excel_sheet(tmp_path, 'ppn', header=None)
        if not ppn_rows:
            # 尝试带表头读取
            ppn_rows = _read_excel_sheet(tmp_path, 'ppn')
            if ppn_rows:
                # 把 DataFrame 格式转成按位置的列表
                ppn_rows = [[r.get(f'Unnamed: {i}') for i in range(5)] for r in ppn_rows]

        # 归一化:取 col1=ppn, col2=manu_name, col3=digikey_status
        base_map = {}  # ppn_key -> { ppn, manu_name, digikey_status }
        for row in ppn_rows:
            ppn_val = _to_str(row[0] if isinstance(row, (list, tuple)) else row.get(0))
            if not ppn_val:
                continue
            manu = _to_str(row[1] if isinstance(row, (list, tuple)) else row.get(1))
            dk = _to_str(row[2] if isinstance(row, (list, tuple)) else row.get(2))
            key = ppn_val.lower().strip()
            base_map[key] = {
                'ppn': ppn_val.strip(),
                'manu_name': manu,
                'digikey_status': dk,
            }

        if not base_map:
            return error_response('ppn sheet 为空或无有效数据', 400)

        # ================================================================
        # Step 2: 解析各指标 sheet,按 ppn 合并
        # ================================================================

        # Helper: 按 col index 读取 ppn -> value 映射
        def _read_col_map(sheet_name, ppn_col_idx, val_col_idx):
            """读取指定 sheet,返回 {ppn_lower: value}
            行格式兼容 dict (pandas to_dict('records')) 和 list"""
            rows = _read_excel_sheet(tmp_path, sheet_name, header=None)
            result = {}
            for row in rows:
                # 兼容 dict (pandas 默认) 或 list
                if isinstance(row, dict):
                    ppn = _to_str(row.get(ppn_col_idx))
                    val = row.get(val_col_idx)
                elif isinstance(row, (list, tuple)):
                    ppn = _to_str(row[ppn_col_idx]) if len(row) > ppn_col_idx else None
                    val = row[val_col_idx] if len(row) > val_col_idx else None
                else:
                    continue
                if ppn and val is not None:
                    result[ppn.lower().strip()] = val
            return result

        # HQ_hot_result: ppn(col0), hq_m_avg(col6=第7列)
        hq_m_avg_map = _read_col_map('HQ_hot_result', 0, 6)

        # HQ_stock_sum: ppn(col0), hq_sup_count(col2=第3列), hq_stock(col3=第4列)
        hq_sup_map = _read_col_map('HQ_stock_sum', 0, 2)
        hq_stock_map = _read_col_map('HQ_stock_sum', 0, 3)

        # IC_stock_sum: ppn(col0), ic_sup_count(col2=第3列), ic_stock(col4=第5列)
        ic_sup_map = _read_col_map('IC_stock_sum', 0, 2)
        ic_stock_map = _read_col_map('IC_stock_sum', 0, 4)

        # efind_supplier: ppn(col0), efind_all_sup(col2=第3列)
        efind_map = _read_col_map('efind_supplier', 0, 2)

        # wheat_record: ppn(col0), wheat_global(col1=第2列), wheat_ru(col2=第3列)
        wheat_global_map = _read_col_map('wheat_record', 0, 1)
        wheat_ru_map = _read_col_map('wheat_record', 0, 2)

        # octopart: ppn(col0=第1列), oc_stock(col4=第5列),
        # oc_price = 第6列(货币单位, index 5) + 第7列(货币数值, index 6) 合并
        # 例如: "USD" + "2.45" → "USD 2.45"
        oc_rows = _read_excel_sheet(tmp_path, 'octopart', header=None)
        oc_stock_map = {}
        oc_price_map = {}
        for row in oc_rows:
            # 兼容 dict (pandas 默认) 或 list
            if isinstance(row, dict):
                ppn = _to_str(row.get(0))
                oc_stock_val = row.get(4)
                currency = _to_str(row.get(5))
                price_val = row.get(6)
            elif isinstance(row, (list, tuple)):
                ppn = _to_str(row[0]) if len(row) > 0 else None
                oc_stock_val = row[4] if len(row) > 4 else None
                currency = _to_str(row[5]) if len(row) > 5 else None
                price_val = row[6] if len(row) > 6 else None
            else:
                continue
            if not ppn:
                continue
            ppn_key = ppn.lower().strip()
            # oc_stock: 第5列 (index 4)
            if oc_stock_val is not None:
                oc_stock_map[ppn_key] = oc_stock_val
            # oc_price: 货币单位(第6列) + 货币数值(第7列) 合并
            # 任一非空才记录;数值列转 float 清理(去掉千分位/货币符号),再拼字符串
            if price_val is not None:
                price_num = _to_float(price_val)  # 清理千分位/符号,转 float
                if currency:
                    oc_price_map[ppn_key] = f"{currency} {price_num}"
                else:
                    oc_price_map[ppn_key] = str(price_num)
            elif currency:
                # 只有货币单位无数值,仅记录单位
                oc_price_map[ppn_key] = currency

        # ================================================================
        # Step 3: 合并所有数据,构建待写入列表
        # ================================================================
        merged = []
        warnings = []
        for key, base in base_map.items():
            ppn = base['ppn']
            merged.append({
                'ppn': ppn,
                'manu_name': base['manu_name'],
                'digikey_status': base['digikey_status'],
                'hq_m_avg': _to_str(_to_float(hq_m_avg_map.get(key))),
                'hq_sup_count': _to_str(_to_int(hq_sup_map.get(key))),
                'hq_stock': _to_str(_to_int(hq_stock_map.get(key, 0))),
                'ic_sup_count': _to_str(_to_int(ic_sup_map.get(key))),
                'ic_stock': _to_str(_to_int(ic_stock_map.get(key, 0))),
                'efind_all_sup': _to_str(_to_int(efind_map.get(key, 0))),
                'wheat_global': _to_str(_to_int(wheat_global_map.get(key))),
                'wheat_ru': _to_str(_to_int(wheat_ru_map.get(key))),
                'oc_price': _to_str(oc_price_map.get(key)),  # 已是 "USD 2.45" 格式字符串,不再转 float
                'oc_stock': _to_str(_to_int(oc_stock_map.get(key, 0))),
                'task_name': task_name,
            })

        # 统计各指标覆盖率
        coverage = {
            'total_ppn': len(merged),
            'with_hq_m_avg': sum(1 for r in merged if r['hq_m_avg'] not in (None, '0', '')),
            'with_hq_stock': sum(1 for r in merged if r['hq_stock'] not in (None, '0', '')),
            'with_ic_stock': sum(1 for r in merged if r['ic_stock'] not in (None, '0', '')),
            'with_oc_price': sum(1 for r in merged if r['oc_price'] not in (None, '0', '')),
        }

        if coverage['with_hq_m_avg'] == 0 and len(merged) > 0:
            warnings.append('HQ_hot_result sheet 未匹配到任何 PPN 的 hq_m_avg,请检查列位置')
        if coverage['with_hq_stock'] == 0 and len(merged) > 0:
            warnings.append('HQ_stock_sum sheet 未匹配到任何 PPN 的 hq_stock,请检查列位置')
        if coverage['with_ic_stock'] == 0 and len(merged) > 0:
            warnings.append('IC_stock_sum sheet 未匹配到任何 PPN 的 ic_stock,请检查列位置')

        # 仅预览:返回前 50 条 + 统计
        if not confirm:
            preview_sample = merged[:50]
            return success_response(data={
                'mode': 'preview',
                'total_count': len(merged),
                'coverage': coverage,
                'warnings': warnings,
                'sample': preview_sample,
            }, message=f'解析成功,共 {len(merged)} 条,请确认后写入')

        # ================================================================
        # Step 4: 确认写入 — 纯 UPSERT (ON DUPLICATE KEY UPDATE)
        # 不删除旧数据:同 (ppn, manu_name, task_name) 的记录被新数据替换,
        # 其余旧记录(同 task 下不同 ppn,或不同 task 的数据)全部保留
        # ================================================================
        engine = db.engine
        columns = ['ppn', 'manu_name', 'digikey_status', 'hq_m_avg', 'hq_sup_count',
                   'hq_stock', 'ic_sup_count', 'ic_stock', 'efind_all_sup',
                   'wheat_global', 'wheat_ru', 'oc_price', 'oc_stock', 'task_name']
        col_str = ', '.join(columns)
        val_str = ', '.join([f':{c}' for c in columns])
        # 冲突键: uk_ppn_manu_task (ppn, manu_name, task_name) → 其余列参与 UPDATE
        conflict_cols = [c for c in columns if c not in ('ppn', 'manu_name', 'task_name')]
        update_str = ', '.join([f'{c}=VALUES({c})' for c in conflict_cols])
        upsert_sql = f"INSERT INTO t_ppn_result ({col_str}) VALUES ({val_str}) ON DUPLICATE KEY UPDATE {update_str}"

        batch_size = 500
        written = 0
        with engine.connect() as conn:
            with conn.begin():
                # 不再 DELETE:旧数据保留,仅同键记录被 UPSERT 替换
                for i in range(0, len(merged), batch_size):
                    batch = merged[i:i + batch_size]
                    conn.execute(text(upsert_sql), batch)
                    written += len(batch)

        return success_response(data={
            'mode': 'confirm',
            'written_count': written,
            'coverage': coverage,
            'warnings': warnings,
        }, message=f'成功导入 {written} 条 PPN 指标数据')

    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f'解析失败: {str(e)}', 500)
    finally:
        # 清理临时文件
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            os.rmdir(tmpdir)
        except Exception:
            pass


@data_bp.route('/ppn_store/check', methods=['GET'])
def ppn_store_check():
    """批量查询当前用户已收藏的 PPN 记录 id 列表
    查询参数:
      - user_id: 用户 id (必填,来自 t_user.id)
      - ppn_ids: 逗号分隔的 t_ppn_result.id 列表 (必填)
    返回: { code, data: { collected_ids: [1, 3, ...] } }
    """
    user_id_str = request.args.get('user_id', '').strip()
    ppn_ids_str = request.args.get('ppn_ids', '').strip()

    if not user_id_str or not ppn_ids_str:
        return error_response('user_id 和 ppn_ids 不能为空', 400)

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return error_response('user_id 必须是整数', 400)

    # 解析 ppn_ids (逗号分隔,容错空格/空项)
    try:
        ppn_ids = [int(x.strip()) for x in ppn_ids_str.split(',') if x.strip()]
    except (ValueError, TypeError):
        return error_response('ppn_ids 必须是整数列表', 400)

    if not ppn_ids:
        return jsonify({'code': 200, 'message': 'Success', 'data': {'collected_ids': []}}), 200

    try:
        engine = db.engine
        with engine.connect() as conn:
            # 批量查询:返回该用户已收藏的 ppn_id 列表
            sql = text("""
                SELECT ppn_id FROM t_ppn_store
                WHERE user_id = :user_id AND ppn_id IN :ppn_ids
            """)
            # SQLAlchemy text bind IN 需用 expanding bindparam
            from sqlalchemy import bindparam
            sql = sql.bindparams(
                bindparam('user_id', value=user_id),
                bindparam('ppn_ids', expanding=True),
            )
            rows = conn.execute(sql, {'ppn_ids': ppn_ids}).fetchall()
            collected_ids = [r[0] for r in rows]
            return jsonify({
                'code': 200,
                'message': 'Success',
                'data': {'collected_ids': collected_ids},
            }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f'查询收藏状态失败: {str(e)}', 500)


@data_bp.route('/ppn_store/toggle', methods=['POST'])
def ppn_store_toggle():
    """切换收藏状态 (已收藏 → 取消, 未收藏 → 收藏)
    请求体 JSON:
      - user_id: 用户 id (必填)
      - ppn_id: t_ppn_result.id (必填)
      - note: 用户评价 (可选)
    返回: { code, data: { collected: true/false }, message }
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    ppn_id = data.get('ppn_id')
    note = data.get('note')

    if not user_id or not ppn_id:
        return error_response('user_id 和 ppn_id 不能为空', 400)

    try:
        user_id = int(user_id)
        ppn_id = int(ppn_id)
    except (ValueError, TypeError):
        return error_response('user_id 和 ppn_id 必须是整数', 400)

    try:
        engine = db.engine
        with engine.connect() as conn:
            with conn.begin():
                # 先查是否已收藏
                existing = conn.execute(
                    text("SELECT id FROM t_ppn_store WHERE user_id = :uid AND ppn_id = :pid"),
                    {'uid': user_id, 'pid': ppn_id}
                ).fetchone()

                if existing:
                    # 已收藏 → 取消收藏
                    conn.execute(
                        text("DELETE FROM t_ppn_store WHERE user_id = :uid AND ppn_id = :pid"),
                        {'uid': user_id, 'pid': ppn_id}
                    )
                    return success_response(
                        data={'collected': False},
                        message='已取消收藏'
                    )
                else:
                    # 未收藏 → 添加收藏
                    conn.execute(
                        text("INSERT INTO t_ppn_store (ppn_id, user_id, note) VALUES (:pid, :uid, :note)"),
                        {'pid': ppn_id, 'uid': user_id, 'note': note}
                    )
                    return success_response(
                        data={'collected': True},
                        message='收藏成功'
                    )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f'切换收藏失败: {str(e)}', 500)


def compute_score(hq_m_avg, hq_sup, ic_sup):
    """计算综合得分(0~100,及格线 60)。原子化函数,供 /ppn_result/detail 等复用。

    输入(数值;None 或 0 均视为"未爬取到数据",按及格线基准中性处理,0 加减分):
      - hq_m_avg: 华强月度搜索指数均值(float)——主导项,越大分越高
      - hq_sup:   华强供应商数(int)——越小分越高(稀缺性),重要性最低
      - ic_sup:   IC交易网供应商数(int)——越小分越高,重要性 ic_sup > hq_sup

    评分规则:
      及格线 60 = hq_m_avg=100 且 hq_sup<=3 且 ic_sup<=5 的边界(满足即及格,更稀缺则 >60)。
      通过区(>=60): 60 起算 + 需求加分 demand_bonus(hq_m_avg 主导,每增 50 加 1,封顶 +40)
                    + 供应商稀缺加分(ic_sup 权重 10 > hq_sup 权重 5,体现重要性排序)。
      硬性不合格(<60):
        - note1: hq_m_avg < 100 → 直接不合格,按 hq_m_avg 线性映射 [0,60)
                  (此时 hq_sup / ic_sup 多半无值)
        - note2: hq_sup > 5     → 直接不合格,60*5/hq_sup(忽略需求/加分,保证不合格)
                  (此时 ic_sup 多半无值)
      保底规则(m>=100 时):供应商过多(hq_sup>5 或 ic_sup 过大)不再把分压到 0,
                           至少保底 50(不合格 D,落在 50~59 区),避免"需求好但供应多"被归零。

    返回: round(score, 2),范围 [0,100];hq_m_avg 为 None 返回 None(前端显示 --)
    """
    if hq_m_avg is None:
        return None

    # 硬性不合格门 1: hq_m_avg < 100(note1)→ 需求不足,线性映射 [0,60)
    if hq_m_avg < 100:
        return round(max(0.0, hq_m_avg / 100 * 60), 2)

    # m >= 100: 需求健康,60 起算 + 需求加分 + 供应商加减分
    demand_bonus = min(40.0, (hq_m_avg - 100) / 50)   # 需求加分:hq_m_avg 主导,每增 50 加 1,封顶 +40
    # 0/None 视为"未爬取到数据",按及格线基准中性处理(避免 0 被当成"0 家供应商"误放大稀缺加分)
    ic = ic_sup if ic_sup else 5            # ic_sup 无值/0 → 5(基准,0 加减分)
    hq = hq_sup if hq_sup else 3            # hq_sup 无值/0 → 3(基准,0 加减分)
    ic_adj = (5 - ic) * 10     # 权重 10(更重要):ic_sup<5 加分,>5 扣分
    hq_adj = (3 - hq) * 5     # 权重 5(次要):hq_sup<3 加分,>3 扣分
    score = 60 + demand_bonus + ic_adj + hq_adj

    # note2: hq_sup > 5 仍判定不合格(<60),取供应商超标线性分(忽略需求,保证不合格)
    if hq_sup is not None and hq_sup > 5:
        score = 60.0 * 5 / hq_sup

    # 保底:m>=100(需求健康)时,供应商过多不再把分压到 0,至少 50(不合格 D,落在 50~59)
    score = max(50.0, score)
    return round(max(0.0, min(100.0, score)), 2)


def compute_grade(score):
    """根据综合得分(0~100)计算物料等级(边界含下不含上)。

    >=90 → A, 80~90 → B, 60~80 → C, <60 → D
    (得分已封顶 100,故 A 档改为 >=90;score 为 None 返回 None → 前端显示 --)
    """
    if score is None:
        return None
    if score >= 90:
        return 'A'
    if score >= 80:
        return 'B'
    if score >= 60:
        return 'C'
    return 'D'


@data_bp.route('/ppn_result/detail', methods=['GET'])
def ppn_result_detail():
    """查询单个 PPN 的聚合详情(一次 DB 往返合并 6 张表,前端无需多次请求)。
    查询参数:
      - ppn: PPN 型号 (必填)
      - task_name: 任务名 (可选,仅作用于 t_ppn_result 精确定位)
    返回: { code, data: { ... } | null }
    合并的表(均按 update_time 倒序取最新一条,LEFT JOIN 缺表字段为 null → 前端 --):
      - t_ppn_result : 基础指标 + 综合得分(score) + 物料等级(grade)
      - t_hq_peakfire : 华强月/周搜索指数(month_hot_array / weak_hot_array + 均值)
      - t_ic_price_demand : IC 月搜索量(month_search_count)
      - t_octopart_info : Octopart 库存波动点位(stock_points)
      - t_digikey_attr : 分类(category,多行层级字符串)
      - t_ppn : source(任务来源)
    综合得分 / 物料等级: 见 compute_score() / compute_grade()(单一数据源,避免重复维护)
    """
    ppn = request.args.get('ppn', '').strip()
    task_name = request.args.get('task_name', '').strip()
    if not ppn:
        return error_response('ppn 不能为空', 400)

    try:
        engine = db.engine
        with engine.connect() as conn:
            # 以 (SELECT :ppn) 为锚保证恒返回 1 行,各关联表取最新记录 LEFT JOIN
            # → 单次查询拿到 t_ppn_result 基础指标 + hq/ic_price/octopart/digikey/ppn 全部关联数据
            tn_clause = "AND task_name = :tn" if task_name else ""
            params = {'ppn': ppn}
            if task_name:
                params['tn'] = task_name

            row = conn.execute(text(f"""
                SELECT
                  r.id, r.ppn, r.manu_name, r.task_name, r.digikey_status,
                  r.hq_m_avg, r.hq_sup_count, r.hq_stock,
                  r.ic_sup_count, r.ic_stock, r.efind_all_sup,
                  r.wheat_global, r.wheat_ru, r.oc_price, r.oc_stock, r.update_time,
                  h.month_hot, h.weak_hot, h.update_time AS hq_update_time,
                  i.month_search_count, i.update_time AS ic_update_time,
                  o.stock_data, o.update_time AS oc_update_time,
                  d.category, d.update_time AS dk_update_time,
                  p2.source
                FROM (SELECT :ppn AS ppn) p
                LEFT JOIN (
                  SELECT id, ppn, manu_name, task_name, digikey_status,
                         hq_m_avg, hq_sup_count, hq_stock,
                         ic_sup_count, ic_stock, efind_all_sup,
                         wheat_global, wheat_ru, oc_price, oc_stock, update_time
                  FROM t_ppn_result
                  WHERE ppn = :ppn {tn_clause}
                  ORDER BY update_time DESC
                  LIMIT 1
                ) r ON r.ppn = p.ppn
                LEFT JOIN (SELECT ppn, month_hot, weak_hot, update_time FROM t_hq_peakfire WHERE ppn = :ppn ORDER BY update_time DESC LIMIT 1) h ON h.ppn = p.ppn
                LEFT JOIN (SELECT ppn, month_search_count, update_time FROM t_ic_price_demand WHERE ppn = :ppn ORDER BY update_time DESC LIMIT 1) i ON i.ppn = p.ppn
                LEFT JOIN (SELECT ppn, stock_data, update_time FROM t_octopart_info WHERE ppn = :ppn ORDER BY update_time DESC LIMIT 1) o ON o.ppn = p.ppn
                LEFT JOIN (SELECT ppn, category, update_time FROM t_digikey_attr WHERE ppn = :ppn ORDER BY update_time DESC LIMIT 1) d ON d.ppn = p.ppn
                LEFT JOIN (SELECT ppn, source FROM t_ppn WHERE ppn = :ppn ORDER BY upload_date DESC LIMIT 1) p2 ON p2.ppn = p.ppn
                LIMIT 1
            """), params).fetchone()

            # 锚点子查询保证恒返回 1 行;若所有表均无记录则各字段为 NULL(前端显示 --)
            if not row:
                return jsonify({'code': 200, 'message': 'Success', 'data': None}), 200

            # varchar → 数值(空值/非数字 → None;0 由前端 formatVal 统一转 --)
            def _to_float(v):
                try:
                    return float(v) if v is not None and str(v).strip() != '' else None
                except (ValueError, TypeError):
                    return None

            def _to_int(v):
                try:
                    return int(float(v)) if v is not None and str(v).strip() != '' else None
                except (ValueError, TypeError):
                    return None

            # 基础指标(t_ppn_result)
            hq_m_avg = _to_float(row[5])
            hq_sup = _to_int(row[6])
            ic_sup = _to_int(row[8])

            # 综合得分 + 物料等级(原子化函数,公式见 compute_score / compute_grade)
            score = compute_score(hq_m_avg, hq_sup, ic_sup)
            grade = compute_grade(score)

            # 关联:t_hq_peakfire 华强月/周搜索指数(int 数组 + 均值)
            month_hot_arr = _parse_int_array(row[16])
            weak_hot_arr = _parse_int_array(row[17])
            month_hot_avg = round(sum(month_hot_arr) / len(month_hot_arr), 2) if month_hot_arr else None
            weak_hot_avg = round(sum(weak_hot_arr) / len(weak_hot_arr), 2) if weak_hot_arr else None

            # 关联:t_octopart_info 库存波动点位(JSON → [{date, stock}])
            stock_points = _parse_stock_points(row[21])

            data = {
                # --- t_ppn_result 基础指标 + 得分 ---
                'id': row[0],
                'ppn': row[1] or ppn,
                'manu_name': row[2] or '',
                'task_name': row[3] or '',
                'digikey_status': row[4] or '',
                'hq_m_avg': hq_m_avg,
                'hq_sup_count': hq_sup,
                'hq_stock': _to_int(row[7]),
                'ic_sup_count': ic_sup,
                'ic_stock': _to_int(row[9]),
                'efind_all_sup': _to_int(row[10]),
                'wheat_global': _to_int(row[11]),
                'wheat_ru': _to_int(row[12]),
                'oc_price': row[13] if row[13] else None,
                'oc_stock': _to_int(row[14]),
                'update_time': row[15].strftime('%Y-%m-%d') if row[15] else None,
                'score': score,
                'grade': grade,
                # --- t_hq_peakfire 华强月/周搜索指数 ---
                'month_hot_array': month_hot_arr,
                'month_hot_avg': month_hot_avg,
                'weak_hot_array': weak_hot_arr,
                'weak_hot_avg': weak_hot_avg,
                'hq_update_time': row[18].strftime('%Y-%m-%d %H:%M:%S') if row[18] else None,
                # --- t_ic_price_demand IC 月搜索量 ---
                'month_search_count': _to_int(row[19]),
                'ic_update_time': row[20].strftime('%Y-%m-%d %H:%M:%S') if row[20] else None,
                # --- t_octopart_info 库存波动 ---
                'stock_points': stock_points,
                'oc_update_time': row[22].strftime('%Y-%m-%d %H:%M:%S') if row[22] else None,
                # --- t_digikey_attr 分类 ---
                'category': row[23] if row[23] else None,
                'dk_update_time': row[24].strftime('%Y-%m-%d %H:%M:%S') if row[24] else None,
                # --- t_ppn source ---
                'source': row[25] if row[25] else None,
            }
            return jsonify({'code': 200, 'message': 'Success', 'data': data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f'查询详情失败: {str(e)}', 500)
