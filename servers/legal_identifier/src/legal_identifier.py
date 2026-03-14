"""
Legal Clause Identifier Server - 法律条款识别服务
使用 Qwen3-Max 模型识别合同中的法律条款
"""

from typing import Dict, List
from openai import OpenAI
from ultrarag.server import UltraRAG_MCP_Server

app = UltraRAG_MCP_Server("legal_identifier")


# 法律条款分类
LEGAL_CATEGORIES = {
    "责任条款": "涉及责任划分、赔偿、违约等",
    "监管条款": "涉及政府监管、审批、备案等",
    "合规条款": "涉及法律法规遵循、行业标准等",
    "争议解决": "涉及仲裁、诉讼、管辖等",
    "其他法律条款": "其他涉及法律的内容"
}


@app.tool(output="contract_text->identified_clauses")
def identify_clauses(
    contract_text: str,
    model: str = "deepseek-chat",
    api_key: str = None,
    base_url: str = "https://api.deepseek.com/v1"
) -> Dict:
    """
    识别合同中的法律条款
    
    Args:
        contract_text: 合同文本内容
        model: Qwen 模型名称 (默认 qwen3-max)
        api_key: API 密钥 (如不传则使用环境变量 DASHSCOPE_API_KEY)
        base_url: API 基础 URL
    
    Returns:
        包含识别结果和条款列表的字典
    """
    try:
        # 初始化客户端
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        # 构建分类标签字符串
        categories_str = "\n".join([
            f"{key}: {value}" for key, value in LEGAL_CATEGORIES.items()
        ])
        
        # 构建提示词
        prompt = f"""你是一个专业的法律文档分析助手。请分析以下合同文本，识别出涉及法律规定的条款，并按照以下分类进行标记：

分类标签：
{categories_str}

请按以下格式输出：
[分类标签] 原始条款内容

合同文本：
{contract_text}

请只输出标记后的法律条款，不要输出其他内容。"""
        
        # 调用 API
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的法律文档分析助手。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        identified_text = completion.choices[0].message.content
        
        # 提取条款列表
        clauses = []
        for line in identified_text.split('\n'):
            if line.strip() and '[' in line and ']' in line:
                clause = line.split(']', 1)[1].strip()
                if clause:
                    clauses.append(clause)
        
        app.logger.info(f"成功识别{len(clauses)}条法律条款")
        
        return {
            "identified_clauses": clauses,
            "identified_text": identified_text
        }
        
    except Exception as e:
        app.logger.error(f"法律条款识别失败：{e}")
        return {
            "error": str(e),
            "identified_clauses": [],
            "identified_text": ""
        }


if __name__ == "__main__":
    app.run(transport="stdio")
