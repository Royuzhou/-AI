"""
法律条款识别器 (保留以兼容 evaluation 模块)

注意: 主流程中条款分类由 Agent 在 think 标签内完成，此类仅用于评估脚本。
"""

from openai import OpenAI


class LegalClauseIdentifier:
    """法律条款识别器 — 保留以兼容 evaluation"""

    def __init__(self, api_key: str, base_url: str, model: str = "deepseek-chat"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.categories = {
            "责任条款": "涉及责任划分、赔偿、违约等",
            "监管条款": "涉及政府监管、审批、备案等",
            "合规条款": "涉及法律法规遵循、行业标准等",
            "争议解决": "涉及仲裁、诉讼、管辖等",
            "其他法律条款": "其他涉及法律的内容",
        }

    def identify(self, contract_text: str) -> str:
        """识别合同中的法律条款"""
        categories_str = "\n".join([
            f"{key}: {value}" for key, value in self.categories.items()
        ])

        prompt = f"""你是一个专业的法律文档分析助手。请分析以下合同文本，识别出涉及法律规定的条款，并按照以下分类进行标记：

分类标签：
{categories_str}

请按以下格式输出：
[分类标签] 原始条款内容

合同文本：
{contract_text}

请只输出标记后的法律条款，不要输出其他内容。"""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的法律文档分析助手。"},
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"法律条款识别失败: {e}")
            return ""

    def extract_clauses(self, identified_text: str) -> list[str]:
        """从识别结果中提取法律条款列表"""
        clauses = []
        for line in identified_text.split('\n'):
            if line.strip() and '[' in line and ']' in line:
                clause = line.split(']', 1)[1].strip()
                if clause:
                    clauses.append(clause)
        return clauses
