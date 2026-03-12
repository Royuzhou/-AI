"""
文档提取模块
支持从PDF和Word文档中提取文本
"""

import fitz
from paddleocr import PaddleOCR
import numpy as np
from PIL import Image
import io
import PyPDF2
from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph


class DocumentExtractor:
    """文档提取器"""
    
    def __init__(self, ocr_config=None):
        """
        初始化文档提取器
        
        Args:
            ocr_config: OCR配置字典
        """
        if ocr_config is None:
            ocr_config = {
                "use_textline_orientation": True,
                "lang": "ch"
            }
        self.ocr = PaddleOCR(**ocr_config)
    
    def extract_from_word(self, file_path):
        """
        从Word文档提取文本
        
        Args:
            file_path: Word文档路径
            
        Returns:
            提取的文本内容
        """
        doc = Document(file_path)
        text_content = []
        
        def iter_blocks(parent):
            for element in parent.element.body.iterchildren():
                if isinstance(element, CT_P):
                    yield Paragraph(element, parent)
                elif isinstance(element, CT_Tbl):
                    yield Table(element, parent)
        
        for block in iter_blocks(doc):
            if isinstance(block, Paragraph):
                if block.text.strip():
                    text_content.append(block.text.strip())
            elif isinstance(block, Table):
                table_text = []
                for row in block.rows:
                    row_text = " | ".join(cell.text for cell in row.cells)
                    table_text.append(row_text)
                text_content.append("[表格]\n" + "\n".join(table_text))
        
        return "\n".join(text_content)
    
    def extract_from_pdf(self, file_path, text_threshold=50, dpi=2):
        """
        从PDF文档提取文本（自动检测类型）
        
        Args:
            file_path: PDF文档路径
            text_threshold: 文本阈值，低于此值使用OCR
            dpi: OCR识别的DPI倍数
            
        Returns:
            提取的文本内容
        """
        text_content = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text.strip() and len(text.strip()) > text_threshold:
                        text_content.append(f"[第{page_num+1}页]\n{text.strip()}")
                    else:
                        doc = fitz.open(file_path)
                        page = doc[page_num]
                        
                        mat = fitz.Matrix(dpi, dpi)
                        pix = page.get_pixmap(matrix=mat)
                        img_bytes = pix.tobytes('png')
                        
                        img = Image.open(io.BytesIO(img_bytes))
                        img_array = np.array(img)
                        
                        result = self.ocr.predict(img_array)
                        
                        if result and result[0]:
                            texts = result[0]['rec_texts']
                            ocr_text = "\n".join(texts)
                            text_content.append(f"[第{page_num+1}页-OCR]\n{ocr_text}")
                        doc.close()
        except Exception as e:
            print(f"PDF提取错误: {e}")
            return ""
        
        return "\n".join(text_content)
    
    def extract(self, file_path, **kwargs):
        """
        智能提取文档内容（自动识别PDF或Word）
        
        Args:
            file_path: 文档路径
            **kwargs: 其他参数
            
        Returns:
            提取的文本内容
        """
        if file_path.lower().endswith('.docx'):
            return self.extract_from_word(file_path)
        elif file_path.lower().endswith('.pdf'):
            return self.extract_from_pdf(file_path, **kwargs)
        else:
            raise ValueError("不支持的文件格式，仅支持 .docx 和 .pdf")