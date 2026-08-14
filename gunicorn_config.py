# Gunicorn 生产环境配置， mac 本地调试不要用
import multiprocessing
import os
import subprocess
import time
from dotenv import load_dotenv

# 加载.env配置
load_dotenv()

# 端口从.env读取
_port = int(os.getenv('SERVER_PORT', 8001))
bind = f"0.0.0.0:{_port}"

# worker进程数
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_connections = 1000

# 超时
timeout = 180
graceful_timeout = 30
keepalive = 5

# 进程名
proc_name = "chippower"

# 日志
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
accesslog = os.path.join(log_dir, "access.log")
errorlog = os.path.join(log_dir, "error.log")
loglevel = "info"

# 工作目录
chdir = os.path.dirname(os.path.abspath(__file__))

# 预加载
preload_app = True
daemon = False


def on_starting(server):
    """gunicorn master进程启动前清理端口"""
    port = _port
    try:
        # 杀掉旧进程
        subprocess.run(["pkill", "-9", "-f", "gunicorn.*main:app"], capture_output=True, timeout=3)
        subprocess.run(["pkill", "-9", "-f", "python.*main.py"], capture_output=True, timeout=3)
        time.sleep(0.5)
        
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=3)
        pids = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
        for pid in pids:
            try:
                os.kill(int(pid), 9)
                print(f"[gunicorn] 终止占用端口 {port} 的进程 PID={pid}")
            except:
                pass
        if pids:
            time.sleep(0.5)
    except Exception as e:
        print(f"[gunicorn] 清理端口出错: {e}")
