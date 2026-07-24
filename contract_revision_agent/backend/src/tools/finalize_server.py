"""revision-finalizer MCP Server — 结果持久化 + 格式校验"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.mcp import SimpleMCPServer
from src.hooks import validate_revision_format

server = SimpleMCPServer("revision-finalizer", version="1.0.0")


@server.tool()
async def finalize_revision(revised_content: str, output_path: str) -> str:
    """保存修订结果。每条修改必须用以下标签格式:
    §CHANGE
    §ORIGINAL (合同原文)
    §LAW (RAG检索的法律条文)
    §SUGGESTION (修改建议+理由+法条依据)
    §REVISED (修改后文本)
    §END

    整体须含【修订后的完整合同】和【修改建议清单】。格式不符拒绝保存。"""
    if not revised_content:
        return "保存失败: 修订内容为空。"
    if not output_path:
        return "保存失败: 缺少输出路径。"

    valid, errors = validate_revision_format(revised_content)
    if not valid:
        return ("格式校验失败！请修正后重新调用:\n" +
                "\n".join(f"  - {e}" for e in errors))

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(revised_content)
        return f"格式校验通过，已保存到: {output_path}"
    except Exception as e:
        return f"文件保存失败: {e}"


if __name__ == "__main__":
    server.run_sync()
