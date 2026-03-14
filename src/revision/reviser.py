"""
合同修订模块
使用大模型生成修订后的合同
"""

from openai import OpenAI


class ContractReviser:
    """合同修订器"""
    
    def __init__(self, api_key, base_url, model="deepseek-chat"):
        """
        初始化合同修订器
        
        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    def revise(self, original_contract, legal_references):
        """
        生成修订后的合同
        
        Args:
            original_contract: 原始合同文本
            legal_references: 法律参考信息列表
            
        Returns:
            修订后的合同文本
        """
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
                    {"role": "user", "content": prompt}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"合同修订失败: {e}")
            return ""
    
    def save_revised_contract(self, revised_text, output_path):
        """
        保存修订后的合同
        
        Args:
            revised_text: 修订后的合同文本
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(revised_text)