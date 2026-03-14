"""
Document Extractor Server - 文档提取服务
支持 PDF 和 Word 文档的文本提取，包含 OCR 功能
"""

from typing import Dict
import PyPDF2
from docx import Document
from pathlib import Path

try:
    from paddleocr import PaddleOCR
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("警告：PaddleOCR 未安装，PDF 扫描件将无法处理")

from ultrarag.server import UltraRAG_MCP_Server

app = UltraRAG_MCP_Server("doc_extractor")


def extract_from_word(file_path: str) -> str:
    """从 Word 文档提取文本"""
    doc = Document(file_path)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return "\n".join(text)


def extract_from_pdf(file_path: str, use_ocr: bool = False) -> str:
    """
    从 PDF 提取文本
    
    Args:
        file_path: PDF 文件路径
        use_ocr: 是否使用 OCR (用于扫描件)
    
    Returns:
        提取的文本内容
    """
    if use_ocr and OCR_AVAILABLE:
        # 使用 OCR 处理扫描件
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        result = ocr.ocr(file_path, cls=True)
        text = []
        for idx, res in enumerate(result):
            if res:
                for line in res:
                    text.append(line[1][0])
        return "\n".join(text)
    else:
        # 使用 PyPDF2 提取文本型 PDF
        text = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return "\n".join(text)


@app.tool(output="file_path->text")
def extract_text(file_path: str, use_ocr: bool = False) -> Dict[str, str]:
    """
    从文档文件中提取文本
    
    Args:
        file_path: 文档文件路径 (PDF 或 Word)
        use_ocr: 是否对 PDF 使用 OCR(默认 False，如为 True 可处理扫描件)
    
    Returns:
        包含'extracted_text'键的字典
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {"error": f"文件不存在：{file_path}"}
        
        # 根据文件类型选择提取方法
        if path.suffix.lower() == '.docx':
            text = extract_from_word(str(path))
        elif path.suffix.lower() == '.pdf':
            text = extract_from_pdf(str(path), use_ocr=use_ocr)
        else:
            # 尝试作为文本文件读取
            text = path.read_text(encoding='utf-8')
        
        app.logger.info(f"成功提取文本，共{len(text)}字符")
        return {"extracted_text": text}
        
    except Exception as e:
        app.logger.error(f"文本提取失败：{e}")
        return {"error": str(e)}


if __name__ == "__main__":
    app.run(transport="stdio")
