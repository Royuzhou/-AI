"""
think/answer 标签格式校验 Hook

检查 DeepSeek 返回的响应是否严格遵守 think/answer 标签格式。

规则:
  1. 必须同时包含 think 和 /think 标签
  2. 必须同时包含 answer 和 /answer 标签
  3. think 必须在 /think 之前
  4. answer 必须在 /answer 之前
  5. think 块必须在 answer 块之前
  6. 不允许嵌套标签
  7. 标签必须独立成行（前后只能是空白或换行）

用法:
  import: from src.hooks import validate_think_answer, ThinkAnswerError
  CLI:    python -m src.hooks.think_answer_validator "<response_text>"
  echo "$response" | python -m src.hooks.think_answer_validator -
"""

import re
import sys


class ThinkAnswerError(ValueError):
    """think/answer 格式错误"""
    def __init__(self, message: str, raw_content: str = ""):
        self.raw_content = raw_content
        super().__init__(message)


def validate_think_answer(content: str) -> tuple[bool, str | None, str]:
    """校验 DeepSeek 响应的 think/answer 标签格式。

    Args:
        content: LLM 原始响应全文

    Returns:
        (valid: bool, think_text: str | None, answer_text: str)

    Raises:
        ThinkAnswerError: 格式不符合规范时抛出
    """
    if not content:
        raise ThinkAnswerError("响应内容为空")

    # ── 1. 检查 think 标签对 ──
    has_think_open = "think" in content
    has_think_close = "/think" in content

    if not has_think_open and not has_think_close:
        raise ThinkAnswerError(
            "响应中缺少 think 和 /think 标签。必须使用 think/answer 标签格式输出。",
            content[:500],
        )
    if not has_think_open:
        raise ThinkAnswerError(
            "响应中缺少 'think' 开始标签。",
            content[:500],
        )
    if not has_think_close:
        raise ThinkAnswerError(
            "响应中缺少 '/think' 结束标签。",
            content[:500],
        )

    # ── 2. 检查 answer 标签对 ──
    has_answer_open = "answer" in content
    has_answer_close = "/answer" in content

    if not has_answer_open and not has_answer_close:
        raise ThinkAnswerError(
            "响应中缺少 answer 和 /answer 标签。",
            content[:500],
        )
    if not has_answer_open:
        raise ThinkAnswerError("响应中缺少 'answer' 开始标签。", content[:500])
    if not has_answer_close:
        raise ThinkAnswerError("响应中缺少 '/answer' 结束标签。", content[:500])

    # ── 3. 提取 think 块 ──
    think_start = content.index("think") + len("think")
    think_end = content.index("/think")

    if think_start >= think_end:
        raise ThinkAnswerError(
            "think 标签位置错误: 开始标签在结束标签之后。",
            content[:500],
        )

    think_text = content[think_start:think_end].strip()

    # ── 4. 提取 answer 块 ──
    answer_start = content.index("answer") + len("answer")
    answer_end = content.index("/answer")

    if answer_start >= answer_end:
        raise ThinkAnswerError(
            "answer 标签位置错误: 开始标签在结束标签之后。",
            content[:500],
        )

    answer_text = content[answer_start:answer_end].strip()

    # ── 5. think 块必须在 answer 块之前 ──
    if think_end > answer_start:
        raise ThinkAnswerError(
            "标签顺序错误: think 块必须在 answer 块之前。"
            f"think 结束于位置 {think_end}，answer 开始于位置 {answer_start}。",
            content[:500],
        )

    # ── 6. 检查嵌套 ──
    if "think" in think_text or "/think" in think_text:
        raise ThinkAnswerError("think 块内出现嵌套的 think 标签。", think_text[:200])

    if "answer" in think_text or "/answer" in think_text:
        raise ThinkAnswerError("think 块内不应出现 answer 标签。", think_text[:200])

    if "think" in answer_text or "/think" in answer_text:
        raise ThinkAnswerError("answer 块内不应出现 think 标签。", answer_text[:200])

    # ── 7. answer 块不能为空 ──
    if not answer_text:
        raise ThinkAnswerError("answer 块内容为空，必须包含对外输出。", content[:500])

    return True, think_text or None, answer_text


def _main():
    """CLI 入口: 从参数或 stdin 读取内容并校验"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "-":
            content = sys.stdin.read()
        else:
            content = sys.argv[1]
    else:
        content = sys.stdin.read()

    try:
        valid, think_text, answer_text = validate_think_answer(content)
        print(f"✓ think/answer 格式校验通过")
        print(f"  think 长度: {len(think_text or '')} 字符")
        print(f"  answer 长度: {len(answer_text)} 字符")
        return 0
    except ThinkAnswerError as e:
        print(f"✗ think/answer 格式校验失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(_main())
