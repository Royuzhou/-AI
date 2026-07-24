"""
src/mcp — 自研 MCP 精简协议 (替代 mcp + langchain-mcp-adapters)

协议: JSON-RPC over stdio
方法: initialize / ping / tools/list / tools/call
"""

from .server import SimpleMCPServer
from .client import SimpleMCPClient

__all__ = ["SimpleMCPServer", "SimpleMCPClient"]
