"""
Agent 记忆层 — 无操作模式，待后续接入持久化后端时替换此类即可。
"""


class SessionStore:
    """无操作记忆层 — 所有读写直接丢弃，接口保持兼容"""

    def create_session(self, session_id: str, contract_file: str = "",
                       output_file: str = "") -> str:
        return session_id

    def update_session_status(self, session_id: str, status: str,
                              message_count: int = 0):
        pass

    def list_sessions(self, limit: int = 20) -> list[dict]:
        return []

    def get_session(self, session_id: str) -> dict | None:
        return None

    def save_message(self, session_id: str, step: int, role: str,
                     content: str = "", tool_name: str = None,
                     tool_args: dict = None, think_text: str = None):
        pass

    def get_session_messages(self, session_id: str) -> list[dict]:
        return []

    def save_legal_memory(self, clause_text: str, law_ref: str,
                          source_session: str, score: float = 0.0):
        pass

    def find_similar_cases(self, clause_text: str, top_k: int = 3) -> list[dict]:
        return []

    def get_legal_memory_stats(self) -> dict:
        return {"total_entries": 0, "most_used": []}

    def save_revision_pattern(self, pattern_name: str, original: str,
                              revised: str, law_basis: str):
        pass

    def get_common_patterns(self, limit: int = 5) -> list[dict]:
        return []


__all__ = ["SessionStore"]
