"""
合同修订模块 — 文件持久化 + 评估兼容

修订逻辑由 Agent LLM 在 think/answer 标签内完成。
ContractReviser 类保留以兼容评估模块 (src/evaluation2/)。
"""

import os
from openai import OpenAI


class ContractReviser:
    """合同修订器 (保留以兼容 evaluation 模块)

    注意: 主流程中修订由 Agent LLM 直接完成，此类仅用于评估脚本。
    """

    def __init__(self, api_key: str, base_url: str, model: str = "deepseek-chat"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def revise(self, original_contract: str, legal_references: list) -> str:
        """生成修订后的合同 (兼容旧接口)"""
        if legal_references:
            references_text = "\n".join([
                f"- {ref['reference']}\n  (相似度: {ref['score']:.2f})"
                for ref in legal_references
            ])
        else:
            references_text = "无（将基于通用的法律知识和最佳实践进行修订）"

        prompt = f"""你是一个专业的合同修订助手。请根据以下信息，对合同进行修订：

【原始合同】
{original_contract}

【相关法律条文参考】
{references_text}

【修订要求】
1. 仔细分析合同中与法律条文相关的内容
2. 根据法律条文的要求，对合同进行必要的修订
3. 保持合同的基本结构和商业意图
4. 确保修订后的合同符合相关法律法规
5. 标注出具体的修改内容和修改原因

【输出格式】
请按以下格式输出：

【修订后的完整合同】
（完整的修订后合同文本）

【修改建议】
1. 修改位置：...
   原文：...
   修改为：...
   修改原因：...

2. 修改位置：...
   原文：...
   修改为：...
   修改原因：...

（继续列出所有修改建议）"""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的合同修订助手，熟悉各类法律法规。"},
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"合同修订失败: {e}")
            return ""

    def save_revised_contract(self, revised_text: str, output_path: str):
        """保存修订后的合同到文件"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(revised_text)


def save_revised_contract(revised_text: str, output_path: str):
    """保存修订后的合同到文件（独立函数，供 MCP Tool 调用）"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(revised_text)
