import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'chip-power-secret-key-2024')
    # MySQL 数据库配置
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'yjcx_recommended')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        f'?charset=utf8mb4'
        f'&ssl_disabled=True'
        f'&connect_timeout=120'
        f'&read_timeout=120'
        f'&write_timeout=120'
    )

    # 监控数据库 (monitor_market)
    MONITOR_DB_HOST = os.getenv('MONITOR_DB_HOST', '8.219.49.4')
    MONITOR_DB_USER = os.getenv('MONITOR_DB_USER', 'monitorDBA')
    MONITOR_DB_PASSWORD = os.getenv('MONITOR_DB_PASSWORD', 'Calcitrapa0228.')
    MONITOR_DB_NAME = os.getenv('MONITOR_DB_NAME', 'monitor_market')
    MONITOR_DB_PORT = int(os.getenv('MONITOR_DB_PORT', 3306))

    # 招标数据库 (tender_info)
    TENDER_DB_HOST = os.getenv('TENDER_DB_HOST', '8.219.49.4')
    TENDER_DB_USER = os.getenv('TENDER_DB_USER', 'tender_manager')
    TENDER_DB_PASSWORD = os.getenv('TENDER_DB_PASSWORD', 'ZGKHyuE2t8GBsmDn')
    TENDER_DB_NAME = os.getenv('TENDER_DB_NAME', 'tender_info')
    TENDER_DB_PORT = int(os.getenv('TENDER_DB_PORT', 3306))

    SQLALCHEMY_BINDS = {
        'monitor': (
            f'mysql+pymysql://{MONITOR_DB_USER}:{MONITOR_DB_PASSWORD}@{MONITOR_DB_HOST}:{MONITOR_DB_PORT}/{MONITOR_DB_NAME}'
            f'?charset=utf8mb4'
            f'&ssl_disabled=True'
            f'&connect_timeout=120'
            f'&read_timeout=120'
            f'&write_timeout=120'
        ),
        'tender': (
            f'mysql+pymysql://{TENDER_DB_USER}:{TENDER_DB_PASSWORD}@{TENDER_DB_HOST}:{TENDER_DB_PORT}/{TENDER_DB_NAME}'
            f'?charset=utf8mb4'
            f'&ssl_disabled=True'
            f'&connect_timeout=120'
            f'&read_timeout=120'
            f'&write_timeout=120'
        )
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 1800
    SQLALCHEMY_POOL_PRE_PING = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 1800,
        'connect_args': {
            'ssl_disabled': True,
            'connect_timeout': 120,
            'read_timeout': 120,
            'write_timeout': 120,
        }
    }
    SQLALCHEMY_ECHO = False
