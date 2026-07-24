"""
项目启动脚本 — 一键启动

开发模式: python start.py --dev    (前端热更新 + 后端 API)
生产模式: python start.py          (build 前端 + 启动服务)

访问: http://localhost:5000
"""

import os
import sys
import subprocess
import signal

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")
PORT = 8080


def kill_port(port: int):
    """杀死占用指定端口的进程 (Windows)"""
    if os.name != 'nt':
        return
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True, capture_output=True, text=True
        )
        seen = set()
        for line in result.stdout.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 5 and 'LISTENING' in line:
                pid = parts[-1]
                if pid not in seen:
                    seen.add(pid)
                    subprocess.run(f'taskkill /PID {pid} /F', shell=True,
                                   capture_output=True)
                    print(f"  已清理端口 {port} (PID {pid})")
    except Exception:
        pass


def build_frontend():
    """构建前端"""
    print("=" * 50)
    print("  构建前端...")
    print("=" * 50)
    result = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, shell=True)
    if result.returncode != 0:
        print("前端构建失败！请先运行: cd frontend && npm install")
        sys.exit(1)
    print("  前端构建完成 → frontend/dist/\n")


def start_backend():
    """启动 Flask 后端"""
    sys.path.insert(0, BACKEND)
    os.chdir(BACKEND)
    from run import app
    print("=" * 50)
    print(f"  http://localhost:{PORT}")
    print("  Ctrl+C 停止服务")
    print("=" * 50)
    app.run(debug=False, host="0.0.0.0", port=PORT, use_reloader=False)


if __name__ == "__main__":
    dev_mode = "--dev" in sys.argv

    if dev_mode:
        print("开发模式: 前端 npm run dev (port 3000) + 后端 python run.py (port 5000)")
        print("请手动在两个终端分别启动:")
        print("  终端1: cd frontend && npm run dev")
        print("  终端2: cd backend && python run.py")
    else:
        # 清理旧进程
        kill_port(PORT)

        # 检查是否需要安装前端依赖
        if not os.path.exists(os.path.join(FRONTEND, "node_modules")):
            print("前端依赖未安装，正在安装...")
            subprocess.run(["npm", "install"], cwd=FRONTEND, shell=True)

        # 检查是否需要构建
        dist_dir = os.path.join(FRONTEND, "dist")
        if not os.path.exists(dist_dir):
            build_frontend()

        start_backend()
