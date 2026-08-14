"""
ChipPower 数据服务
启动方式: python main.py
"""

import os
import subprocess
import signal
import time
from dotenv import load_dotenv

load_dotenv()
SERVER_PORT = int(os.getenv('SERVER_PORT', 8001))


def kill_port(port):
    """启动前杀掉占用端口的旧进程"""
    try:
        subprocess.run(["pkill", "-9", "-f", "python.*main.py"], capture_output=True, timeout=2)
        time.sleep(0.3)
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=2)
        for pid in [p.strip() for p in result.stdout.split('\n') if p.strip()]:
            try:
                os.kill(int(pid), signal.SIGKILL)
                print(f"终止占用端口 {port} 的进程: {pid}")
            except:
                pass
    except:
        pass


from app import create_app
app = create_app()


if __name__ == '__main__':
    kill_port(SERVER_PORT)
    print(f"服务启动: http://localhost:{SERVER_PORT}")
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=False, threaded=True)
