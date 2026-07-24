"""
MCP Host — 代理 + 日志层

位于 Agent 和所有 MCP Server 之间:
  Agent ←→ Host (stdio) ←→ 5 个 MCP Server (stdio 子进程)

职责:
  1. 向 Agent 暴露所有下游工具（透明代理）
  2. 记录所有请求/响应到 logs/mcp_YYYYMMDD.log
  3. 子进程生命周期管理
"""

import asyncio
import json
import os
import subprocess
import sys
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import MCP_SERVERS
from src.mcp.protocol import Request, Response, read_request, write_response, write_error


class MCPHost:
    """MCP 代理主机"""

    def __init__(self, servers_config: dict = None):
        self._servers_cfg = servers_config or MCP_SERVERS
        self._processes: dict[str, subprocess.Popen] = {}
        self._tool_routing: dict[str, str] = {}  # tool_name → server_name
        self._locks: dict[str, threading.Lock] = {}
        self._log_path = self._init_log()

    def _init_log(self) -> str:
        os.makedirs("logs", exist_ok=True)
        path = f"logs/mcp_{datetime.now().strftime('%Y%m%d')}.log"
        return path

    def _log(self, direction: str, server: str, content: str):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{ts}] {direction} [{server}] {content[:500]}\n"
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(line)

    def start_all(self):
        """启动所有下游 MCP Server 并构建工具路由表"""
        for name, cfg in self._servers_cfg.items():
            cmd = [cfg["command"]] + cfg.get("args", [])
            proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, encoding="utf-8",
            )
            self._processes[name] = proc
            self._locks[name] = threading.Lock()

            # initialize
            self._send_recv(proc, name, "initialize", {"clientInfo": {"name": "mcp-host"}})

            # tools/list
            resp = self._send_recv(proc, name, "tools/list", {})
            tools = resp.get("result", {}).get("tools", [])
            for t in tools:
                self._tool_routing[t["name"]] = name
                self._log("INIT", name, f"tool={t['name']}")

            print(f"[MCP Host] {name}: {len(tools)} tools loaded")

    def _send_recv(self, proc, server_name: str, method: str, params: dict) -> dict:
        """同步发送请求并读取响应"""
        lock = self._locks[server_name]
        with lock:
            req = json.dumps({"id": method[:6], "method": method, "params": params}, ensure_ascii=False)
            self._log("REQ", server_name, req)
            proc.stdin.write(req + "\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            resp = json.loads(line) if line else {"error": "no response"}
            self._log("RESP", server_name, json.dumps(resp, ensure_ascii=False)[:500])
            return resp

    def get_all_tool_schemas(self) -> list[dict]:
        """返回所有下游工具 schema 的并集"""
        schemas = []
        for name, proc in self._processes.items():
            resp = self._send_recv(proc, name, "tools/list", {})
            schemas.extend(resp.get("result", {}).get("tools", []))
        return schemas

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """转发工具调用到对应下游 server"""
        server_name = self._tool_routing.get(tool_name)
        if not server_name:
            return f"Error: tool '{tool_name}' not found"
        proc = self._processes[server_name]
        resp = self._send_recv(proc, server_name, "tools/call", {"name": tool_name, "arguments": arguments})
        if resp.get("error"):
            return f"Error: {resp['error'].get('message', str(resp['error']))}"
        return str(resp.get("result", ""))

    def close(self):
        for proc in self._processes.values():
            try:
                proc.stdin.close(); proc.stdout.close(); proc.stderr.close()
                proc.terminate(); proc.wait(timeout=3)
            except: proc.kill()
