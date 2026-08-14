import threading
import time
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from app.config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app)

    from app.controllers.data_controller import data_bp
    app.register_blueprint(data_bp, url_prefix='/api/data')

    # 启动连接池保活线程：每20秒执行一次简单查询，防止远程数据库连接在爬虫等待期间失效
    def keep_alive():
        while True:
            try:
                with app.app_context():
                    with db.engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
            except Exception:
                pass
            time.sleep(20)

    t = threading.Thread(target=keep_alive, daemon=True)
    t.start()

    return app
