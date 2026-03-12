"""
使用改进评估指标的批量评估脚本
"""

import os
import sys
import json
from typing import Dict, List
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.evaluation.improved_evaluator import ImprovedContractEvaluator
from src.evaluation.docx_reader import read_docx_safe


def load_contracts(base_dir: str) -> Dict[str, Dict[str, str]]:
    """
    加载所有合同文件
    
    Args:
        base_dir: 评估目录路径
        
    Returns:
        合同数据字典，格式为 {case_id: {'original': str, 'revised': str, 'reference': str}}
    """
    correct_dir = os.path.join(base_dir, 'CorrectContract')
    incorrect_dir = os.path.join(base_dir, 'IncorrectContract')
    output_dir = os.path.join(base_dir, 'Output')
    
    contracts = {}
    
    print("=" * 80)
    print("加载合同文件")
    print("=" * 80)
    
    # 获取所有需要修订的合同文件
    incorrect_files = [f for f in os.listdir(incorrect_dir) if f.endswith('.docx')]
    
    for incorrect_file in incorrect_files:
        # 提取合同编号（例如：Contract1Incorrect.docx -> Contract1）
        case_id = incorrect_file.replace('Incorrect.docx', '')
        
        # 构建文件路径
        incorrect_path = os.path.join(incorrect_dir, incorrect_file)
        correct_file = f"{case_id}Correct.docx"
        correct_path = os.path.join(correct_dir, correct_file)
        revised_file = f"{case_id}Incorrect(Revised).docx"
        revised_path = os.path.join(output_dir, revised_file)
        
        # 读取文件
        print(f"\n处理 {case_id}:")
        
        original = read_docx_safe(incorrect_path)
        if not original:
            print(f"  ✗ 无法读取原始合同: {incorrect_file}")
            continue
        
        print(f"  ✓ 原始合同: {incorrect_file}")
        
        revised = read_docx_safe(revised_path)
        if not revised:
            print(f"  ✗ 无法读取修订合同: {revised_file}")
            continue
        
        print(f"  ✓ 修订合同: {revised_file}")
        
        reference = read_docx_safe(correct_path)
        if reference:
            print(f"  ✓ 参考合同: {correct_file}")
        else:
            print(f"  ⚠ 参考合同不存在: {correct_file}")
        
        contracts[case_id] = {
            'original': original,
            'revised': revised,
            'reference': reference,
            'case_name': case_id
        }
    
    print(f"\n✓ 成功加载 {len(contracts)} 个合同\n")
    return contracts


def evaluate_contracts(contracts: Dict[str, Dict[str, str]], output_dir: str) -> Dict:
    """
    评估所有合同
    
    Args:
        contracts: 合同数据字典
        output_dir: 输出目录
        
    Returns:
        批量评估结果
    """
    print("=" * 80)
    print("开始评估（使用改进的评估指标）")
    print("=" * 80)
    
    evaluator = ImprovedContractEvaluator()
    
    # 准备测试用例
    test_cases = []
    for case_id, data in contracts.items():
        test_case = {
            'name': data['case_name'],
            'original': data['original'],
            'revised': data['revised'],
            'reference': data['reference'],
            'legal_references': None,
            'suggestions': None
        }
        test_cases.append(test_case)
    
    # 执行批量评估
    print(f"\n正在评估 {len(test_cases)} 个合同...\n")
    batch_result = evaluator.batch_evaluate(test_cases)
    
    return batch_result


def generate_reports(batch_result: Dict, output_dir: str):
    """
    生成评估报告
    
    Args:
        batch_result: 批量评估结果
        output_dir: 输出目录
    """
    print("=" * 80)
    print("生成评估报告")
    print("=" * 80)
    
    # 生成文本报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f'improved_evaluation_report_{timestamp}'
    
    # 文本报告
    text_report = generate_text_report(batch_result)
    text_path = os.path.join(output_dir, f'{base_filename}.txt')
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text_report)
    print(f"\n✓ 文本报告已保存: {text_path}")
    
    # HTML报告
    html_report = generate_html_report(batch_result)
    html_path = os.path.join(output_dir, f'{base_filename}.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    print(f"✓ HTML报告已保存: {html_path}")
    
    # JSON报告
    json_path = os.path.join(output_dir, f'{base_filename}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(batch_result, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON报告已保存: {json_path}")


def generate_text_report(batch_result: Dict) -> str:
    """
    生成文本格式的评估报告
    
    Args:
        batch_result: 批量评估结果
        
    Returns:
        报告文本内容
    """
    lines = []
    lines.append("=" * 80)
    lines.append("合同修订评估报告（改进版）")
    lines.append("=" * 80)
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # 总体统计
    lines.append("【总体统计】")
    lines.append("-" * 80)
    total_cases = batch_result.get('total_cases', 0)
    lines.append(f"评估用例总数: {total_cases}")
    lines.append("")
    
    # 平均分数
    avg_scores = batch_result.get('average_scores', {})
    if avg_scores:
        lines.append("【平均分数】")
        lines.append("-" * 80)
        lines.append(f"语义相似度: {avg_scores.get('semantic_similarity', 0):.4f} (权重: 25%)")
        lines.append(f"法律条款完整性: {avg_scores.get('legal_completeness', 0):.4f} (权重: 25%)")
        lines.append(f"逻辑一致性: {avg_scores.get('logical_consistency', 0):.4f} (权重: 15%)")
        lines.append(f"语言规范性: {avg_scores.get('language_normativity', 0):.4f} (权重: 15%)")
        lines.append(f"修订合理性: {avg_scores.get('revision_rationality', 0):.4f} (权重: 20%)")
        lines.append(f"综合分数: {avg_scores.get('overall', 0):.4f}")
        lines.append("")
    
    # 详细结果
    results = batch_result.get('results', [])
    if results:
        lines.append("【详细评估结果】")
        lines.append("-" * 80)
        
        for i, result in enumerate(results, 1):
            lines.append(f"\n用例 {i}: {result.get('case_name', 'Unknown')}")
            lines.append("-" * 80)
            lines.append(f"  语义相似度: {result.get('semantic_similarity', 0):.4f}")
            lines.append(f"  法律条款完整性: {result.get('legal_completeness', 0):.4f}")
            lines.append(f"  逻辑一致性: {result.get('logical_consistency', 0):.4f}")
            lines.append(f"  语言规范性: {result.get('language_normativity', 0):.4f}")
            lines.append(f"  修订合理性: {result.get('revision_rationality', 0):.4f}")
            lines.append(f"  综合分数: {result.get('overall_score', 0):.4f}")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("报告结束")
    lines.append("=" * 80)
    
    return '\n'.join(lines)


def generate_html_report(batch_result: Dict) -> str:
    """
    生成HTML格式的评估报告
    
    Args:
        batch_result: 批量评估结果
        
    Returns:
        HTML报告内容
    """
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html lang='zh-CN'>")
    html.append("<head>")
    html.append("    <meta charset='UTF-8'>")
    html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    html.append("    <title>合同修订评估报告（改进版）</title>")
    html.append("    <style>")
    html.append("        body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }")
    html.append("        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }")
    html.append("        h1 { color: #333; text-align: center; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }")
    html.append("        h2 { color: #555; margin-top: 30px; border-left: 4px solid #4CAF50; padding-left: 10px; }")
    html.append("        .summary { background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0; }")
    html.append("        .metric { display: inline-block; margin: 10px 20px; padding: 15px; background-color: #e8f5e9; border-radius: 5px; min-width: 150px; }")
    html.append("        .metric-label { font-size: 14px; color: #666; }")
    html.append("        .metric-value { font-size: 24px; font-weight: bold; color: #4CAF50; }")
    html.append("        .metric-weight { font-size: 12px; color: #999; }")
    html.append("        table { width: 100%; border-collapse: collapse; margin: 20px 0; }")
    html.append("        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }")
    html.append("        th { background-color: #4CAF50; color: white; }")
    html.append("        tr:hover { background-color: #f5f5f5; }")
    html.append("        .score-good { color: #4CAF50; font-weight: bold; }")
    html.append("        .score-medium { color: #FF9800; font-weight: bold; }")
    html.append("        .score-poor { color: #f44336; font-weight: bold; }")
    html.append("        .timestamp { text-align: right; color: #999; font-size: 12px; }")
    html.append("    </style>")
    html.append("</head>")
    html.append("<body>")
    html.append("    <div class='container'>")
    html.append("        <h1>合同修订评估报告（改进版）</h1>")
    html.append(f"        <div class='timestamp'>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>")
    
    # 总体统计
    html.append("        <h2>总体统计</h2>")
    html.append("        <div class='summary'>")
    total_cases = batch_result.get('total_cases', 0)
    html.append(f"            <p><strong>评估用例总数:</strong> {total_cases}</p>")
    html.append("        </div>")
    
    # 平均分数
    avg_scores = batch_result.get('average_scores', {})
    if avg_scores:
        html.append("        <h2>平均分数</h2>")
        html.append("        <div class='summary'>")
        html.append(f"            <div class='metric'>")
        html.append(f"                <div class='metric-label'>语义相似度</div>")
        html.append(f"                <div class='metric-value'>{avg_scores.get('semantic_similarity', 0):.4f}</div>")
        html.append(f"                <div class='metric-weight'>权重: 25%</div>")
        html.append(f"            </div>")
        html.append(f"            <div class='metric'>")
        html.append(f"                <div class='metric-label'>法律条款完整性</div>")
        html.append(f"                <div class='metric-value'>{avg_scores.get('legal_completeness', 0):.4f}</div>")
        html.append(f"                <div class='metric-weight'>权重: 25%</div>")
        html.append(f"            </div>")
        html.append(f"            <div class='metric'>")
        html.append(f"                <div class='metric-label'>逻辑一致性</div>")
        html.append(f"                <div class='metric-value'>{avg_scores.get('logical_consistency', 0):.4f}</div>")
        html.append(f"                <div class='metric-weight'>权重: 15%</div>")
        html.append(f"            </div>")
        html.append(f"            <div class='metric'>")
        html.append(f"                <div class='metric-label'>语言规范性</div>")
        html.append(f"                <div class='metric-value'>{avg_scores.get('language_normativity', 0):.4f}</div>")
        html.append(f"                <div class='metric-weight'>权重: 15%</div>")
        html.append(f"            </div>")
        html.append(f"            <div class='metric'>")
        html.append(f"                <div class='metric-label'>修订合理性</div>")
        html.append(f"                <div class='metric-value'>{avg_scores.get('revision_rationality', 0):.4f}</div>")
        html.append(f"                <div class='metric-weight'>权重: 20%</div>")
        html.append(f"            </div>")
        html.append(f"            <div class='metric'>")
        html.append(f"                <div class='metric-label'>综合分数</div>")
        html.append(f"                <div class='metric-value'>{avg_scores.get('overall', 0):.4f}</div>")
        html.append(f"            </div>")
        html.append("        </div>")
    
    # 详细结果表格
    results = batch_result.get('results', [])
    if results:
        html.append("        <h2>详细评估结果</h2>")
        html.append("        <table>")
        html.append("            <thead>")
        html.append("                <tr>")
        html.append("                    <th>用例名称</th>")
        html.append("                    <th>语义相似度</th>")
        html.append("                    <th>法律完整性</th>")
        html.append("                    <th>逻辑一致性</th>")
        html.append("                    <th>语言规范性</th>")
        html.append("                    <th>修订合理性</th>")
        html.append("                    <th>综合分数</th>")
        html.append("                </tr>")
        html.append("            </thead>")
        html.append("            <tbody>")
        
        for result in results:
            overall_score = result.get('overall_score', 0)
            score_class = 'score-good' if overall_score >= 0.7 else ('score-medium' if overall_score >= 0.5 else 'score-poor')
            
            html.append("                <tr>")
            html.append(f"                    <td>{result.get('case_name', 'Unknown')}</td>")
            html.append(f"                    <td>{result.get('semantic_similarity', 0):.4f}</td>")
            html.append(f"                    <td>{result.get('legal_completeness', 0):.4f}</td>")
            html.append(f"                    <td>{result.get('logical_consistency', 0):.4f}</td>")
            html.append(f"                    <td>{result.get('language_normativity', 0):.4f}</td>")
            html.append(f"                    <td>{result.get('revision_rationality', 0):.4f}</td>")
            html.append(f"                    <td class='{score_class}'>{overall_score:.4f}</td>")
            html.append("                </tr>")
        
        html.append("            </tbody>")
        html.append("        </table>")
    
    html.append("    </div>")
    html.append("</body>")
    html.append("</html>")
    
    return '\n'.join(html)


def print_summary(batch_result: Dict):
    """
    打印评估摘要
    
    Args:
        batch_result: 批量评估结果
    """
    print("\n" + "=" * 80)
    print("评估摘要")
    print("=" * 80)
    
    avg_scores = batch_result.get('average_scores', {})
    results = batch_result.get('results', [])
    
    print(f"\n总测试用例数: {batch_result.get('total_cases', 0)}")
    print(f"平均综合得分: {avg_scores.get('overall', 0.0):.2%}")
    
    # 计算得分分布
    if results:
        scores = [r.get('overall_score', 0) for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        excellent = sum(1 for s in scores if s >= 0.9)
        good = sum(1 for s in scores if 0.7 <= s < 0.9)
        fair = sum(1 for s in scores if 0.5 <= s < 0.7)
        poor = sum(1 for s in scores if s < 0.5)
        
        print(f"最低得分: {min_score:.2%}")
        print(f"最高得分: {max_score:.2%}")
        
        print(f"\n得分分布:")
        print(f"  优秀 (≥90%): {excellent}")
        print(f"  良好 (70%-90%): {good}")
        print(f"  一般 (50%-70%): {fair}")
        print(f"  较差 (<50%): {poor}")
    
    print("\n" + "-" * 80)
    print("详细评估结果")
    print("-" * 80)
    
    for eval_result in results:
        case_name = eval_result.get('case_name', 'N/A')
        score = eval_result.get('overall_score', 0.0)
        print(f"\n{case_name}:")
        print(f"  综合得分: {score:.2%}")
        print(f"  语义相似度: {eval_result.get('semantic_similarity', 0):.2%}")
        print(f"  法律完整性: {eval_result.get('legal_completeness', 0):.2%}")
        print(f"  逻辑一致性: {eval_result.get('logical_consistency', 0):.2%}")
        print(f"  语言规范性: {eval_result.get('language_normativity', 0):.2%}")
        print(f"  修订合理性: {eval_result.get('revision_rationality', 0):.2%}")


def main():
    """
    主函数
    """
    print("=" * 80)
    print("合同修订系统 - 批量评估（改进版）")
    print("=" * 80)
    print()
    
    # 设置目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, 'evaluation_results')
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载合同
    contracts = load_contracts(base_dir)
    
    if not contracts:
        print("✗ 没有找到可评估的合同文件")
        return
    
    # 评估合同
    batch_result = evaluate_contracts(contracts, output_dir)
    
    # 生成报告
    generate_reports(batch_result, output_dir)
    
    # 打印摘要
    print_summary(batch_result)
    
    print("\n" + "=" * 80)
    print("评估完成！")
    print(f"所有报告已保存到: {output_dir}")
    print("=" * 80)


if __name__ == '__main__':
    main()
