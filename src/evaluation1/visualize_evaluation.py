"""
合同修订评估结果可视化脚本
"""

import os
import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
import warnings

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 设置图表样式
plt.style.use('seaborn-v0_8-darkgrid')

# 颜色配置
COLORS = {
    'semantic_similarity': '#3498db',
    'legal_completeness': '#e74c3c',
    'logical_consistency': '#2ecc71',
    'language_normativity': '#f39c12',
    'revision_rationality': '#9b59b6',
    'overall': '#1abc9c'
}

METRIC_NAMES = {
    'semantic_similarity': '语义相似度',
    'legal_completeness': '法律条款完整性',
    'logical_consistency': '逻辑一致性',
    'language_normativity': '语言规范性',
    'revision_rationality': '修订合理性',
    'overall': '综合分数'
}

METRIC_WEIGHTS = {
    'semantic_similarity': 0.25,
    'legal_completeness': 0.25,
    'logical_consistency': 0.15,
    'language_normativity': 0.15,
    'revision_rationality': 0.20
}


def load_evaluation_results(json_path: str) -> dict:
    """
    加载评估结果
    
    Args:
        json_path: JSON文件路径
        
    Returns:
        评估结果字典
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_overall_score_bar_chart(data: dict, output_path: str):
    """
    创建综合分数柱状图
    
    Args:
        data: 评估结果数据
        output_path: 输出路径
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    results = data['results']
    case_names = [r['case_name'] for r in results]
    overall_scores = [r['overall_score'] * 100 for r in results]
    avg_score = data['average_scores']['overall'] * 100
    
    # 创建柱状图
    bars = ax.bar(case_names, overall_scores, color=COLORS['overall'], alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # 添加平均线
    ax.axhline(y=avg_score, color='red', linestyle='--', linewidth=2, label=f'平均分: {avg_score:.2f}%')
    
    # 在柱子上添加数值标签
    for i, (bar, score) in enumerate(zip(bars, overall_scores)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{score:.2f}%',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # 设置标题和标签
    ax.set_xlabel('合同编号', fontsize=14, fontweight='bold')
    ax.set_ylabel('综合分数 (%)', fontsize=14, fontweight='bold')
    ax.set_title('五篇合同修订结果综合分数对比', fontsize=16, fontweight='bold', pad=20)
    
    # 设置y轴范围
    ax.set_ylim(0, 100)
    
    # 添加网格
    ax.grid(True, alpha=0.3, axis='y')
    
    # 添加图例
    ax.legend(loc='upper right', fontsize=12)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ 综合分数柱状图已保存: {output_path}")


def create_metrics_grouped_bar_chart(data: dict, output_path: str):
    """
    创建各项指标分组柱状图
    
    Args:
        data: 评估结果数据
        output_path: 输出路径
    """
    results = data['results']
    case_names = [r['case_name'] for r in results]
    
    metrics = ['semantic_similarity', 'legal_completeness', 'logical_consistency', 
               'language_normativity', 'revision_rationality']
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    x = np.arange(len(case_names))
    width = 0.15
    
    # 为每个指标创建柱状图
    for i, metric in enumerate(metrics):
        values = [r[metric] * 100 for r in results]
        offset = (i - len(metrics)/2 + 0.5) * width
        bars = ax.bar(x + offset, values, width, 
                     label=f"{METRIC_NAMES[metric]} (权重{METRIC_WEIGHTS[metric]*100:.0f}%)",
                     color=COLORS[metric], alpha=0.8, edgecolor='black', linewidth=1)
    
    # 设置标题和标签
    ax.set_xlabel('合同编号', fontsize=14, fontweight='bold')
    ax.set_ylabel('分数 (%)', fontsize=14, fontweight='bold')
    ax.set_title('五篇合同各项评估指标对比', fontsize=16, fontweight='bold', pad=20)
    
    # 设置x轴刻度
    ax.set_xticks(x)
    ax.set_xticklabels(case_names, fontsize=11)
    
    # 设置y轴范围
    ax.set_ylim(0, 100)
    
    # 添加网格
    ax.grid(True, alpha=0.3, axis='y')
    
    # 添加图例
    ax.legend(loc='upper right', fontsize=10, ncol=2)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ 各项指标分组柱状图已保存: {output_path}")


def create_radar_chart(data: dict, output_path: str):
    """
    创建雷达图
    
    Args:
        data: 评估结果数据
        output_path: 输出路径
    """
    results = data['results']
    
    metrics = ['semantic_similarity', 'legal_completeness', 'logical_consistency', 
               'language_normativity', 'revision_rationality']
    metric_labels = [METRIC_NAMES[m] for m in metrics]
    
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))
    
    # 计算角度
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]
    
    # 为每个合同创建雷达图
    colors = plt.cm.Set3(np.linspace(0, 1, len(results)))
    
    for idx, result in enumerate(results):
        values = [result[m] for m in metrics]
        values += values[:1]
        
        ax.plot(angles, values, 'o-', linewidth=2, 
                label=result['case_name'], color=colors[idx])
        ax.fill(angles, values, alpha=0.15, color=colors[idx])
    
    # 设置角度标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_labels, fontsize=11)
    
    # 设置y轴
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # 设置标题
    ax.set_title('五篇合同各项评估指标雷达图', fontsize=16, fontweight='bold', pad=20)
    
    # 添加图例
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ 雷达图已保存: {output_path}")


def create_heatmap(data: dict, output_path: str):
    """
    创建热力图
    
    Args:
        data: 评估结果数据
        output_path: 输出路径
    """
    results = data['results']
    
    case_names = [r['case_name'] for r in results]
    metrics = ['semantic_similarity', 'legal_completeness', 'logical_consistency', 
               'language_normativity', 'revision_rationality']
    metric_labels = [METRIC_NAMES[m] for m in metrics]
    
    # 创建数据矩阵
    matrix = np.array([[r[m] for m in metrics] for r in results]) * 100
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 创建热力图
    im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
    
    # 设置刻度
    ax.set_xticks(np.arange(len(metrics)))
    ax.set_yticks(np.arange(len(case_names)))
    ax.set_xticklabels(metric_labels, fontsize=11)
    ax.set_yticklabels(case_names, fontsize=11)
    
    # 旋转x轴标签
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # 在每个格子中添加数值
    for i in range(len(case_names)):
        for j in range(len(metrics)):
            text = ax.text(j, i, f'{matrix[i, j]:.1f}%',
                          ha="center", va="center", color="black", fontsize=10, fontweight='bold')
    
    # 设置标题
    ax.set_title('五篇合同评估指标热力图', fontsize=16, fontweight='bold', pad=20)
    
    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('分数 (%)', fontsize=12, fontweight='bold')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ 热力图已保存: {output_path}")


def create_summary_dashboard(data: dict, output_dir: str):
    """
    创建综合仪表板
    
    Args:
        data: 评估结果数据
        output_dir: 输出目录
    """
    fig = plt.figure(figsize=(20, 12))
    
    # 创建子图布局
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # 1. 综合分数柱状图
    ax1 = fig.add_subplot(gs[0, 0])
    results = data['results']
    case_names = [r['case_name'] for r in results]
    overall_scores = [r['overall_score'] * 100 for r in results]
    avg_score = data['average_scores']['overall'] * 100
    
    bars = ax1.bar(case_names, overall_scores, color=COLORS['overall'], 
                   alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.axhline(y=avg_score, color='red', linestyle='--', linewidth=2, 
                label=f'平均分: {avg_score:.2f}%')
    
    for bar, score in zip(bars, overall_scores):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{score:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax1.set_xlabel('合同编号', fontsize=12, fontweight='bold')
    ax1.set_ylabel('综合分数 (%)', fontsize=12, fontweight='bold')
    ax1.set_title('综合分数对比', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, 100)
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.legend(loc='upper right', fontsize=10)
    
    # 2. 平均分数柱状图
    ax2 = fig.add_subplot(gs[0, 1])
    avg_scores = data['average_scores']
    metrics = ['semantic_similarity', 'legal_completeness', 'logical_consistency', 
               'language_normativity', 'revision_rationality']
    metric_labels = [METRIC_NAMES[m] for m in metrics]
    avg_values = [avg_scores[m] * 100 for m in metrics]
    
    colors = [COLORS[m] for m in metrics]
    bars = ax2.bar(metric_labels, avg_values, color=colors, alpha=0.8, 
                   edgecolor='black', linewidth=1.5)
    
    for bar, value in zip(bars, avg_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{value:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax2.set_xlabel('评估指标', fontsize=12, fontweight='bold')
    ax2.set_ylabel('平均分数 (%)', fontsize=12, fontweight='bold')
    ax2.set_title('各项指标平均分数', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3, axis='y')
    plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
    
    # 3. 雷达图
    ax3 = fig.add_subplot(gs[1, 0], projection='polar')
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]
    
    colors_radar = plt.cm.Set3(np.linspace(0, 1, len(results)))
    for idx, result in enumerate(results):
        values = [result[m] for m in metrics]
        values += values[:1]
        ax3.plot(angles, values, 'o-', linewidth=2, 
                label=result['case_name'], color=colors_radar[idx])
        ax3.fill(angles, values, alpha=0.15, color=colors_radar[idx])
    
    ax3.set_xticks(angles[:-1])
    ax3.set_xticklabels(metric_labels, fontsize=10)
    ax3.set_ylim(0, 1)
    ax3.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax3.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_title('各项指标雷达图', fontsize=14, fontweight='bold')
    ax3.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
    
    # 4. 热力图
    ax4 = fig.add_subplot(gs[1, 1])
    matrix = np.array([[r[m] for m in metrics] for r in results]) * 100
    im = ax4.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
    
    ax4.set_xticks(np.arange(len(metrics)))
    ax4.set_yticks(np.arange(len(case_names)))
    ax4.set_xticklabels(metric_labels, fontsize=9)
    ax4.set_yticklabels(case_names, fontsize=9)
    plt.setp(ax4.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    for i in range(len(case_names)):
        for j in range(len(metrics)):
            ax4.text(j, i, f'{matrix[i, j]:.1f}%',
                     ha="center", va="center", color="black", fontsize=9, fontweight='bold')
    
    ax4.set_title('评估指标热力图', fontsize=14, fontweight='bold')
    cbar = plt.colorbar(im, ax=ax4)
    cbar.set_label('分数 (%)', fontsize=10, fontweight='bold')
    
    # 设置总标题
    fig.suptitle('合同修订评估结果综合仪表板', fontsize=18, fontweight='bold', y=0.98)
    
    # 保存图表
    output_path = os.path.join(output_dir, 'evaluation_dashboard.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ 综合仪表板已保存: {output_path}")


def main():
    """
    主函数
    """
    print("=" * 80)
    print("合同修订评估结果可视化")
    print("=" * 80)
    print()
    
    # 设置路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, 'evaluation_results')
    
    # 查找最新的JSON文件
    json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
    if not json_files:
        print("✗ 未找到评估结果JSON文件")
        return
    
    latest_json = sorted(json_files)[-1]
    json_path = os.path.join(results_dir, latest_json)
    
    print(f"正在加载评估结果: {latest_json}")
    
    # 加载数据
    data = load_evaluation_results(json_path)
    
    print(f"评估用例总数: {data['total_cases']}")
    print(f"平均综合分数: {data['average_scores']['overall'] * 100:.2f}%")
    print()
    
    # 创建输出目录
    output_dir = os.path.join(results_dir, 'charts')
    os.makedirs(output_dir, exist_ok=True)
    
    print("正在生成可视化图表...")
    print()
    
    # 生成各种图表
    create_overall_score_bar_chart(data, os.path.join(output_dir, 'overall_score_bar.png'))
    create_metrics_grouped_bar_chart(data, os.path.join(output_dir, 'metrics_grouped_bar.png'))
    create_radar_chart(data, os.path.join(output_dir, 'radar_chart.png'))
    create_heatmap(data, os.path.join(output_dir, 'heatmap.png'))
    create_summary_dashboard(data, output_dir)
    
    print()
    print("=" * 80)
    print("可视化图表生成完成！")
    print(f"所有图表已保存到: {output_dir}")
    print("=" * 80)


if __name__ == '__main__':
    main()
