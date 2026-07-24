"""
MCP 精简协议 — 消息类型定义与 stdio JSON 序列化

仅实现: tools/list + tools/call + initialize + ping
传输层: stdio (stdin 读，stdout 写)
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Any, Literal

# ═══════════════════════════════════════════════════════════════
# 消息类型
# ═══════════════════════════════════════════════════════════════

@dataclass
class Request:
    id: str
    method: str
    params: dict = field(default_factory=dict)

@dataclass
class Response:
    id: str
    result: Any = None
    error: dict | None = None

    @property
    def is_error(self) -> bool:
        return self.error is not None

# ═══════════════════════════════════════════════════════════════
# 错误码（兼容 JSON-RPC 2.0）
# ═══════════════════════════════════════════════════════════════

PARSE_ERROR      = -32700
METHOD_NOT_FOUND = -32601
INVALID_PARAMS   = -32602
INTERNAL_ERROR   = -32603

def make_error(code: int, message: str, data: Any = None) -> dict:
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return err

# ═══════════════════════════════════════════════════════════════
# Tool Schema（tools/list 返回格式）
# ═══════════════════════════════════════════════════════════════

@dataclass
class ToolSchema:
    name: str
    description: str
    inputSchema: dict  # JSON Schema for tool arguments

# ═══════════════════════════════════════════════════════════════
# stdio 读写
# ═══════════════════════════════════════════════════════════════

def read_request(stream=None) -> Request | None:
    """从 stdin 读一行 JSON，解析为 Request。EOF 返回 None。"""
    if stream is None:
        stream = sys.stdin
    line = stream.readline()
    if not line:
        return None
    try:
        data = json.loads(line)
        return Request(
            id=data.get("id", ""),
            method=data.get("method", ""),
            params=data.get("params", {}),
        )
    except (json.JSONDecodeError, KeyError) as e:
        return Request(id="", method="", params={"_parse_error": str(e)})

def write_response(resp: Response, stream=None):
    """将 Response 序列化为一行 JSON 写入 stdout（强制 UTF-8）。"""
    if stream is None:
        stream = sys.stdout
    payload = asdict(resp)
    line = json.dumps(payload, ensure_ascii=False) + "\n"
    # Windows 下 stdout 可能是 GBK，用 buffer 直接写 UTF-8 字节
    if hasattr(stream, "buffer"):
        stream.buffer.write(line.encode("utf-8"))
        stream.buffer.flush()
    else:
        stream.write(line)
        stream.flush()

def write_error(req_id: str, code: int, message: str, stream=None):
    """快捷: 写入错误响应。"""
    write_response(Response(id=req_id, error=make_error(code, message)), stream=stream)
