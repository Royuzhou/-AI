"""
Word文档读取工具
用于读取Word文档并提取文本内容
"""

import os
from typing import Optional


def read_docx(file_path: str) -> str:
    """
    读取Word文档并提取文本内容
    
    Args:
        file_path: Word文档路径
        
    Returns:
        文档文本内容
    """
    try:
        from docx import Document
        
        doc = Document(file_path)
        
        paragraphs = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                paragraphs.append(paragraph.text)
        
        return '\n'.join(paragraphs)
    except Exception as e:
        print(f"读取Word文档失败: {e}")
        return ""


def read_docx_safe(file_path: str) -> Optional[str]:
    """
    安全读取Word文档
    
    Args:
        file_path: Word文档路径
        
    Returns:
        文档文本内容，失败时返回None
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
    
    try:
        content = read_docx(file_path)
        if content:
            return content
        else:
            print(f"文档内容为空: {file_path}")
            return None
    except Exception as e:
        print(f"读取文档时出错: {e}")
        return None


def batch_read_docx(directory: str, pattern: str = "*.docx") -> dict:
    """
    批量读取目录下的Word文档
    
    Args:
        directory: 目录路径
        pattern: 文件名模式
        
    Returns:
        字典，键为文件名，值为文档内容
    """
    import glob
    
    files = glob.glob(os.path.join(directory, pattern))
    results = {}
    
    for file_path in files:
        filename = os.path.basename(file_path)
        content = read_docx_safe(file_path)
        
        if content:
            results[filename] = content
            print(f"✓ 已读取: {filename}")
        else:
            print(f"✗ 读取失败: {filename}")
    
    return results


if __name__ == "__main__":
    test_file = "src/evaluation/CorrectContract/Contract1Correct.docx"
    if os.path.exists(test_file):
        content = read_docx(test_file)
        print(f"文档内容:\n{content}")
    else:
        print(f"测试文件不存在: {test_file}")
