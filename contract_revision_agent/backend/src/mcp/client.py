"""
MCP 精简 Client — 替代 langchain_mcp_adapters.client.MultiServerMCPClient

功能:
  - 按配置启动子进程（每个 MCP Server 一个进程）
  - initialize 握手 + tools/list 发现工具
  - 将 MCP tool 包装为 langchain_core.tools.BaseTool (StructuredTool)
  - 工具调用时通过 stdio 发送 JSON 请求并读取响应
  - 进程级锁保证线程安全
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import threading
from typing import Any, Type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from .protocol import Request, Response


# ═══════════════════════════════════════════════════════════════
# 工具工厂 — 闭包持有 state，避免 Pydantic 字段冲突
# ═══════════════════════════════════════════════════════════════

def _create_mcp_tool(
    process: subprocess.Popen,
    schema: dict,
    lock: threading.Lock,
) -> StructuredTool:
    """从 MCP tool schema 创建 LangChain StructuredTool。

    使用闭包持有 process 和 lock，避免 Pydantic BaseTool 子类的字段冲突。
    """
    tool_name = schema["name"]

    # 从 inputSchema 动态生成 Pydantic args_schema
    input_schema = schema.get("inputSchema", {})
    args_model = _build_args_model(tool_name, input_schema)

    def _call_mcp_tool(arguments: dict) -> str:
        """通过 stdio 发送 tools/call 并读取结果（同步、线程安全）"""
        with lock:
            req_id = str(threading.get_ident()) + "_" + tool_name
            req = {
                "id": req_id,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }
            req_line = json.dumps(req, ensure_ascii=False) + "\n"

            try:
                process.stdin.write(req_line)
                process.stdin.flush()
            except (BrokenPipeError, OSError) as e:
                return f"工具调用失败 — 子进程已断开: {e}"

            try:
                resp_line = process.stdout.readline()
                if not resp_line:
                    return "工具调用失败 — 子进程无响应（stdout EOF）"
                resp_data = json.loads(resp_line)
            except (json.JSONDecodeError, Exception) as e:
                return f"工具调用失败 — 响应解析错误: {e}"

            if resp_data.get("error"):
                err = resp_data["error"]
                return f"工具执行错误: {err.get('message', str(err))}"

            result = resp_data.get("result")
            return str(result) if result is not None else "（工具执行完成，无返回内容）"

    # 同步包装: 接收 **kwargs，组装为 arguments dict
    def _sync_runner(**kwargs) -> str:
        # 去掉占位字段
        kwargs.pop("_placeholder", None)
        return _call_mcp_tool(kwargs)

    # 异步包装
    async def _async_runner(**kwargs) -> str:
        kwargs.pop("_placeholder", None)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _call_mcp_tool, kwargs)

    return StructuredTool(
        name=tool_name,
        description=schema.get("description", ""),
        args_schema=args_model,
        func=_sync_runner,
        coroutine=_async_runner,
        response_format="content",
    )


# ═══════════════════════════════════════════════════════════════
# MCP Client — 管理所有子进程
# ═══════════════════════════════════════════════════════════════

class SimpleMCPClient:
    """MCP Client — 启动子进程、发现工具、返回 BaseTool 列表

    用法:
        client = SimpleMCPClient({
            "extractor": {"command": "python", "args": ["-m", "src.tools.document_server"]},
        })
        tools = await client.get_tools()
    """

    def __init__(self, servers: dict[str, dict]):
        self._servers = servers
        self._processes: dict[str, subprocess.Popen] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._tools: list[StructuredTool] = []
        self._started = False

    async def get_tools(self) -> list[StructuredTool]:
        """启动子进程 → 发现工具 → 返回 BaseTool 列表"""
        if not self._started:
            await self.start_all()
        return self._tools

    async def start_all(self):
        """启动所有 MCP Server 子进程并发现工具"""
        loop = asyncio.get_running_loop()
        for name, cfg in self._servers.items():
            cmd = [cfg["command"]] + cfg.get("args", [])
            proc = await loop.run_in_executor(
                None,
                lambda c=cmd: subprocess.Popen(
                    c, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, encoding="utf-8",
                ),
            )
            self._processes[name] = proc
            self._locks[name] = threading.Lock()

            # initialize 握手
            await self._send_initialize(proc, name)

            # tools/list 发现工具
            schemas = await self._discover_tools(proc, name)

            # 包装为 StructuredTool
            lock = self._locks[name]
            for schema in schemas:
                tool = _create_mcp_tool(process=proc, schema=schema, lock=lock)
                self._tools.append(tool)

            print(f"  MCP Server [{name}]: {len(schemas)} 个工具已加载")

        self._started = True

    async def _send_initialize(self, proc: subprocess.Popen, name: str):
        """发送 initialize 握手请求"""
        loop = asyncio.get_running_loop()
        req = json.dumps({
            "id": "init-1",
            "method": "initialize",
            "params": {"clientInfo": {"name": "contract-revision-agent"}},
        }, ensure_ascii=False) + "\n"

        await loop.run_in_executor(None, lambda: proc.stdin.write(req) or proc.stdin.flush())
        resp_line = await loop.run_in_executor(None, proc.stdout.readline)
        resp = json.loads(resp_line)

        if resp.get("error"):
            raise RuntimeError(f"MCP Server [{name}] 初始化失败: {resp['error']}")

        server_info = resp.get("result", {}).get("serverInfo", {})
        print(f"  MCP Server [{name}]: {server_info.get('name', '?')} v{server_info.get('version', '?')}")

    async def _discover_tools(self, proc: subprocess.Popen, name: str) -> list[dict]:
        """发送 tools/list 发现工具列表"""
        loop = asyncio.get_running_loop()
        req = json.dumps({
            "id": "list-1",
            "method": "tools/list",
            "params": {},
        }, ensure_ascii=False) + "\n"

        await loop.run_in_executor(None, lambda: proc.stdin.write(req) or proc.stdin.flush())
        resp_line = await loop.run_in_executor(None, proc.stdout.readline)
        resp = json.loads(resp_line)

        if resp.get("error"):
            raise RuntimeError(f"MCP Server [{name}] tools/list 失败: {resp['error']}")

        return resp.get("result", {}).get("tools", [])

    def close(self):
        """关闭所有子进程"""
        for name, proc in self._processes.items():
            try:
                proc.stdin.close()
                proc.stdout.close()
                proc.stderr.close()
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                proc.kill()


# ═══════════════════════════════════════════════════════════════
# Pydantic 动态模型生成
# ═══════════════════════════════════════════════════════════════

_JSON_TYPE_TO_PYTHON = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


def _build_args_model(name: str, input_schema: dict) -> Type[BaseModel]:
    """从 JSON Schema 动态生成 Pydantic 模型（供 LangChain 校验参数）"""
    properties = input_schema.get("properties", {})
    required = set(input_schema.get("required", []))

    fields = {}
    for prop_name, prop_schema in properties.items():
        prop_type = prop_schema.get("type", "string")
        python_type = _JSON_TYPE_TO_PYTHON.get(prop_type, str)
        is_required = prop_name in required
        description = prop_schema.get("description", "")

        # list[str] → str (JSON 字符串)，tool 内部自行解析
        if prop_type == "array":
            python_type = str
        elif prop_type == "object":
            python_type = str

        if is_required:
            fields[prop_name] = (python_type, Field(description=description))
        else:
            fields[prop_name] = (python_type | None, Field(default=None, description=description))

    if not fields:
        fields["_placeholder"] = (str | None, Field(default=None, description="占位"))

    model_name = f"{name}_args".replace("-", "_")
    return create_model(model_name, **fields)
