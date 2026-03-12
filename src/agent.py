"""
合同修订智能体 - 主程序
整合所有模块提供完整的合同修订功能
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.document.extractor import DocumentExtractor
from src.legal.identifier import LegalClauseIdentifier
try:
    # 如果配置启用了 UltraRAG，我们会使用 UltraRAGRetriever
    from src.legal.ultrarag_retriever import UltraRAGRetriever
except ImportError:
    UltraRAGRetriever = None

from src.legal.retriever import LegalReferenceRetriever
from src.revision.reviser import ContractReviser
from src.utils.helpers import (
    print_section, print_step, print_success, 
    print_error, print_warning, generate_output_filename
)


class ContractRevisionAgent:
    """合同修订智能体"""
    
    def __init__(self, config):
        """
        初始化合同修订智能体
        
        Args:
            config: 配置字典
        """
        self.config = config
        
        # 初始化各个模块
        self.document_extractor = DocumentExtractor(
            ocr_config=config.get('ocr_config')
        )
        
        self.legal_identifier = LegalClauseIdentifier(
            api_key=config['qwen_config']['api_key'],
            base_url=config['qwen_config']['base_url'],
            model=config['qwen_config']['model']
        )
        
        # 根据配置选择检索器实现
        ur_cfg = config.get('ultrarag_config', {})
        if ur_cfg.get('use') and UltraRAGRetriever is not None:
            self.legal_retriever = UltraRAGRetriever(
                server_root=ur_cfg.get('server_root'),
                retriever_model=ur_cfg.get('retriever_model')
            )
        else:
            self.legal_retriever = LegalReferenceRetriever(
                api_key=config['pinecone_config']['api_key'],
                index_name=config['pinecone_config']['index_name'],
                model_name=config['model_config']['sentence_transformer'],
                hf_endpoint=config['model_config'].get('hf_endpoint')
            )
        
        self.contract_reviser = ContractReviser(
            api_key=config['qwen_config']['api_key'],
            base_url=config['qwen_config']['base_url'],
            model=config['qwen_config']['model']
        )
    
    def process_contract(self, input_file, output_dir=None, output_file=None):
        """
        处理合同文件
        
        Args:
            input_file: 输入合同文件路径
            output_dir: 输出目录
            output_file: 输出文件名（可选）
            
        Returns:
            修订后的合同文本
        """
        print_section("开始处理合同")
        
        # 检查输入文件
        if not os.path.exists(input_file):
            print_error(f"找不到文件: {input_file}")
            return None
        
        # 确定输出路径
        if output_dir is None:
            output_dir = self.config.get('output_dir', 'data/outputs')
        
        if output_file is None:
            output_file = generate_output_filename(input_file)
        
        output_path = os.path.join(output_dir, output_file)
        
        # 步骤1: 提取合同文本
        print_step(1, "提取合同文本")
        try:
            contract_text = self.document_extractor.extract(input_file)
            print_success(f"合同文本提取完成，共 {len(contract_text)} 字符")
        except Exception as e:
            print_error(f"合同文本提取失败: {e}")
            return None
        
        # 步骤2: 识别法律条款
        print_step(2, "识别合同中的法律条款")
        try:
            legal_clauses_text = self.legal_identifier.identify(contract_text)
            print_success("法律条款识别完成")
            print(legal_clauses_text)
        except Exception as e:
            print_error(f"法律条款识别失败: {e}")
            return None
        
        # 提取法律条款列表
        legal_clauses = self.legal_identifier.extract_clauses(legal_clauses_text)
        print_success(f"共识别出 {len(legal_clauses)} 条法律相关条款")
        
        # 步骤3: 查询相关法律条文
        print_step(3, "查询相关法律条文")
        try:
            top_k = self.config['pinecone_config'].get('top_k', 3)
            legal_references = self.legal_retriever.query(legal_clauses, top_k=top_k)
            
            if not legal_references:
                print_warning("未获取到法律条文参考，将基于原始合同进行修订")
            else:
                print_success(f"查询完成，获得 {len(legal_references)} 条相关法律条文")
                
                for ref in legal_references:
                    print(f"\n- 条款: {ref['clause'][:50]}...")
                    print(f"  参考条文: {ref['reference'][:80]}...")
                    print(f"  相似度: {ref['score']:.2f}")
        except Exception as e:
            print_error(f"法律条文查询失败: {e}")
            print_warning("将跳过法律条文查询，基于原始合同进行修订")
            legal_references = []
        
        # 步骤4: 生成修订后的合同
        print_step(4, "生成修订后的合同")
        try:
            revised_contract = self.contract_reviser.revise(
                contract_text, 
                legal_references
            )
            print_success("合同修订完成")
        except Exception as e:
            print_error(f"合同修订失败: {e}")
            return None
        
        # 输出结果
        print_section("修订结果")
        print(revised_contract)
        
        # 保存到文件
        try:
            self.contract_reviser.save_revised_contract(revised_contract, output_path)
            print_success(f"结果已保存到: {output_path}")
        except Exception as e:
            print_error(f"保存文件失败: {e}")
        
        return revised_contract