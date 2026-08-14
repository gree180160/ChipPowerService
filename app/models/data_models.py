from app import db
from datetime import datetime


class Task(db.Model):
    __tablename__ = 't_task'
    __table_args__ = {'extend_existing': True}
    
    TID = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    Tname = db.Column(db.String(200))
    Tdes = db.Column(db.String(256))
    Tstate = db.Column(db.SmallInteger)
    Tlevel = db.Column(db.SmallInteger)
    TstartDate = db.Column(db.DateTime)
    TendDate = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'TID': self.TID,
            'Tname': self.Tname,
            'Tdes': self.Tdes,
            'Tstate': self.Tstate,
            'Tlevel': self.Tlevel,
            'TstartDate': self.TstartDate.strftime('%Y-%m-%d %H:%M:%S') if self.TstartDate else None,
            'TendDate': self.TendDate.strftime('%Y-%m-%d %H:%M:%S') if self.TendDate else None
        }


class ICHotM(db.Model):
    __tablename__ = 't_IC_hot_m'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(255))
    manu = db.Column(db.String(255))
    m1 = db.Column(db.Integer)
    m2 = db.Column(db.Integer)
    m3 = db.Column(db.Integer)
    m4 = db.Column(db.Integer)
    m5 = db.Column(db.Integer)
    m6 = db.Column(db.Integer)
    m7 = db.Column(db.Integer)
    m8 = db.Column(db.Integer)
    m9 = db.Column(db.Integer)
    m10 = db.Column(db.Integer)
    m11 = db.Column(db.Integer)
    m12 = db.Column(db.Integer)
    task_name = db.Column(db.String(25))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        data = {'ppn': self.ppn, 'manu': self.manu, 'task_name': self.task_name}
        for i in range(1, 13):
            data[f'm{i}'] = getattr(self, f'm{i}')
        data['update_time'] = self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        return data


class ICHotW(db.Model):
    __tablename__ = 't_IC_hot_w'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(255))
    manu = db.Column(db.String(255))
    w1 = db.Column(db.Integer)
    w2 = db.Column(db.Integer)
    w3 = db.Column(db.Integer)
    w4 = db.Column(db.Integer)
    w5 = db.Column(db.Integer)
    w6 = db.Column(db.Integer)
    w7 = db.Column(db.Integer)
    w8 = db.Column(db.Integer)
    w9 = db.Column(db.Integer)
    w10 = db.Column(db.Integer)
    w11 = db.Column(db.Integer)
    w12 = db.Column(db.Integer)
    w13 = db.Column(db.Integer)
    w14 = db.Column(db.Integer)
    w15 = db.Column(db.Integer)
    w16 = db.Column(db.Integer)
    w17 = db.Column(db.Integer)
    w18 = db.Column(db.Integer)
    w19 = db.Column(db.Integer)
    w20 = db.Column(db.Integer)
    w21 = db.Column(db.Integer)
    w22 = db.Column(db.Integer)
    w23 = db.Column(db.Integer)
    w24 = db.Column(db.Integer)
    w25 = db.Column(db.Integer)
    w26 = db.Column(db.Integer)
    w27 = db.Column(db.Integer)
    w28 = db.Column(db.Integer)
    w29 = db.Column(db.Integer)
    w30 = db.Column(db.Integer)
    w31 = db.Column(db.Integer)
    w32 = db.Column(db.Integer)
    w33 = db.Column(db.Integer)
    w34 = db.Column(db.Integer)
    w35 = db.Column(db.Integer)
    w36 = db.Column(db.Integer)
    w37 = db.Column(db.Integer)
    w38 = db.Column(db.Integer)
    w39 = db.Column(db.Integer)
    w40 = db.Column(db.Integer)
    w41 = db.Column(db.Integer)
    w42 = db.Column(db.Integer)
    w43 = db.Column(db.Integer)
    w44 = db.Column(db.Integer)
    w45 = db.Column(db.Integer)
    w46 = db.Column(db.Integer)
    w47 = db.Column(db.Integer)
    w48 = db.Column(db.Integer)
    w49 = db.Column(db.Integer)
    w50 = db.Column(db.Integer)
    w51 = db.Column(db.Integer)
    w52 = db.Column(db.Integer)
    task_name = db.Column(db.String(25))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        data = {'ppn': self.ppn, 'manu': self.manu, 'task_name': self.task_name}
        for i in range(1, 53):
            data[f'w{i}'] = getattr(self, f'w{i}')
        data['update_time'] = self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        return data


class ICPriceDemand(db.Model):
    __tablename__ = 't_ic_price_demand'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(255))
    manu = db.Column(db.String(255))
    price = db.Column(db.String(10))
    month_search_count = db.Column(db.String(10))
    supplierCount = db.Column(db.String(10))
    cp_count = db.Column(db.String(4))
    rank_count = db.Column(db.String(4))
    task_name = db.Column(db.String(100))
    updata_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu': self.manu, 'price': self.price,
            'month_search_count': self.month_search_count, 'supplierCount': self.supplierCount,
            'cp_count': self.cp_count, 'rank_count': self.rank_count, 'task_name': self.task_name,
            'updata_time': self.updata_time.strftime('%Y-%m-%d %H:%M:%S') if self.updata_time else None
        }


class CXYXStock(db.Model):
    __tablename__ = 't_cxyx_stock'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    supplier_name = db.Column(db.String(100))
    model = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    category = db.Column(db.String(30))
    price_step = db.Column(db.String(200))
    stock_num = db.Column(db.String(13))
    batch_info = db.Column(db.String(50))
    task_name = db.Column(db.String(100))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id, 'supplier_name': self.supplier_name, 'model': self.model,
            'brand': self.brand, 'category': self.category, 'price_step': self.price_step,
            'stock_num': self.stock_num, 'batch_info': self.batch_info, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class ICStock(db.Model):
    __tablename__ = 't_ic_stock'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'st_manu', 'supplier_manu', 'supplier', 'batch', 'pakaging', 'task_name'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(100))
    st_manu = db.Column(db.String(50))
    supplier_ppn = db.Column(db.String(1000))
    supplier_manu = db.Column(db.String(155))
    supplier = db.Column(db.String(255))
    isICCP = db.Column(db.Integer)
    isSSCP = db.Column(db.Integer)
    iSRanking = db.Column(db.Integer)
    isHotSell = db.Column(db.Integer)
    isYouXian = db.Column(db.Integer)
    batch = db.Column(db.String(60))
    pakaging = db.Column(db.String(100))
    stock_num = db.Column(db.Integer)
    task_name = db.Column(db.String(40))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'st_manu': self.st_manu, 'supplier_ppn': self.supplier_ppn,
            'supplier_manu': self.supplier_manu, 'supplier': self.supplier,
            'isICCP': self.isICCP, 'isSSCP': self.isSSCP, 'iSRanking': self.iSRanking,
            'isHotSell': self.isHotSell, 'isYouXian': self.isYouXian, 'batch': self.batch,
            'pakaging': self.pakaging, 'stock_num': self.stock_num, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class ICDes(db.Model):
    __tablename__ = 't_ic_des'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(50))
    manu = db.Column(db.String(255))
    todaySearch = db.Column(db.String(13))
    todaySearch_person = db.Column(db.String(13))
    yesterdaySearch = db.Column(db.String(13))
    yesterdaySearch_person = db.Column(db.String(13))
    reference_price = db.Column(db.String(13))
    week_search = db.Column(db.String(13))
    market_hot = db.Column(db.String(25))
    risk = db.Column(db.String(50))
    mainLand_stock = db.Column(db.String(13))
    international_stock = db.Column(db.String(13))
    task_name = db.Column(db.String(100))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu': self.manu, 'todaySearch': self.todaySearch,
            'todaySearch_person': self.todaySearch_person, 'yesterdaySearch': self.yesterdaySearch,
            'yesterdaySearch_person': self.yesterdaySearch_person, 'reference_price': self.reference_price,
            'week_search': self.week_search, 'market_hot': self.market_hot, 'risk': self.risk,
            'mainLand_stock': self.mainLand_stock, 'international_stock': self.international_stock,
            'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class HQStock(db.Model):
    __tablename__ = 't_hq_stock'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'std_manu', 'supplier', 'sup_ppn', 'sup_manu', 'batch', 'packing'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(50))
    std_manu = db.Column(db.String(100))
    supplier = db.Column(db.String(100))
    sup_ppn = db.Column(db.String(255))
    sup_manu = db.Column(db.String(100))
    batch = db.Column(db.String(50))
    stock = db.Column(db.String(26))
    packing = db.Column(db.String(80))
    param = db.Column(db.String(256))
    place = db.Column(db.String(100))
    instruction = db.Column(db.Text)
    publish_date = db.Column(db.String(100))
    task_name = db.Column(db.String(100))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'std_manu': self.std_manu, 'supplier': self.supplier,
            'sup_ppn': self.sup_ppn, 'sup_manu': self.sup_manu, 'batch': self.batch,
            'stock': self.stock, 'packing': self.packing, 'param': self.param,
            'place': self.place, 'instruction': self.instruction, 'publish_date': self.publish_date,
            'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class HQHot(db.Model):
    __tablename__ = 't_hq_peakfire'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(100))
    manu = db.Column(db.String(50))
    weak_hot = db.Column(db.String(255))
    month_hot = db.Column(db.String(400))
    task_name = db.Column(db.String(50))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu': self.manu, 'weak_hot': self.weak_hot,
            'month_hot': self.month_hot, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class EFindStock(db.Model):
    __tablename__ = 't_efind_stock'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu', 'supplier'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(50))
    manu = db.Column(db.String(100))
    sup_manu = db.Column(db.String(100))
    supplier = db.Column(db.String(255))
    publish_date = db.Column(db.String(255))
    info = db.Column(db.String(256))
    price = db.Column(db.String(100))
    stock = db.Column(db.String(50))
    task_name = db.Column(db.String(50))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu': self.manu, 'sup_manu': self.sup_manu,
            'supplier': self.supplier, 'publish_date': self.publish_date, 'info': self.info,
            'price': self.price, 'stock': self.stock, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class EFindSupplier(db.Model):
    __tablename__ = 't_efind_supplier'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(50))
    manu = db.Column(db.String(100))
    all_supplier = db.Column(db.String(13))
    price_supplier = db.Column(db.String(13))
    stock_supplier = db.Column(db.String(13))
    stock = db.Column(db.String(13))
    middle_price = db.Column(db.String(50))
    min_price = db.Column(db.String(50))
    max_price = db.Column(db.String(50))
    task_name = db.Column(db.String(25))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu': self.manu, 'all_supplier': self.all_supplier,
            'price_supplier': self.price_supplier, 'stock_supplier': self.stock_supplier,
            'stock': self.stock, 'middle_price': self.middle_price, 'min_price': self.min_price,
            'max_price': self.max_price, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class BOMPrice(db.Model):
    __tablename__ = 't_bom_price'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu', 'supplier', 'package'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(100))
    manu = db.Column(db.String(50))
    supplier = db.Column(db.String(255))
    package = db.Column(db.String(255))
    lot = db.Column(db.String(255))
    quoted_price = db.Column(db.String(25))
    release_time = db.Column(db.String(25))
    stock_num = db.Column(db.String(100))
    valid_supplier = db.Column(db.String(255))
    task_name = db.Column(db.String(50))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu': self.manu, 'supplier': self.supplier,
            'package': self.package, 'lot': self.lot, 'quoted_price': self.quoted_price,
            'release_time': self.release_time, 'stock_num': self.stock_num,
            'valid_supplier': self.valid_supplier, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class OctopartPrice(db.Model):
    __tablename__ = 't_octopart_price'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu', 'distribute', 'sku'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(100))
    manu = db.Column(db.String(100))
    is_star = db.Column(db.Integer)
    distribute = db.Column(db.String(255))
    sku = db.Column(db.String(255))
    stock = db.Column(db.String(25))
    moq = db.Column(db.String(25))
    currency_type = db.Column(db.String(5))
    k_price = db.Column(db.String(50))
    updated = db.Column(db.String(25))
    opn = db.Column(db.String(155))
    task_name = db.Column(db.String(25))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu': self.manu, 'is_star': self.is_star,
            'distribute': self.distribute, 'sku': self.sku, 'stock': self.stock,
            'moq': self.moq, 'currency_type': self.currency_type, 'k_price': self.k_price,
            'updated': self.updated, 'opn': self.opn, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class OctopartMarket(db.Model):
    __tablename__ = 't_octopart_market'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(100))
    manu = db.Column(db.String(100))
    des = db.Column(db.Text)
    distribute = db.Column(db.String(100))
    stock = db.Column(db.String(15))
    currency_type = db.Column(db.String(10))
    k_price = db.Column(db.String(100))
    stock_pic = db.Column(db.Text)
    opn = db.Column(db.String(50))
    task_name = db.Column(db.String(50))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu': self.manu, 'des': self.des,
            'distribute': self.distribute, 'stock': self.stock, 'currency_type': self.currency_type,
            'k_price': self.k_price, 'stock_pic': self.stock_pic, 'opn': self.opn,
            'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class OctopartInfo(db.Model):
    __tablename__ = 't_octopart_info'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu', 'task_name'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(100))
    manu = db.Column(db.String(100))
    des = db.Column(db.Text)
    distribute = db.Column(db.String(100))
    stock = db.Column(db.String(25))
    currency_type = db.Column(db.CHAR(10))
    k_price = db.Column(db.String(25))
    opn = db.Column(db.String(100))
    stock_data = db.Column(db.JSON)
    tech_data = db.Column(db.JSON)
    supplier_data = db.Column(db.JSON)
    task_name = db.Column(db.String(100))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu': self.manu, 'des': self.des,
            'distribute': self.distribute, 'stock': self.stock, 'currency_type': self.currency_type,
            'k_price': self.k_price, 'opn': self.opn, 'stock_data': self.stock_data,
            'tech_data': self.tech_data, 'supplier_data': self.supplier_data, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class FindChipStock(db.Model):
    __tablename__ = 't_findchips_stock'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu', 'supplier'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(50))
    manu = db.Column(db.String(100))
    supplier = db.Column(db.String(255))
    authorized = db.Column(db.String(5))
    part_url = db.Column(db.String(255))
    stock_str = db.Column(db.String(13))
    task_name = db.Column(db.String(25))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu': self.manu, 'supplier': self.supplier,
            'authorized': self.authorized, 'part_url': self.part_url, 'stock_str': self.stock_str,
            'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class DigikeyAttr(db.Model):
    __tablename__ = 't_digikey_attr'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    ppn = db.Column(db.String(255))
    manu = db.Column(db.String(255))
    digi_key_code = db.Column(db.String(255))
    manu_code = db.Column(db.String(255))
    des = db.Column(db.String(255))
    delivery_time = db.Column(db.String(50))
    detail_des = db.Column(db.String(250))
    category = db.Column(db.String(100))
    serial = db.Column(db.String(50))
    package = db.Column(db.String(50))
    status = db.Column(db.String(50))
    kind = db.Column(db.String(50))
    single_channel = db.Column(db.String(50))
    voltage_reverse = db.Column(db.String(50))
    voltage_breakdown = db.Column(db.String(50))
    voltage_ipp = db.Column(db.String(50))
    peakCurrentPulse = db.Column(db.String(50))
    peakPowerPulse = db.Column(db.String(50))
    protect_power = db.Column(db.String(50))
    apply = db.Column(db.String(255))
    capacitance = db.Column(db.String(50))
    operating_temperature = db.Column(db.String(50))
    install_kind = db.Column(db.String(50))
    shell = db.Column(db.String(50))
    supplier_packeage = db.Column(db.String(50))
    product_code = db.Column(db.String(255))
    task_name = db.Column(db.String(50))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id, 'ppn': self.ppn, 'manu': self.manu,
            'digi_key_code': self.digi_key_code, 'manu_code': self.manu_code, 'des': self.des,
            'delivery_time': self.delivery_time, 'detail_des': self.detail_des, 'category': self.category,
            'serial': self.serial, 'package': self.package, 'status': self.status, 'kind': self.kind,
            'single_channel': self.single_channel, 'voltage_reverse': self.voltage_reverse,
            'voltage_breakdown': self.voltage_breakdown, 'voltage_ipp': self.voltage_ipp,
            'peakCurrentPulse': self.peakCurrentPulse, 'peakPowerPulse': self.peakPowerPulse,
            'protect_power': self.protect_power, 'apply': self.apply, 'capacitance': self.capacitance,
            'operating_temperature': self.operating_temperature, 'install_kind': self.install_kind,
            'shell': self.shell, 'supplier_packeage': self.supplier_packeage,
            'product_code': self.product_code, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class WheatRecord(db.Model):
    __tablename__ = 't_wheat_record'
    __table_args__ = (
        db.PrimaryKeyConstraint('keyword'),
        {'extend_existing': True}
    )
    
    keyword = db.Column(db.String(100))
    all_records = db.Column(db.String(13))
    ru_records = db.Column(db.String(13))
    update_time = db.Column(db.DateTime)
    task_name = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'keyword': self.keyword, 'all_records': self.all_records, 'ru_records': self.ru_records,
            'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class WheatBuyer(db.Model):
    __tablename__ = 't_wheat_buyer'
    __table_args__ = (
        db.PrimaryKeyConstraint('keyword', 'wheat_date', 'buyer', 'supplier', 'HSCode', 'buy_country', 'supplier_country', 'productContry'),
        {'extend_existing': True}
    )
    
    keyword = db.Column(db.String(50))
    wheat_date = db.Column(db.String(50))
    buyer = db.Column(db.String(150))
    supplier = db.Column(db.String(150))
    HSCode = db.Column(db.String(20))
    description = db.Column(db.Text)
    buy_country = db.Column(db.String(50))
    supplier_country = db.Column(db.String(50))
    productContry = db.Column(db.String(30))
    weight = db.Column(db.String(20))
    number = db.Column(db.String(13))
    totalValue = db.Column(db.String(15))
    current_page = db.Column(db.Integer)
    task_name = db.Column(db.String(50))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'keyword': self.keyword, 'wheat_date': self.wheat_date, 'buyer': self.buyer,
            'supplier': self.supplier, 'HSCode': self.HSCode, 'description': self.description,
            'buy_country': self.buy_country, 'supplier_country': self.supplier_country,
            'productContry': self.productContry, 'weight': self.weight, 'number': self.number,
            'totalValue': self.totalValue, 'current_page': self.current_page, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class Rusprofile(db.Model):
    __tablename__ = 't_rusprofile'
    __table_args__ = (
        db.PrimaryKeyConstraint('company_name'),
        {'extend_existing': True}
    )
    
    company_name = db.Column(db.String(255))
    profile_id = db.Column(db.String(30))
    full_name = db.Column(db.String(255))
    inn = db.Column(db.String(30))
    activity = db.Column(db.Text)
    register_date = db.Column(db.String(255))
    industry_rank = db.Column(db.String(255))
    company_address = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    website = db.Column(db.String(255))
    revenue = db.Column(db.String(100))
    profit = db.Column(db.String(100))
    cost = db.Column(db.String(100))
    task_name = db.Column(db.String(255))
    update_time = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'company_name': self.company_name, 'profile_id': self.profile_id, 'full_name': self.full_name,
            'inn': self.inn, 'activity': self.activity, 'register_date': self.register_date,
            'industry_rank': self.industry_rank, 'company_address': self.company_address,
            'phone': self.phone, 'email': self.email, 'website': self.website,
            'revenue': self.revenue, 'profit': self.profit, 'cost': self.cost, 'task_name': self.task_name,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class FutureInfo(db.Model):
    __tablename__ = 't_futrue'
    __table_args__ = (
        db.PrimaryKeyConstraint('f_ppn', 'f_manu'),
        {'extend_existing': True}
    )
    
    st_part = db.Column(db.String(255))
    st_manu = db.Column(db.String(255))
    f_ppn = db.Column(db.String(255))
    f_manu = db.Column(db.String(255))
    OnOrder = db.Column(db.String(50))
    stock = db.Column(db.String(50))
    leadTime = db.Column(db.String(50))
    unitPrice = db.Column(db.String(50))
    task_name = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'st_part': self.st_part, 'st_manu': self.st_manu, 'f_ppn': self.f_ppn,
            'f_manu': self.f_manu, 'OnOrder': self.OnOrder, 'stock': self.stock,
            'leadTime': self.leadTime, 'unitPrice': self.unitPrice, 'task_name': self.task_name
        }


class ArrowInfo(db.Model):
    __tablename__ = 't_arrow'
    __table_args__ = (
        db.PrimaryKeyConstraint('a_ppn', 'a_manu'),
        {'extend_existing': True}
    )
    
    st_part = db.Column(db.String(250))
    st_manu = db.Column(db.String(250))
    a_ppn = db.Column(db.String(250))
    a_manu = db.Column(db.String(250))
    stock = db.Column(db.String(50))
    leadTime = db.Column(db.String(50))
    price = db.Column(db.String(50))
    batch = db.Column(db.String(20))
    task_name = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'st_part': self.st_part, 'st_manu': self.st_manu, 'a_ppn': self.a_ppn,
            'a_manu': self.a_manu, 'stock': self.stock, 'leadTime': self.leadTime,
            'price': self.price, 'batch': self.batch, 'task_name': self.task_name
        }


class PPN(db.Model):
    __tablename__ = 't_ppn'
    __table_args__ = (
        db.PrimaryKeyConstraint('ppn', 'manu_name'),
        {'extend_existing': True}
    )
    
    ppn = db.Column(db.String(100))
    manu_id = db.Column(db.Integer)
    manu_name = db.Column(db.String(20))
    source = db.Column(db.String(255))
    note = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'ppn': self.ppn, 'manu_id': self.manu_id, 'manu_name': self.manu_name,
            'source': self.source, 'note': self.note
        }


class OPN(db.Model):
    __tablename__ = 't_opn'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    opn = db.Column(db.String(20))
    manu_id = db.Column(db.Integer)
    manu_name = db.Column(db.String(20))
    
    def to_dict(self):
        return {
            'id': self.id, 'opn': self.opn, 'manu_id': self.manu_id, 'manu_name': self.manu_name
        }


class User(db.Model):
    __tablename__ = 't_user'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), default='0')
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'role': self.role,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }
