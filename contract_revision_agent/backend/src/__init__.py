"""合同修订智能体 - 核心模块"""

# 延迟导入 — 避免在 web 等不需要 Agent 的场景下加载 LangChain/MCP 依赖
__all__ = ['ContractRevisionAgent']


def __getattr__(name):
    if name == 'ContractRevisionAgent':
        from .agent import ContractRevisionAgent
        return ContractRevisionAgent
    raise AttributeError(f"module 'src' has no attribute '{name}'")
