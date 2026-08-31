import threading
import time
import gzip
from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from app.config import Config

db = SQLAlchemy()

# 超过该字节数的 JSON 响应才启用 gzip 压缩，避免大响应在远程网络上被截断
GZIP_MIN_LENGTH = 2048


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app)

    # 对较大的 JSON 响应启用 gzip，避免大响应(尤其单行 JSON)在远程网络上传输时被中间层截断
    @app.after_request
    def compress_large_responses(response):
        if 'gzip' not in request.headers.get('Accept-Encoding', ''):
            return response
        if response.mimetype != 'application/json' or not response.is_sequence:
            return response
        data = response.get_data()
        if data is None or len(data) < GZIP_MIN_LENGTH:
            return response
        compressed = gzip.compress(data, compresslevel=6)
        if len(compressed) >= len(data):
            return response
        response.set_data(compressed)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Vary'] = 'Accept-Encoding'
        response.headers['Content-Length'] = str(len(compressed))
        return response

    from app.controllers.data_controller import data_bp
    app.register_blueprint(data_bp, url_prefix='/api/data')

    # 启动连接池保活线程：每20秒ping两个数据库，防止远程连接在爬虫等待期间失效
    def keep_alive():
        while True:
            with app.app_context():
                # 保活主库
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                except Exception:
                    pass
                # 保活monitor库
                try:
                    monitor_engine = db.engines.get('monitor')
                    if monitor_engine:
                        with monitor_engine.connect() as conn:
                            conn.execute(text("SELECT 1"))
                except Exception:
                    pass
                # 保活tender库
                try:
                    tender_engine = db.engines.get('tender')
                    if tender_engine:
                        with tender_engine.connect() as conn:
                            conn.execute(text("SELECT 1"))
                except Exception:
                    pass
            time.sleep(20)

    t = threading.Thread(target=keep_alive, daemon=True)
    t.start()

    return app
