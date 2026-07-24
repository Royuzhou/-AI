"""合同修订 API"""
import asyncio
import os
import threading
import uuid
from flask import request, jsonify, Response
from . import api
from config import CONFIG

_task_status: dict[str, dict] = {}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@api.route("/contract/revise", methods=["POST"])
def contract_revise():
    """启动合同修订 (后台线程)"""
    data = request.json or {}
    fp = data.get("filepath", "")
    if not fp or not os.path.exists(fp):
        return jsonify({"success": False, "error": "file not found"}), 400

    task_id = str(uuid.uuid4())[:8]
    _task_status[task_id] = {"status": "processing", "result": None, "error": None}

    def _run():
        try:
            from src.agent import ContractRevisionAgent
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            agent = ContractRevisionAgent(CONFIG)
            loop.run_until_complete(agent.initialize())
            result = loop.run_until_complete(agent.process_contract(fp, output_dir=OUTPUT_DIR))
            _task_status[task_id] = {"status": "completed", "result": result}
        except Exception as e:
            import traceback
            _task_status[task_id] = {
                "status": "failed", "error": str(e),
                "traceback": traceback.format_exc(),
            }

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"success": True, "task_id": task_id})


@api.route("/contract/status/<task_id>", methods=["GET"])
def contract_status(task_id):
    task = _task_status.get(task_id)
    if not task:
        return jsonify({"status": "not_found"}), 404
    return jsonify(task)


@api.route("/contract/download/<task_id>", methods=["GET"])
def contract_download(task_id):
    task = _task_status.get(task_id, {})
    result = task.get("result", "")
    if not result:
        return jsonify({"error": "结果不可用"}), 404
    return Response(result, mimetype="text/plain; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename=revised_{task_id}.txt"})
