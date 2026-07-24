"""
Agent 校验 Hooks — 可插拔的检查模块

每个 hook 是一个独立函数，可在 Agent 流程中按需调用，
也可通过 CLI 独立运行: python -m src.hooks.<name>
"""

from .think_answer_validator import validate_think_answer, ThinkAnswerError
from .format_validator import validate_revision_format, FormatError

__all__ = [
    "validate_think_answer",
    "ThinkAnswerError",
    "validate_revision_format",
    "FormatError",
]
