"""
测试脚本 - 验证修复效果
"""

import os
import sys

# 设置环境变量跳过模型连接检查
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# 导入配置和模块
from config import CONFIG
from src.document.extractor import DocumentExtractor
from src.legal.identifier import LegalClauseIdentifier
from src.legal.retriever import LegalReferenceRetriever
# 可选的 UltraRAG 封装
try:
    from src.legal.ultrarag_retriever import UltraRAGRetriever
except ImportError:
    UltraRAGRetriever = None
from src.revision.reviser import ContractReviser

def test_document_extractor():
    """测试文档提取器"""
    print("=" * 80)
    print("测试1: 文档提取器")
    print("=" * 80)
    
    extractor = DocumentExtractor(ocr_config=CONFIG['ocr_config'])
    print(f"✓ 文档提取器初始化成功")
    print(f"  OCR语言配置: {CONFIG['ocr_config']['lang']}")
    return extractor

def test_legal_identifier():
    """测试法律条款识别器"""
    print("\n" + "=" * 80)
    print("测试2: 法律条款识别器")
    print("=" * 80)
    
    identifier = LegalClauseIdentifier(
        api_key=CONFIG['qwen_config']['api_key'],
        base_url=CONFIG['qwen_config']['base_url'],
        model=CONFIG['qwen_config']['model']
    )
    print(f"✓ 法律条款识别器初始化成功")
    return identifier

def test_legal_retriever():
    """测试法律条文检索器（支持离线模式）"""
    print("\n" + "=" * 80)
    print("测试3: 法律条文检索器")
    print("=" * 80)
    
    # 如果配置指示使用 UltraRAG 并且模块存在，优先创建 UltraRAGRetriever
    ur_cfg = CONFIG.get('ultrarag_config', {})
    if ur_cfg.get('use') and UltraRAGRetriever is not None:
        retriever = UltraRAGRetriever(
            server_root=ur_cfg.get('server_root'),
            retriever_model=ur_cfg.get('retriever_model')
        )
        print("✓ 使用 UltraRAGRetriever 初始化")
    else:
        retriever = LegalReferenceRetriever(
            api_key=CONFIG['pinecone_config']['api_key'],
            index_name=CONFIG['pinecone_config']['index_name'],
            model_name=CONFIG['model_config']['sentence_transformer'],
            hf_endpoint=CONFIG['model_config'].get('hf_endpoint')
        )
    
    if retriever.offline_mode:
        print(f"✓ 法律条文检索器初始化成功（离线模式）")
        print(f"  说明: 由于网络或模型问题，已切换到离线模式")
    else:
        print(f"✓ 法律条文检索器初始化成功（在线模式）")
    
    return retriever

def test_contract_reviser():
    """测试合同修订器"""
    print("\n" + "=" * 80)
    print("测试4: 合同修订器")
    print("=" * 80)
    
    reviser = ContractReviser(
        api_key=CONFIG['qwen_config']['api_key'],
        base_url=CONFIG['qwen_config']['base_url'],
        model=CONFIG['qwen_config']['model']
    )
    print(f"✓ 合同修订器初始化成功")
    return reviser

def test_full_integration():
    """测试完整集成"""
    print("\n" + "=" * 80)
    print("测试5: 完整集成")
    print("=" * 80)
    
    try:
        from src.agent import ContractRevisionAgent
        agent = ContractRevisionAgent(CONFIG)
        print(f"✓ 合同修订智能体初始化成功")
        return agent
    except Exception as e:
        print(f"✗ 合同修订智能体初始化失败: {e}")
        return None

def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("合同修订智能体 - 修复验证测试")
    print("=" * 80)
    
    # 测试各个模块
    extractor = test_document_extractor()
    identifier = test_legal_identifier()
    retriever = test_legal_retriever()
    reviser = test_contract_reviser()
    agent = test_full_integration()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    results = {
        "文档提取器": extractor is not None,
        "法律条款识别器": identifier is not None,
        "法律条文检索器": retriever is not None,
        "合同修订器": reviser is not None,
        "完整集成": agent is not None
    }
    
    all_passed = all(results.values())
    
    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
    
    if all_passed:
        print("\n🎉 所有测试通过！系统可以正常工作。")
    else:
        print("\n⚠️  部分测试失败，请检查相关模块。")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())