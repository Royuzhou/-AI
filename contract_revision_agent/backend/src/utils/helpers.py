"""
工具模块
提供通用的辅助函数
"""

import os
from datetime import datetime


def ensure_dir(directory):
    """
    确保目录存在，不存在则创建
    
    Args:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_timestamp():
    """
    获取当前时间戳
    
    Returns:
        格式化的时间戳字符串
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def generate_output_filename(input_file, suffix="_revised"):
    """
    生成输出文件名
    
    Args:
        input_file: 输入文件名
        suffix: 后缀
        
    Returns:
        输出文件名
    """
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = get_timestamp()
    return f"{base_name}{suffix}_{timestamp}.txt"


def print_section(title):
    """
    打印章节标题
    
    Args:
        title: 标题文本
    """
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_step(step_num, description):
    """
    打印步骤信息
    
    Args:
        step_num: 步骤编号
        description: 步骤描述
    """
    print(f"\n[步骤{step_num}] {description}")


def print_success(message):
    """
    打印成功信息
    
    Args:
        message: 消息文本
    """
    print(f"✓ {message}")


def print_error(message):
    """
    打印错误信息
    
    Args:
        message: 消息文本
    """
    print(f"✗ {message}")


def print_warning(message):
    """
    打印警告信息
    
    Args:
        message: 消息文本
    """
    print(f"⚠ {message}")