"""
document-extractor MCP Server

通过 MCP/stdio 协议提供文档提取工具。
底层: DocumentExtractor (PaddleOCR + PyMuPDF + python-docx)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.mcp import SimpleMCPServer
from config import OCR_CONFIG
from src.document.extractor import DocumentExtractor

server = SimpleMCPServer("document-extractor", version="1.0.0")

# 初始化提取器（模块级，复用）
_extractor = DocumentExtractor(ocr_config=OCR_CONFIG)


@server.tool()
async def extract_document(file_path: str) -> str:
    """从合同文件（PDF/DOCX）中提取原始文本。

    必须先调用此工具获取合同全文后才能进行后续的法律分析和修订。
    支持 .docx 和 .pdf 格式，PDF 自动检测是否为扫描件并启用 OCR。

    Args:
        file_path: 合同文件的完整路径
    """
    if not os.path.exists(file_path):
        return f"错误: 找不到文件 '{file_path}'"
    try:
        text = _extractor.extract(file_path)
        return text
    except Exception as e:
        return f"文档提取失败: {e}"


if __name__ == "__main__":
    server.run_sync()
