"""
Contract Revision Server - 合同修订服务
使用 Qwen3-Max 模型生成修订后的合同
"""

from typing import Dict, List
from openai import OpenAI
from ultrarag.server import UltraRAG_MCP_Server

app = UltraRAG_MCP_Server("contract_revision")


@app.tool(output="contract_text,legal_clauses,legal_references->revised_contract,suggestions")
def revise_contract(
    contract_text: str,
    legal_clauses: List[str],
    legal_references: List[Dict],
    model: str = "deepseek-chat",
    api_key: str = None,
    base_url: str = "https://api.deepseek.com/v1"
) -> Dict:
    """
    生成修订后的合同
    
    Args:
        contract_text: 原始合同文本
        legal_clauses: 识别出的法律条款列表
        legal_references: 相关法律参考条文列表
        model: Qwen 模型名称
        api_key: API 密钥
        base_url: API 基础 URL
    
    Returns:
        包含修订后合同和修改建议的字典
    """
    try:
        # 初始化客户端
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        # 格式化法律参考文本
        if legal_references:
            references_text = "\n".join([
                f"- {ref['reference']}\n  (相似度：{ref['score']:.2f})"
                for ref in legal_references
            ])
        else:
            references_text = "无（将基于通用的法律知识和最佳实践进行修订）"
        
        # 构建提示词
        prompt = f"""你是一个专业的合同修订助手。请根据以下信息，对合同进行修订：

【原始合同】
{contract_text}

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
        
        # 调用 API
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的合同修订助手，熟悉各类法律法规。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        revised_text = completion.choices[0].message.content
        
        # 解析修订结果
        revised_contract = ""
        suggestions = []
        
        if "【修订后的完整合同】" in revised_text:
            parts = revised_text.split("【修订后的完整合同】", 1)
            if len(parts) > 1:
                remainder = parts[1]
                if "【修改建议】" in remainder:
                    contract_part, suggestions_part = remainder.split("【修改建议】", 1)
                    revised_contract = contract_part.strip()
                    suggestions_text = suggestions_part.strip()
                    
                    # 解析修改建议
                    for line in suggestions_text.split('\n'):
                        if line.strip() and (line.startswith('1.') or line.startswith('2.') or 
                                            line.startswith('3.') or line.startswith('-')):
                            suggestions.append(line.strip())
                else:
                    revised_contract = remainder.strip()
        else:
            revised_contract = revised_text
        
        app.logger.info(f"合同修订完成，生成{len(suggestions)}条修改建议")
        
        return {
            "revised_contract": revised_contract,
            "suggestions": suggestions,
            "full_output": revised_text
        }
        
    except Exception as e:
        app.logger.error(f"合同修订失败：{e}")
        return {
            "error": str(e),
            "revised_contract": "",
            "suggestions": [],
            "full_output": ""
        }


if __name__ == "__main__":
    app.run(transport="stdio")
