"""
合同修订智能体 - 简化测试脚本
验证系统基本功能
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent import ContractRevisionAgent
from config import CONFIG


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
    # 尝试导入 UltraRAG 封装，如果启用了配置则此模块应存在
    try:
        from src.legal.ultrarag_retriever import UltraRAGRetriever
        print("✓ UltraRAGRetriever 导入成功")
    except Exception as e:
        print(f"⚠ UltraRAGRetriever 导入失败: {e}")
    
    try:
        from src.revision.reviser import ContractReviser
        print("✓ ContractReviser 导入成功")
    except Exception as e:
        print(f"✗ ContractReviser 导入失败: {e}")
        return False
    
    print("✓ 所有模块导入成功\n")
    return True


def test_agent_initialization():
    """测试智能体初始化"""
    print("=" * 80)
    print("测试2: 智能体初始化")
    print("=" * 80)
    
    try:
        agent = ContractRevisionAgent(CONFIG)
        print("✓ 智能体初始化成功")
        print(f"✓ 文档提取器已初始化")
        print(f"✓ 法律条款识别器已初始化")
        print(f"✓ 法律条文检索器已初始化 ({agent.legal_retriever.__class__.__name__})")
        print(f"✓ 合同修订器已初始化\n")
        return True
    except Exception as e:
        print(f"✗ 智能体初始化失败: {e}\n")
        return False


def test_document_extraction():
    """测试文档提取功能"""
    print("=" * 80)
    print("测试3: 文档提取功能")
    print("=" * 80)
    
    agent = ContractRevisionAgent(CONFIG)
    
    # 测试Word文档提取
    if os.path.exists("contract.docx"):
        print("\n测试Word文档提取...")
        try:
            text = agent.document_extractor.extract_from_word("contract.docx")
            print(f"✓ Word文档提取成功，共 {len(text)} 字符")
            print(f"  前100个字符: {text[:100]}...")
        except Exception as e:
            print(f"✗ Word文档提取失败: {e}")
            return False
    else:
        print("⚠ contract.docx 不存在，跳过Word文档测试")
    
    # 测试PDF文档提取
    if os.path.exists("AI Legal Assistant for Contract Revision.pdf"):
        print("\n测试PDF文档提取...")
        try:
            text = agent.document_extractor.extract_from_pdf("AI Legal Assistant for Contract Revision.pdf")
            print(f"✓ PDF文档提取成功，共 {len(text)} 字符")
            print(f"  前100个字符: {text[:100]}...")
        except Exception as e:
            print(f"✗ PDF文档提取失败: {e}")
            return False
    else:
        print("⚠ PDF文件不存在，跳过PDF文档测试")
    
    print("\n✓ 文档提取功能测试完成\n")
    return True


def test_pinecone_query():
    """测试Pinecone查询功能"""
    print("=" * 80)
    print("测试4: Pinecone查询功能")
    print("=" * 80)
    
    agent = ContractRevisionAgent(CONFIG)
    
    test_clauses = [
        "海关依照本办法对进出保税区的货物、运输工具、个人携带物品实施监管"
    ]
    
    print("\n测试查询条款:")
    for i, clause in enumerate(test_clauses, 1):
        print(f"{i}. {clause}")
    
    print("\n查询结果:")
    
    try:
        results = agent.legal_retriever.query(test_clauses, top_k=2)
        for i, ref in enumerate(results, 1):
            print(f"\n结果 {i}:")
            print(f"  条款: {ref['clause'][:50]}...")
            print(f"  参考条文: {ref['reference'][:80]}...")
            print(f"  相似度: {ref['score']:.2f}")
        
        print("\n✓ Pinecone查询功能测试完成\n")
        return True
    except Exception as e:
        print(f"✗ Pinecone查询失败: {e}\n")
        return False


def run_basic_tests():
    """运行基础测试"""
    print("\n" + "=" * 80)
    print("合同修订智能体 - 基础功能测试")
    print("=" * 80 + "\n")
    
    results = []
    
    # 运行各个测试
    results.append(("模块导入", test_imports()))
    results.append(("智能体初始化", test_agent_initialization()))
    results.append(("文档提取", test_document_extraction()))
    results.append(("Pinecone查询", test_pinecone_query()))
    
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
        print("所有测试通过！系统运行正常。")
    else:
        print("部分测试失败，请检查错误信息。")
    print("=" * 80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    run_basic_tests()
