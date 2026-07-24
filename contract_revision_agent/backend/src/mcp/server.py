"""
MCP 精简 Server — 替代 mcp.server.Server

功能:
  - @server.tool() 装饰器注册工具
  - stdio 事件循环: 读请求 → 派发 → 写响应
  - 从函数类型注解自动生成 JSON Schema (inputSchema)

支持的方法: initialize / ping / tools/list / tools/call
"""

from __future__ import annotations

import inspect
import sys
import traceback
from typing import Any, Callable

from .protocol import (
    Request, Response, ToolSchema,
    read_request, write_response, write_error,
    METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL_ERROR,
)


class SimpleMCPServer:
    """MCP 精简 Server — 与 mcp.server.Server 接口兼容"""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: dict[str, Callable] = {}
        self._tool_descriptions: dict[str, str] = {}
        self._tool_arg_descriptions: dict[str, dict[str, str]] = {}
        self._initialized = False
        self._client_info: dict = {}

    def tool(self, arg_description: str = None):
        """装饰器: @server.tool() 注册工具函数。

        从函数签名和 docstring 自动提取:
          - name: 函数名
          - description: docstring 首段
          - inputSchema: 类型注解 → JSON Schema
        """
        def decorator(func):
            name = func.__name__
            self._tools[name] = func
            # 从 docstring 提取 description
            desc = (func.__doc__ or "").strip()
            self._tool_descriptions[name] = desc
            return func
        return decorator

    # ── 工具 Schema 生成 ──────────────────────────────

    def _build_tool_schemas(self) -> list[dict]:
        """生成所有工具的 JSON Schema 列表，兼容 MCP tools/list 响应"""
        schemas = []
        for name, func in self._tools.items():
            schemas.append({
                "name": name,
                "description": self._tool_descriptions.get(name, ""),
                "inputSchema": self._build_input_schema(func),
            })
        return schemas

    @staticmethod
    def _build_input_schema(func: Callable) -> dict:
        """从函数类型注解推断 JSON Schema"""
        hints = inspect.get_annotations(func)
        properties = {}
        required = []

        for param_name, param_type in hints.items():
            if param_name == "return":
                continue
            json_type = _python_type_to_json_type(param_type)
            if json_type == "array":
                item_type = _get_list_item_type(param_type)
                properties[param_name] = {
                    "type": "array",
                    "description": param_name,
                    "items": {"type": item_type} if item_type else {},
                }
            else:
                properties[param_name] = {"type": json_type, "description": param_name}

        # 参数全为 required（简化处理）
        required = list(properties.keys())

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    # ── 请求派发 ──────────────────────────────────────

    async def _dispatch(self, req: Request) -> Response:
        method = req.method
        req_id = req.id

        if method == "initialize":
            return self._handle_initialize(req_id, req.params)
        elif method == "ping":
            return Response(id=req_id, result={"pong": True})
        elif method == "tools/list":
            return self._handle_tools_list(req_id)
        elif method == "tools/call":
            return await self._handle_tools_call(req_id, req.params)
        else:
            return Response(id=req_id, error={
                "code": METHOD_NOT_FOUND, "message": f"未知方法: {method}"
            })

    def _handle_initialize(self, req_id: str, params: dict) -> Response:
        self._client_info = params.get("clientInfo", {})
        self._initialized = True
        return Response(id=req_id, result={
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": self.name, "version": self.version},
            "capabilities": {"tools": {}},
        })

    def _handle_tools_list(self, req_id: str) -> Response:
        return Response(id=req_id, result={
            "tools": self._build_tool_schemas()
        })

    async def _handle_tools_call(self, req_id: str, params: dict) -> Response:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if not tool_name or tool_name not in self._tools:
            return Response(id=req_id, error={
                "code": METHOD_NOT_FOUND, "message": f"未找到工具: {tool_name}"
            })

        try:
            func = self._tools[tool_name]
            if inspect.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = func(**arguments)
            return Response(id=req_id, result=result)
        except Exception as e:
            return Response(id=req_id, error={
                "code": INTERNAL_ERROR,
                "message": str(e),
                "data": traceback.format_exc(),
            })

    # ── 事件循环 ──────────────────────────────────────

    async def run(self, read_stream=None, write_stream=None):
        """stdio 事件循环: 逐行读 JSON → 派发 → 写 JSON 响应"""
        while True:
            req = read_request(read_stream)
            if req is None:
                break  # stdin EOF → 退出

            # 解析失败
            if req.method == "":
                write_error(req.id or "", -32700, "JSON 解析失败", write_stream)
                continue

            resp = await self._dispatch(req)
            write_response(resp, write_stream)

    def run_sync(self):
        """同步入口 — 兼容不支持 asyncio 的场景"""
        import asyncio
        asyncio.run(self.run())


# ═══════════════════════════════════════════════════════════════
# 类型映射工具
# ═══════════════════════════════════════════════════════════════

_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _python_type_to_json_type(python_type) -> str:
    """将 Python 类型映射为 JSON Schema type"""
    origin = getattr(python_type, "__origin__", None)
    if origin is list or origin is getattr(sys.modules.get("typing"), "List", None):
        return "array"
    return _TYPE_MAP.get(python_type, "string")


def _get_list_item_type(python_type) -> str:
    """获取 list[...] 的 item 类型"""
    args = getattr(python_type, "__args__", None)
    if args:
        return _python_type_to_json_type(args[0])
    return "string"
