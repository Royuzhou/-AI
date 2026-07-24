"""
合同修订智能体 — Web API 启动入口

启动: python run.py
"""

import os
import sys
import mimetypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory
from src.api import api

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.urandom(24)

app.register_blueprint(api)

# 前端 dist 路径
_dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
_dist_dir = os.path.abspath(_dist_dir)

# 确保 MIME 类型正确
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")


@app.route("/")
@app.route("/<path:path>")
def serve_frontend(path=""):
    """SPA: 真实文件返回文件，否则返回 index.html"""
    if path:
        file_path = os.path.join(_dist_dir, path)
        if os.path.isfile(file_path):
            return send_from_directory(_dist_dir, path)
    # SPA fallback
    return send_from_directory(_dist_dir, "index.html")


if __name__ == "__main__":
    print("=" * 60)
    print("  Contract Revision Agent")
    print("  http://localhost:8080")
    print("=" * 60)
    app.run(debug=False, host="0.0.0.0", port=8080)
