import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


@pytest.fixture
def app():
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class TestHealthCheck:
    def test_health_check(self, client):
        response = client.get('/api/data/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert data['data']['status'] == 'ok'


class TestTaskAPI:
    def test_write_and_read_task(self, client):
        task_data = {
            'Tname': 'test_task_001',
            'Tdes': '测试任务',
            'Tstate': 'running',
            'Tlevel': 1
        }
        response = client.post('/api/data/task/write', json=task_data)
        assert response.status_code == 200
        
        response = client.get('/api/data/task/read')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 1
        assert data['data'][0]['Tname'] == 'test_task_001'
    
    def test_write_batch_tasks(self, client):
        tasks = [
            {'Tname': 'task1', 'Tdes': '任务1', 'Tstate': 'pending', 'Tlevel': 1},
            {'Tname': 'task2', 'Tdes': '任务2', 'Tstate': 'running', 'Tlevel': 2}
        ]
        response = client.post('/api/data/task/write', json=tasks)
        assert response.status_code == 200
        
        response = client.get('/api/data/task/read?Tstate=running')
        data = json.loads(response.data)
        assert len(data['data']) == 1
        assert data['data'][0]['Tname'] == 'task2'


class TestICHotMAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'TEST-IC-001',
            'manu': 'TestManufacturer',
            'm1': 100.5, 'm2': 200.3, 'm3': 150.0, 'm4': 180.0,
            'm5': 190.0, 'm6': 170.0, 'm7': 160.0, 'm8': 155.0,
            'm9': 140.0, 'm10': 130.0, 'm11': 120.0, 'm12': 110.0,
            'task_name': 'test_task'
        }
        response = client.post('/api/data/ic_hot_m/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/ic_hot_m/read?ppn=TEST-IC-001')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['ppn'] == 'TEST-IC-001'
        assert result['data'][0]['m1'] == 100.5


class TestICHotWAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'TEST-IC-W-001',
            'manu': 'TestManufacturer',
            'task_name': 'test_task'
        }
        for i in range(1, 53):
            data[f'w{i}'] = float(i * 10)
        
        response = client.post('/api/data/ic_hot_w/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/ic_hot_w/read?ppn=TEST-IC-W-001')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['w1'] == 10.0
        assert result['data'][0]['w52'] == 520.0


class TestICPriceDemandAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'DEMAND-001',
            'manu': 'TestManu',
            'price': '¥6.836',
            'month_search_count': 175,
            'supplierCount': 443,
            'cp_count': 10,
            'rank_count': 5,
            'task_name': 'test_demand'
        }
        response = client.post('/api/data/ic_price_demand/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/ic_price_demand/read?ppn=DEMAND-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['price'] == '¥6.836'
        assert result['data'][0]['month_search_count'] == 175


class TestCXYXStockAPI:
    def test_write_and_read(self, client):
        data = {
            'supplier_name': 'TestSupplier',
            'model': 'MODEL-001',
            'brand': 'TestBrand',
            'category': 'IC',
            'price_step': '1-10:¥5.00',
            'stock_num': '1000',
            'batch_info': '2024+',
            'task_name': 'test_cxyx'
        }
        response = client.post('/api/data/cxyx_stock/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/cxyx_stock/read?model=MODEL-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['supplier_name'] == 'TestSupplier'


class TestICStockAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'STOCK-001',
            'st_manu': 'STManu',
            'supplier_ppn': 'SUP-PPN-001',
            'supplier_manu': 'SupManu',
            'supplier': 'TestSupplier',
            'isICCP': True,
            'isSSCP': False,
            'iSRanking': 1,
            'isHotSell': True,
            'isYouXian': False,
            'batch': '2024+',
            'pakaging': 'QFN',
            'stock_num': '5000',
            'task_name': 'test_ic_stock'
        }
        response = client.post('/api/data/ic_stock/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/ic_stock/read?ppn=STOCK-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['isICCP'] == True
        assert result['data'][0]['stock_num'] == '5000'


class TestICDesAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'DES-001',
            'manu': 'DesManu',
            'todaySearch': 100,
            'todaySearch_person': 50,
            'yesterdaySearch': 90,
            'yesterdaySearch_person': 45,
            'reference_price': '¥10.00',
            'week_search': 500,
            'market_hot': 'high',
            'risk': 'low',
            'mainLand_stock': '10000',
            'international_stock': '50000',
            'task_name': 'test_des'
        }
        response = client.post('/api/data/ic_des/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/ic_des/read?ppn=DES-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['todaySearch'] == 100


class TestHQStockAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'HQ-001',
            'std_manu': 'HQManu',
            'supplier': 'HQSupplier',
            'sup_ppn': 'SUP-HQ-001',
            'sup_manu': 'SupHQManu',
            'batch': '2024+',
            'stock': '1000',
            'packing': 'SOP',
            'param': '参数说明',
            'place': '深圳',
            'instruction': '使用说明',
            'publish_date': '2024-01-01',
            'task_name': 'test_hq'
        }
        response = client.post('/api/data/hq_stock/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/hq_stock/read?ppn=HQ-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['stock'] == '1000'


class TestHQHotAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'HQHOT-001',
            'manu': 'HotManu',
            'weak_hot': 85.5,
            'month_hot': 92.3,
            'task_name': 'test_hq_hot'
        }
        response = client.post('/api/data/hq_hot/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/hq_hot/read?ppn=HQHOT-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['weak_hot'] == 85.5
    
    def test_query_by_models(self, client):
        data1 = {'ppn': 'MODEL-A', 'manu': 'ManuA', 'weak_hot': 80.0, 'month_hot': 90.0, 'task_name': 'test'}
        data2 = {'ppn': 'MODEL-B', 'manu': 'ManuB', 'weak_hot': 70.0, 'month_hot': 80.0, 'task_name': 'test'}
        client.post('/api/data/hq_hot/write', json=[data1, data2])
        
        response = client.post('/api/data/hq_hot/query_by_models', json={'models': ['MODEL-A', 'MODEL-C', 'MODEL-B']})
        result = json.loads(response.data)
        assert len(result['data']) == 3
        assert result['data'][0]['ppn'] == 'MODEL-A'
        assert result['data'][1]['ppn'] == 'MODEL-C'
        assert result['data'][1]['manu'] == '--'


class TestEFindStockAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'EFIND-001',
            'manu': 'EFindManu',
            'sup_manu': 'SupManu',
            'supplier': 'EFindSupplier',
            'publish_date': '2024-01-15',
            'info': '库存信息',
            'price': '¥5.00',
            'stock': '500',
            'task_name': 'test_efind'
        }
        response = client.post('/api/data/efind_stock/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/efind_stock/read?ppn=EFIND-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['price'] == '¥5.00'


class TestEFindSupplierAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'ESUPP-001',
            'manu': 'ESuppManu',
            'all_supplier': 100,
            'price_supplier': 80,
            'stock_supplier': 50,
            'stock': '10000',
            'middle_price': '¥8.00',
            'min_price': '¥5.00',
            'max_price': '¥12.00',
            'task_name': 'test_esupp'
        }
        response = client.post('/api/data/efind_supplier/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/efind_supplier/read?ppn=ESUPP-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['all_supplier'] == 100


class TestBOMPriceAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'BOM-001',
            'manu': 'BOMManu',
            'supplier': 'BOMSupplier',
            'package': 'QFN-32',
            'lot': '2024+',
            'quoted_price': '¥3.50',
            'release_time': '2024-01-20',
            'stock_num': '2000',
            'valid_supplier': 5,
            'task_name': 'test_bom'
        }
        response = client.post('/api/data/bom_price/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/bom_price/read?ppn=BOM-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['quoted_price'] == '¥3.50'


class TestOctopartPriceAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'OCTO-P-001',
            'manu': 'OctoManu',
            'is_star': True,
            'distribute': 'DigiKey',
            'sku': 'SKU-12345',
            'stock': '5000',
            'moq': '1',
            'currency_type': 'CNY',
            'k_price': '¥15.00',
            'updated': '2024-01-25',
            'opn': 'OPN-001',
            'task_name': 'test_octo_p'
        }
        response = client.post('/api/data/octopart_price/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/octopart_price/read?ppn=OCTO-P-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['is_star'] == True


class TestOctopartMarketAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'OCTO-M-001',
            'manu': 'OctoManu',
            'des': '产品描述',
            'distribute': 'Mouser',
            'stock': '3000',
            'currency_type': 'USD',
            'k_price': '$2.00',
            'stock_pic': 'pic_url',
            'opn': 'OPN-M-001',
            'task_name': 'test_octo_m'
        }
        response = client.post('/api/data/octopart_market/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/octopart_market/read?ppn=OCTO-M-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['des'] == '产品描述'


class TestOctopartInfoAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'OCTO-I-001',
            'manu': 'OctoManu',
            'des': '详细描述',
            'distribute': 'Newark',
            'stock': '1000',
            'currency_type': 'EUR',
            'k_price': '€1.80',
            'opn': 'OPN-I-001',
            'stock_data': '库存数据JSON',
            'tech_data': '技术参数JSON',
            'supplier_data': '供应商数据JSON',
            'task_name': 'test_octo_i'
        }
        response = client.post('/api/data/octopart_info/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/octopart_info/read?ppn=OCTO-I-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['stock_data'] == '库存数据JSON'


class TestFindChipStockAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'FIND-001',
            'manu': 'FindManu',
            'supplier': 'FindSupplier',
            'authorized': True,
            'part_url': 'https://example.com/part',
            'stock_str': '10000 in stock',
            'task_name': 'test_find'
        }
        response = client.post('/api/data/findchip_stock/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/findchip_stock/read?ppn=FIND-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['authorized'] == True


class TestDigikeyAttrAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'DIGI-001',
            'manu': 'DigiManu',
            'digi_key_code': 'DK-123',
            'manu_code': 'MANU-456',
            'des': 'TVS二极管',
            'delivery_time': '5-7天',
            'detail_des': '详细描述',
            'category': '二极管',
            'serial': 'SMAJ系列',
            'package': 'SMA',
            'status': '在售',
            'kind': 'TVS',
            'single_channel': '是',
            'voltage_reverse': '5V',
            'voltage_breakdown': '6V',
            'voltage_ipp': '10V',
            'peakCurrentPulse': '400W',
            'peakPowerPulse': '400W',
            'protect_power': '400W',
            'apply': '电源保护',
            'capacitance': '100pF',
            'operating_temperature': '-55~150℃',
            'install_kind': 'SMD',
            'shell': 'SMA',
            'supplier_packeage': 'DigiReel',
            'product_code': 'DK-PROD-001',
            'task_name': 'test_digi'
        }
        response = client.post('/api/data/digikey_attr/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/digikey_attr/read?ppn=DIGI-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['digi_key_code'] == 'DK-123'


class TestWheatRecordAPI:
    def test_write_and_read(self, client):
        data = {'keyword': 'TEST-CHIP', 'all_records': 1000, 'task_name': 'test_wheat'}
        response = client.post('/api/data/wheat_record/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/wheat_record/read?keyword=TEST-CHIP')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['all_records'] == 1000
    
    def test_write_ru_records(self, client):
        data = {'keyword': 'TEST-CHIP-2', 'ru_records': 500, 'task_name': 'test_wheat'}
        response = client.post('/api/data/wheat_record/write?is_ru=true', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/wheat_record/read?keyword=TEST-CHIP-2')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['ru_records'] == 500


class TestWheatBuyerAPI:
    def test_write_and_read(self, client):
        data = {
            'keyword': 'IMPORT-001',
            'wheat_date': '2024-01',
            'buyer': '俄罗斯买家',
            'supplier': '中国供应商',
            'HSCode': '8542390000',
            'description': '集成电路',
            'buy_country': '俄罗斯',
            'supplier_country': '中国',
            'productContry': '中国',
            'weight': '100kg',
            'number': '10000',
            'totalValue': '$50000',
            'current_page': 1,
            'task_name': 'test_wheat_buyer'
        }
        response = client.post('/api/data/wheat_buyer/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/wheat_buyer/read?keyword=IMPORT-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['HSCode'] == '8542390000'


class TestRusprofileAPI:
    def test_write_and_read(self, client):
        data = {
            'company_name': 'Test Company LLC',
            'profile_id': '123456',
            'full_name': 'Test Company Limited Liability Company',
            'inn': '1234567890',
            'activity': '电子元器件贸易',
            'register_date': '2020-01-01',
            'industry_rank': '123',
            'company_address': '莫斯科, 红场1号',
            'phone': '+7-495-123-45-67',
            'email': 'test@example.com',
            'website': 'https://example.com',
            'revenue': '100000000',
            'profit': '10000000',
            'cost': '90000000',
            'task_name': 'test_rus'
        }
        response = client.post('/api/data/rusprofile/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/rusprofile/read?inn=1234567890')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['company_name'] == 'Test Company LLC'


class TestFutureInfoAPI:
    def test_write_and_read(self, client):
        data = {
            'st_part': 'ST-001',
            'st_manu': 'STManu',
            'f_ppn': 'FUTURE-001',
            'f_manu': 'FutureManu',
            'OnOrder': '1000',
            'stock': '500',
            'leadTime': '4-6周',
            'unitPrice': '¥20.00',
            'task_name': 'test_future'
        }
        response = client.post('/api/data/future_info/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/future_info/read?st_part=ST-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['leadTime'] == '4-6周'


class TestArrowInfoAPI:
    def test_write_and_read(self, client):
        data = {
            'st_part': 'ST-ARROW-001',
            'st_manu': 'STManu',
            'a_ppn': 'ARROW-001',
            'a_manu': 'ArrowManu',
            'stock': '2000',
            'leadTime': '2-4周',
            'price': '¥18.00',
            'batch': '2024+',
            'task_name': 'test_arrow'
        }
        response = client.post('/api/data/arrow_info/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/arrow_info/read?st_part=ST-ARROW-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['price'] == '¥18.00'


class TestPPNAPI:
    def test_write_and_read(self, client):
        data = {
            'ppn': 'PPN-TEST-001',
            'manu_id': 'M001',
            'manu_name': 'TestManufacturer',
            'source': 'HQ'
        }
        response = client.post('/api/data/ppn/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/ppn/read?ppn=PPN-TEST-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['manu_name'] == 'TestManufacturer'


class TestOPNAPI:
    def test_write_and_read(self, client):
        data = {
            'opn': 'OPN-TEST-001',
            'manu_id': 'M001',
            'manu_name': 'TestManufacturer'
        }
        response = client.post('/api/data/opn/write', json=data)
        assert response.status_code == 200
        
        response = client.get('/api/data/opn/read?opn=OPN-TEST-001')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['manu_name'] == 'TestManufacturer'


class TestBatchOperations:
    def test_batch_write(self, client):
        tasks = []
        for i in range(10):
            tasks.append({
                'Tname': f'batch_task_{i}',
                'Tdes': f'批量任务{i}',
                'Tstate': 'pending',
                'Tlevel': i % 3 + 1
            })
        
        response = client.post('/api/data/task/write', json=tasks)
        assert response.status_code == 200
        
        response = client.get('/api/data/task/read')
        result = json.loads(response.data)
        assert len(result['data']) == 10
    
    def test_upsert_operation(self, client):
        data = {'Tname': 'upsert_test', 'Tdes': '原始描述', 'Tstate': 'pending', 'Tlevel': 1}
        client.post('/api/data/task/write', json=data)
        
        update_data = {'Tname': 'upsert_test', 'Tdes': '更新后的描述', 'Tstate': 'running', 'Tlevel': 2}
        response = client.post('/api/data/task/write', json=update_data)
        assert response.status_code == 200
        
        response = client.get('/api/data/task/read?Tname=upsert_test')
        result = json.loads(response.data)
        assert len(result['data']) == 1
        assert result['data'][0]['Tdes'] == '更新后的描述'
        assert result['data'][0]['Tstate'] == 'running'
