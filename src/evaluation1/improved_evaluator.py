from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import re

from .metrics import (
    calculate_similarity,
    calculate_bleu,
    calculate_rouge_l,
    calculate_precision_recall_f1
)


@dataclass
class EvaluationResult:
    """
    评估结果数据类
    """
    case_name: str
    semantic_similarity: float
    legal_completeness: float
    logical_consistency: float
    language_normativity: float
    revision_rationality: float
    overall_score: float
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            字典格式的评估结果
        """
        return {
            'case_name': self.case_name,
            'semantic_similarity': self.semantic_similarity,
            'legal_completeness': self.legal_completeness,
            'logical_consistency': self.logical_consistency,
            'language_normativity': self.language_normativity,
            'revision_rationality': self.revision_rationality,
            'overall_score': self.overall_score,
            'details': self.details
        }


class ImprovedContractEvaluator:
    """
    改进的合同评估器，使用更适合合同修订的评估指标
    """
    
    def __init__(self):
        """
        初始化评估器
        """
        self.weights = {
            'semantic_similarity': 0.25,
            'legal_completeness': 0.25,
            'logical_consistency': 0.15,
            'language_normativity': 0.15,
            'revision_rationality': 0.20
        }
    
    def evaluate(
        self,
        original: str,
        revised: str,
        reference: Optional[str] = None,
        legal_references: Optional[List[str]] = None,
        suggestions: Optional[List[Dict[str, Any]]] = None
    ) -> EvaluationResult:
        """
        评估单个合同的修订结果
        
        Args:
            original: 原始合同文本
            revised: 修订后的合同文本
            reference: 参考合同文本（可选）
            legal_references: 法律参考列表（可选）
            suggestions: 改写建议列表（可选）
            
        Returns:
            评估结果对象
        """
        # 计算语义相似度
        semantic_similarity = self._calculate_semantic_similarity(
            original,
            revised,
            reference
        )
        
        # 计算法律条款完整性
        legal_completeness = self._calculate_legal_completeness(revised)
        
        # 计算逻辑一致性
        logical_consistency = self._calculate_logical_consistency(
            original,
            revised
        )
        
        # 计算语言规范性
        language_normativity = self._calculate_language_normativity(revised)
        
        # 计算修订合理性
        revision_rationality = self._calculate_revision_rationality(
            original,
            revised,
            suggestions
        )
        
        # 计算综合分数
        overall_score = (
            self.weights['semantic_similarity'] * semantic_similarity +
            self.weights['legal_completeness'] * legal_completeness +
            self.weights['logical_consistency'] * logical_consistency +
            self.weights['language_normativity'] * language_normativity +
            self.weights['revision_rationality'] * revision_rationality
        )
        
        # 构建详细信息
        details = {
            'semantic_metrics': {
                'similarity': semantic_similarity
            },
            'legal_metrics': {
                'completeness': legal_completeness
            },
            'logic_metrics': {
                'consistency': logical_consistency
            },
            'language_metrics': {
                'normativity': language_normativity
            },
            'revision_metrics': {
                'rationality': revision_rationality
            }
        }
        
        return EvaluationResult(
            case_name="Single Evaluation",
            semantic_similarity=semantic_similarity,
            legal_completeness=legal_completeness,
            logical_consistency=logical_consistency,
            language_normativity=language_normativity,
            revision_rationality=revision_rationality,
            overall_score=overall_score,
            details=details
        )
    
    def _calculate_semantic_similarity(
        self,
        original: str,
        revised: str,
        reference: Optional[str] = None
    ) -> float:
        """
        计算语义相似度（基于关键词和结构）
        
        Args:
            original: 原始合同
            revised: 修订后的合同
            reference: 参考合同
            
        Returns:
            语义相似度分数（0-1之间）
        """
        if not revised:
            return 0.0
        
        # 提取关键实体
        original_entities = self._extract_entities(original)
        revised_entities = self._extract_entities(revised)
        
        # 计算实体重叠度
        entity_overlap = len(original_entities & revised_entities) / len(original_entities) if original_entities else 0.0
        
        # 提取关键条款
        original_clauses = self._extract_clauses(original)
        revised_clauses = self._extract_clauses(revised)
        
        # 计算条款相似度
        clause_similarity = calculate_similarity(
            ' '.join(original_clauses),
            ' '.join(revised_clauses)
        )
        
        # 综合评分
        semantic_score = (entity_overlap * 0.4 + clause_similarity * 0.6)
        
        return semantic_score
    
    def _extract_entities(self, text: str) -> set:
        """
        提取文本中的关键实体
        
        Args:
            text: 文本内容
            
        Returns:
            实体集合
        """
        entities = set()
        
        # 提取金额
        amounts = re.findall(r'[\d,]+\.?\d*[元万千百十]', text)
        entities.update(amounts)
        
        # 提取日期
        dates = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日', text)
        entities.update(dates)
        
        # 提取公司名称
        companies = re.findall(r'[A-Za-z\u4e00-\u9fa5]+(?:有限公司|股份公司|集团|公司)', text)
        entities.update(companies)
        
        # 提取地点
        locations = re.findall(r'[A-Za-z\u4e00-\u9fa5]+(?:省|市|区|县|路|号)', text)
        entities.update(locations)
        
        return entities
    
    def _extract_clauses(self, text: str) -> List[str]:
        """
        提取合同条款
        
        Args:
            text: 合同文本
            
        Returns:
            条款列表
        """
        clauses = []
        
        # 匹配条款标题
        clause_pattern = r'(?:第[一二三四五六七八九十百千万\d]+条|第\d+章|第\d+节)'
        matches = re.finditer(clause_pattern, text)
        
        for match in matches:
            start = match.start()
            clauses.append(match.group())
        
        return clauses
    
    def _calculate_legal_completeness(self, text: str) -> float:
        """
        计算法律条款完整性
        
        Args:
            text: 合同文本
            
        Returns:
            完整性分数（0-1之间）
        """
        if not text:
            return 0.0
        
        # 必要的法律条款
        required_clauses = {
            '合同主体': ['甲方', '乙方', '双方'],
            '权利义务': ['权利', '义务', '责任'],
            '违约责任': ['违约', '赔偿', '责任'],
            '争议解决': ['争议', '仲裁', '诉讼', '法院'],
            '合同期限': ['期限', '时间', '有效期', '至'],
            '合同金额': ['金额', '费用', '价格', '元']
        }
        
        total_score = 0.0
        
        for clause_type, keywords in required_clauses.items():
            clause_score = 0.0
            for keyword in keywords:
                if keyword in text:
                    clause_score += 1.0
            
            # 归一化
            clause_score = min(clause_score / len(keywords), 1.0)
            total_score += clause_score
        
        # 计算平均分
        completeness = total_score / len(required_clauses)
        
        return completeness
    
    def _calculate_logical_consistency(
        self,
        original: str,
        revised: str
    ) -> float:
        """
        计算逻辑一致性
        
        Args:
            original: 原始合同
            revised: 修订后的合同
            
        Returns:
            一致性分数（0-1之间）
        """
        if not revised:
            return 0.0
        
        consistency_score = 0.0
        
        # 检查关键信息是否一致
        original_entities = self._extract_entities(original)
        revised_entities = self._extract_entities(revised)
        
        # 计算实体保留率
        if original_entities:
            entity_retention = len(original_entities & revised_entities) / len(original_entities)
            consistency_score += entity_retention * 0.4
        
        # 检查条款编号是否连续
        clause_numbers = re.findall(r'第([一二三四五六七八九十百千万\d]+)条', revised)
        if clause_numbers:
            # 简单检查：条款编号不重复
            unique_numbers = len(set(clause_numbers))
            total_numbers = len(clause_numbers)
            if total_numbers > 0:
                clause_consistency = unique_numbers / total_numbers
                consistency_score += clause_consistency * 0.3
        
        # 检查引用一致性
        references = re.findall(r'第([一二三四五六七八九十百千万\d]+)条', revised)
        if references:
            # 检查引用的条款是否存在
            all_clauses = set(clause_numbers)
            valid_refs = sum(1 for ref in references if ref in all_clauses)
            if references:
                ref_consistency = valid_refs / len(references)
                consistency_score += ref_consistency * 0.3
        
        return min(consistency_score, 1.0)
    
    def _calculate_language_normativity(self, text: str) -> float:
        """
        计算语言规范性
        
        Args:
            text: 合同文本
            
        Returns:
            规范性分数（0-1之间）
        """
        if not text:
            return 0.0
        
        normativity_score = 0.0
        
        # 检查法律术语使用
        legal_terms = [
            '甲方', '乙方', '双方', '当事人',
            '权利', '义务', '责任',
            '违约', '赔偿', '损失',
            '争议', '解决', '仲裁', '诉讼',
            '合同', '协议', '条款',
            '应当', '必须', '不得', '可以',
            '约定', '规定', '确认'
        ]
        
        term_count = sum(1 for term in legal_terms if term in text)
        term_score = min(term_count / len(legal_terms), 1.0)
        normativity_score += term_score * 0.4
        
        # 检查标点符号使用
        punctuation_score = 0.0
        if '。' in text:
            punctuation_score += 0.3
        if '，' in text:
            punctuation_score += 0.3
        if '：' in text:
            punctuation_score += 0.2
        if '；' in text:
            punctuation_score += 0.2
        normativity_score += punctuation_score * 0.3
        
        # 检查格式规范性
        format_score = 0.0
        if re.search(r'第[一二三四五六七八九十百千万\d]+条', text):
            format_score += 0.5
        if re.search(r'合同编号|合同编号：|合同编号:', text):
            format_score += 0.25
        if re.search(r'签订日期|签订日期：|签订日期:', text):
            format_score += 0.25
        normativity_score += format_score * 0.3
        
        return normativity_score
    
    def _calculate_revision_rationality(
        self,
        original: str,
        revised: str,
        suggestions: Optional[List[Dict[str, Any]]] = None
    ) -> float:
        """
        计算修订合理性
        
        Args:
            original: 原始合同
            revised: 修订后的合同
            suggestions: 改写建议
            
        Returns:
            合理性分数（0-1之间）
        """
        if not revised:
            return 0.0
        
        rationality_score = 0.0
        
        # 检查修订是否改善了问题
        # 比较修订前后的法律完整性
        original_completeness = self._calculate_legal_completeness(original)
        revised_completeness = self._calculate_legal_completeness(revised)
        
        if revised_completeness >= original_completeness:
            improvement_score = (revised_completeness - original_completeness) * 2 + 0.5
            rationality_score += min(improvement_score, 1.0) * 0.4
        else:
            rationality_score += 0.2
        
        # 检查修订是否增加了必要的条款
        original_clauses = len(self._extract_clauses(original))
        revised_clauses = len(self._extract_clauses(revised))
        
        if revised_clauses >= original_clauses:
            clause_rationality = min(revised_clauses / original_clauses, 1.5) / 1.5
            rationality_score += clause_rationality * 0.3
        else:
            rationality_score += 0.2
        
        # 检查修订是否保持了核心内容
        semantic_similarity = self._calculate_semantic_similarity(original, revised, None)
        rationality_score += semantic_similarity * 0.3
        
        return min(rationality_score, 1.0)
    
    def batch_evaluate(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量评估多个测试用例
        
        Args:
            test_cases: 测试用例列表，每个用例包含：
                - name: 用例名称
                - original: 原始合同
                - revised: 修订后的合同
                - reference: 参考合同（可选）
                - legal_references: 法律参考（可选）
                - suggestions: 改写建议（可选）
                
        Returns:
            批量评估结果字典
        """
        results = []
        
        for test_case in test_cases:
            result = self.evaluate(
                original=test_case.get('original', ''),
                revised=test_case.get('revised', ''),
                reference=test_case.get('reference'),
                legal_references=test_case.get('legal_references'),
                suggestions=test_case.get('suggestions')
            )
            
            result.case_name = test_case.get('name', 'Unknown')
            results.append(result)
        
        # 计算平均分数
        avg_scores = self._calculate_average_scores(results)
        
        return {
            'results': [r.to_dict() for r in results],
            'average_scores': avg_scores,
            'total_cases': len(results)
        }
    
    def _calculate_average_scores(
        self,
        results: List[EvaluationResult]
    ) -> Dict[str, float]:
        """
        计算平均分数
        
        Args:
            results: 评估结果列表
            
        Returns:
            平均分数字典
        """
        if not results:
            return {}
        
        avg_scores = {
            'semantic_similarity': sum(r.semantic_similarity for r in results) / len(results),
            'legal_completeness': sum(r.legal_completeness for r in results) / len(results),
            'logical_consistency': sum(r.logical_consistency for r in results) / len(results),
            'language_normativity': sum(r.language_normativity for r in results) / len(results),
            'revision_rationality': sum(r.revision_rationality for r in results) / len(results),
            'overall': sum(r.overall_score for r in results) / len(results)
        }
        
        return avg_scores
