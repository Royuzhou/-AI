"""文件上传"""
import os
from flask import request, jsonify
from . import api

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@api.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "no file"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"success": False, "error": "empty filename"}), 400
    fp = os.path.join(UPLOAD_DIR, file.filename)
    file.save(fp)
    return jsonify({"success": True, "filename": file.filename, "path": fp})
