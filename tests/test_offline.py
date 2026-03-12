"""
合同修订智能体 - 离线测试脚本
测试不依赖网络的基本功能
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """测试模块导入"""
    print("=" * 80)
    print("测试1: 模块导入")
    print("=" * 80)
    
    try:
        from src.document.extractor import DocumentExtractor
        print("✓ DocumentExtractor 导入成功")
    except Exception as e:
        print(f"✗ DocumentExtractor 导入失败: {e}")
        return False
    
    try:
        from src.legal.identifier import LegalClauseIdentifier
        print("✓ LegalClauseIdentifier 导入成功")
    except Exception as e:
        print(f"✗ LegalClauseIdentifier 导入失败: {e}")
        return False
    
    try:
        from src.legal.retriever import LegalReferenceRetriever
        print("✓ LegalReferenceRetriever 导入成功")
    except Exception as e:
        print(f"✗ LegalReferenceRetriever 导入失败: {e}")
        return False
    # UltraRAG 相关导入
    try:
        from src.legal.ultrarag_retriever import UltraRAGRetriever
        print("✓ UltraRAGRetriever 导入成功 (如果未安装 UltraRAG 则会跳过)")
    except Exception as e:
        print(f"⚠ UltraRAGRetriever 导入失败: {e}")
    
    try:
        from src.revision.reviser import ContractReviser
        print("✓ ContractReviser 导入成功")
    except Exception as e:
        print(f"✗ ContractReviser 导入失败: {e}")
        return False
    
    try:
        from src.agent import ContractRevisionAgent
        print("✓ ContractRevisionAgent 导入成功")
    except Exception as e:
        print(f"✗ ContractRevisionAgent 导入失败: {e}")
        return False
    
    try:
        from config import CONFIG
        print("✓ CONFIG 导入成功")
    except Exception as e:
        print(f"✗ CONFIG 导入失败: {e}")
        return False
    
    print("\n✓ 所有模块导入成功\n")
    return True


def test_config_structure():
    """测试配置结构"""
    print("=" * 80)
    print("测试2: 配置结构")
    print("=" * 80)
    
    try:
        from config import CONFIG
        
        required_keys = [
            "qwen_config",
            "pinecone_config",
            "model_config",
            "ocr_config",
            "text_config",
            "legal_categories",
            "output_dir"
        ]
        
        for key in required_keys:
            if key in CONFIG:
                print(f"✓ {key} 配置存在")
            else:
                print(f"✗ {key} 配置缺失")
                return False
        
        # 检查子配置
        if "api_key" in CONFIG["qwen_config"]:
            print("✓ Qwen API配置完整")
        else:
            print("✗ Qwen API配置不完整")
            return False
        
        if "api_key" in CONFIG["pinecone_config"]:
            print("✓ Pinecone API配置完整")
        else:
            print("✗ Pinecone API配置不完整")
            return False
        
        print("\n✓ 配置结构正确\n")
        return True
    except Exception as e:
        print(f"✗ 配置检查失败: {e}\n")
        return False


def test_ultrarag_config():
    """检查 UltraRAG 配置是否存在并合理"""
    print("=" * 80)
    print("测试5: UltraRAG 配置")
    print("=" * 80)
    try:
        from config import CONFIG
        ur = CONFIG.get("ultrarag_config", {})
        if "use" in ur:
            print(f"✓ ultrarag_config.use = {ur['use']}")
        else:
            print("✗ ultrarag_config 缺少 'use' 字段")
            return False
        # server_root 可以为空（默认不启用），这里只验证键存在即可
        if "server_root" in ur:
            print("✓ ultrarag_config.server_root 字段存在")
        else:
            print("✗ ultrarag_config 缺少 'server_root'")
            return False
        print("\n✓ UltraRAG 配置检查完成\n")
        return True
    except Exception as e:
        print(f"✗ UltraRAG 配置检查失败: {e}\n")
        return False


def test_document_extractor():
    """测试文档提取器初始化"""
    print("=" * 80)
    print("测试3: 文档提取器初始化")
    print("=" * 80)
    
    try:
        from src.document.extractor import DocumentExtractor
        from config import CONFIG
        
        extractor = DocumentExtractor(ocr_config=CONFIG.get('ocr_config'))
        print("✓ DocumentExtractor 初始化成功")
        print(f"✓ PaddleOCR 已加载")
        
        print("\n✓ 文档提取器测试通过\n")
        return True
    except Exception as e:
        print(f"✗ 文档提取器测试失败: {e}\n")
        return False


def test_file_structure():
    """测试文件结构"""
    print("=" * 80)
    print("测试4: 文件结构")
    print("=" * 80)
    
    required_files = [
        "config.py",
        "main.py",
        "requirements.txt",
        "README.md",
        "src/__init__.py",
        "src/agent.py",
        "src/document/__init__.py",
        "src/document/extractor.py",
        "src/legal/__init__.py",
        "src/legal/identifier.py",
        "src/legal/retriever.py",
        "src/revision/__init__.py",
        "src/revision/reviser.py",
        "src/utils/__init__.py",
        "src/utils/helpers.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False
    
    if all_exist:
        print("\n✓ 文件结构完整\n")
    else:
        print("\n✗ 部分文件缺失\n")
    
    return all_exist


def run_offline_tests():
    """运行离线测试"""
    print("\n" + "=" * 80)
    print("合同修订智能体 - 离线功能测试")
    print("=" * 80 + "\n")
    
    results = []
    
    # 运行各个测试
    results.append(("模块导入", test_imports()))
    results.append(("配置结构", test_config_structure()))
    results.append(("文档提取器", test_document_extractor()))
    results.append(("文件结构", test_file_structure()))
    results.append(("UltraRAG 配置", test_ultrarag_config()))
    
    # 总结
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("所有离线测试通过！系统基础功能正常。")
        print("\n注意：以下功能需要网络连接，未在此测试中验证：")
        print("- Pinecone向量数据库查询")
        print("- Qwen3-Max大模型API调用")
        print("- HuggingFace模型下载")
    else:
        print("部分测试失败，请检查错误信息。")
    print("=" * 80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    run_offline_tests()
