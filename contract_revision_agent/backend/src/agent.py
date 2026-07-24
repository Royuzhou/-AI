"""
合同修订智能体 — LangGraph + MCP + Reflection

协议:
  外部 LLM 调用: HTTP REST (ChatOpenAI → DeepSeek API)
  内部工具调用:  MCP/stdio (3 个 MCP Server)

架构:
  ┌──────────┐    ┌──────────┐    ┌──────────────┐
  │ LLM Node │───▶│ Tool Node│───▶│ Reflection   │
  │ 推理+修订 │◀───│ 执行工具  │    │ Node (裁判)   │
  └──────────┘    └──────────┘    └──┬───────┬───┘
                                     │       │
                                通过  │       │ 不通过
                                     ▼       ▼
                                  结束    返回意见→LLM
"""

import asyncio
import re
import os
from datetime import datetime
from typing import TypedDict, Annotated, Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.errors import GraphRecursionError
from src.tools.functions import AGENT_TOOLS

from config import (
    MAIN_LLM_CONFIG, JUDGE_LLM_CONFIG, REFLECTION_CONFIG,
    LEGAL_CATEGORIES,
)
from src.memory import SessionStore
from src.hooks import validate_think_answer, ThinkAnswerError, validate_revision_format
from src.utils.helpers import print_section, print_success, print_error, print_warning


# ══════════════════════════════════════════════════════════════════════════
# System Prompt (提示词工程)
# ══════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """# 角色

你是运行在 DeepSeek-R1 推理引擎上的合同法律审查专家。
法律知识覆盖: 《民法典》《仲裁法》《公司法》及相关司法解释。

# DeepSeek-R1 专有输出格式

**你的每一次响应必须使用以下标签结构:**

think
（内部推理: 合同分析、风险评估、法条适用性判断。DeepSeek-R1 专有。）
/think

answer
（对外输出: 结构概述、条款修订、法律意见。向用户展示。）
/answer

不遵守此格式的响应无效。

# 内嵌法律知识库

以下法律原则已嵌入你的知识体系，推理时自动参考:

1. **公平原则**（《民法典》第6条）
   内容: 民事主体从事民事活动，应当遵循公平原则，合理确定各方的权利和义务。
   应用: 违约金过高、单方免责条款、权利不对等——均可能违反公平原则。

2. **诚实信用原则**（《民法典》第7条）
   内容: 民事主体从事民事活动，应当遵循诚信原则，秉持诚实，恪守承诺。
   应用: 合同解释、履约标准、附随义务——均应遵循诚实信用。

3. **违约金调整**（《民法典》第585条）
   内容: 约定的违约金过分高于造成的损失的，当事人可以请求人民法院或者仲裁机构予以适当减少。
   应用: 违约金超过实际损失30%通常被认定为"过分高于"。以补偿性为主、惩罚性为辅。

4. **格式条款**（《民法典》第496-498条）
   内容: 提供格式条款的一方应当采取合理方式提示对方注意重要条款；不合理免除或减轻自身责任、加重对方责任的格式条款无效。
   应用: 标准合同中的免责条款、责任限制条款——必须审查是否为无效格式条款。

5. **合同无效情形**（《民法典》第153条）
   内容: 违反法律、行政法规的强制性规定的民事法律行为无效；违背公序良俗的民事法律行为无效。
   应用: 审查合同条款是否违反强制性法规。

6. **仲裁协议**（《仲裁法》第16-18条）
   内容: 仲裁协议应当以书面形式订立，明确请求仲裁的意思表示、仲裁事项和选定的仲裁委员会。
   应用: 审查争议解决条款中的仲裁约定是否明确有效。

7. **违约损害赔偿**（《民法典》第584条）
   内容: 损失赔偿额应当相当于因违约所造成的损失，包括合同履行后可以获得的利益；但不得超过违约方订立合同时预见到或者应当预见到的损失。
   应用: 审查赔偿范围是否合理，是否违反可预见性规则。

# 条款分类体系

{legal_categories}

# 六阶段推理框架

在 think 标签内完成推理，在 answer 标签内输出成果:

## STRUCTURE (结构分析)
**必须先调用 extract_document 获取合同全文，否则无法进行任何分析。**
拿到文本后:
think: 合同主体? 标的额? 结构? 哪些条款可能有法律风险?
answer: 概述合同结构 + 初步风险判断

## CLASSIFY (条款分类)
think: 逐条分析，按 [责任条款|监管条款|合规条款|争议解决|其他] 五类标记
answer: 列出条款分类结果，指出可能存在问题的条款及初步依据

## RETRIEVE (法条检索与批判)
调用 retrieve_legal_references 后:
think: 每条法条真的适用吗? (语义相似≠法律相关) 有没有盲区需要补充检索?
answer: 总结检索结果和适用性判断

## REVISE (逐条款修订)
think: 每个需要修改的条款——适用哪条法? 怎么改? 为什么?
answer: 逐条输出修订，每条必须严格按以下格式（五个标签，缺一不可）：

§CHANGE
§ORIGINAL
(从合同摘录的原文条款，标注位置如"第X条第Y款")
§LAW
(从 RAG 检索结果中复制的完整法律条文，含法条号和全文)
§SUGGESTION
修改建议: (具体怎么改)
修改理由: (为什么改)
法条依据: 《XX法》第X条
§REVISED
(该条款修改后的完整文本)
§END

## REFLECT (自我审查)
在 think 内逐条对照自审:
□ 每条是否包含全部 §CHANGE §ORIGINAL §LAW §SUGGESTION §REVISED §END 标签?
□ §LAW 中的法律条文是否从 RAG 检索结果中完整复制?
□ 条款间无逻辑冲突? □ 修订未过度损害商业目的?
如发现问题，回到 REVISE 阶段。

## OUTPUT (整理输出)
自审通过后，在 answer 中输出，然后调用 finalize_revision:
【修订后的完整合同】
(修订后的合同全文)

【修改建议清单】
(按 §CHANGE...§END 格式列出所有修改条目，每条 4 个字段: 合同原文/法律原文/修改建议/修改后原文)
# 效率规则
如果发现修订条目较多、推理超过 5 轮，不要在 RETRIEVE 和 REVISE 之间反复循环。立即进入 REFLECT 自审，然后直接 OUTPUT 已完成的修改条目。未完成的条款在修改建议清单中标注"待进一步审查"。质量比数量重要——宁可少改几条，每条都要有法条依据。

# 推理深度示例

合同原文: "若乙方逾期交付，每逾期一日，应向甲方支付合同总额 1% 的违约金。"

think
责任条款。违约金 1%/天 = 年化365%，远超司法实践。需要民法典第585条。
补充风险: 只约束乙方、无对等甲方责任 → 可能违反公平原则(民法典第6条)。
检索后判断法条适用性，如相关度不足则换关键词重搜。
/think

answer
初步判断: 违约金比例明显偏高(年化365%)，且缺少对等甲方责任条款。
适用法条: 《民法典》第585条——违约金过分高于损失的，当事人可请求适当减少。
修订方案: 降至0.05%/天(年化~18%)，增加上限"累计不超过合同总额10%"，补充甲方逾期付款违约责任。
/answer

上述推理链条是每一处修改的最低标准。不要偷懒。质量优于速度。"""


# ══════════════════════════════════════════════════════════════════════════
# 裁判审查 Prompt
# ══════════════════════════════════════════════════════════════════════════

JUDGE_PROMPT = """# 角色

你是独立的合同审查裁判。你的任务是批判性地审查另一名律师对合同的修订结果。
你不负责修改合同，只负责找出问题和遗漏。

# 审查维度

请逐项审查以下内容:

1. **法条准确性**: 每条修改建议引用的法律条文是否准确适用？法条内容是否与修改目的相关？
2. **覆盖完整性**: 合同中所有存在法律风险的条款是否都得到了修订？是否存在应该修改但未修改的条款？
3. **内部一致性**: 修订后的条款之间是否存在逻辑冲突？（例如违约金改了但相关付款条款未同步调整）
4. **商业合理性**: 修订是否过度损害了合同的商业目的？是否在保护法律合规的同时保持了合同的可行性？
5. **格式规范性**: 输出是否包含【修订后的完整合同】和【修改建议清单】？每条建议是否有法条引用？

# 输出格式

请以 JSON 格式输出审查结果:

{{
  "pass": true/false,
  "score": 4.2,
  "issues": [
    "具体问题描述1",
    "具体问题描述2"
  ],
  "suggestions": [
    "改进建议1",
    "改进建议2"
  ]
}}

pass 为 true 表示修订质量合格（score >= 3），无需重新修订。
pass 为 false 表示存在需要修正的问题，必须重新修订。

# 审查对象

原始合同:
{contract_text}

修订结果:
{revised_content}"""


# ══════════════════════════════════════════════════════════════════════════
# Agent State
# ══════════════════════════════════════════════════════════════════════════

class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    session_id: str
    contract_file: str
    output_path: str
    contract_text: str
    judge_retries: int
    finalize_called: bool


# ══════════════════════════════════════════════════════════════════════════
# ContractRevisionAgent
# ══════════════════════════════════════════════════════════════════════════

class ContractRevisionAgent:
    """合同修订智能体 — LangGraph + MCP + Reflection

    使用方式:
        agent = ContractRevisionAgent(CONFIG)
        await agent.initialize()
        result = await agent.process_contract("Contract1.docx")
    """

    def __init__(self, config: dict):
        self.config = config
        self._tools: list[BaseTool] = []
        self._main_llm: ChatOpenAI | None = None
        self._judge_llm: ChatOpenAI | None = None
        self._graph = None
        
        self._memory = SessionStore()

    async def initialize(self):
        """连接 MCP Server 并构建 LangGraph"""
        # ── 1. 加载工具 ──
        print_section("加载工具")
        self._tools = list(AGENT_TOOLS)
        tool_names = [t.name for t in self._tools]
        print_success(f"工具已加载: {tool_names}")

        # ── 2. 创建 LLM ──
        main_cfg = self.config["main_llm"]
        self._main_llm = ChatOpenAI(
            api_key=main_cfg["api_key"],
            base_url=main_cfg["base_url"],
            model=main_cfg["model"],
            temperature=main_cfg.get("temperature", 0),
            max_tokens=main_cfg.get("max_tokens", 8192),
        )
        judge_cfg = self.config["judge_llm"]
        self._judge_llm = ChatOpenAI(
            api_key=judge_cfg["api_key"],
            base_url=judge_cfg["base_url"],
            model=judge_cfg["model"],
            temperature=judge_cfg.get("temperature", 0.3),
            max_tokens=judge_cfg.get("max_tokens", 4096),
        )
        print_success(f"LLM 已就绪: 主模型={main_cfg['model']}, 裁判模型={judge_cfg['model']}")

        # ── 3. 构建 LangGraph ──
        self._graph = self._build_graph()
        print_success("LangGraph 构建完成")

    # ═════════════════════════════════════════════════════════════════
    # 图构建
    # ═════════════════════════════════════════════════════════════════

    def _build_graph(self):
        builder = StateGraph(AgentState)

        # 节点
        builder.add_node("llm", self._llm_node)
        builder.add_node("tools", ToolNode(self._tools))
        builder.add_node("reflection", self._reflection_node)

        # 入口
        builder.set_entry_point("llm")

        # LLM 后的条件路由
        builder.add_conditional_edges("llm", self._llm_router, {
            "tools": "tools",
            "end": END,
        })

        # 工具执行后的路由
        builder.add_conditional_edges("tools", self._tool_router, {
            "llm": "llm",
            "reflection": "reflection",
        })

        # Reflection 后的路由
        builder.add_conditional_edges("reflection", self._judge_router, {
            "pass": END,
            "fail": "llm",
        })

        return builder.compile()

    # ═════════════════════════════════════════════════════════════════
    # LLM Node
    # ═════════════════════════════════════════════════════════════════

    def _llm_node(self, state: AgentState) -> dict:
        """主 LLM 推理节点 — 含 think/answer 格式校验 Hook"""
        messages = state["messages"]

        # 确保 System Prompt 在第一条
        if not messages or not isinstance(messages[0], SystemMessage):
            categories_str = "\n".join(
                f"{k}: {v}" for k, v in LEGAL_CATEGORIES.items()
            )
            system_content = SYSTEM_PROMPT.format(legal_categories=categories_str)
            messages = [SystemMessage(content=system_content)] + list(messages)

        # ── LLM 调用 + think/answer 格式校验 (Hook) ──
        max_format_retries = 2
        for attempt in range(max_format_retries + 1):
            response = self._main_llm.invoke(messages)
            content = response.content or ""

            # 如果响应带有 tool_calls，跳过纯文本格式校验
            if hasattr(response, "tool_calls") and response.tool_calls:
                break

            # 仅对纯文本响应做 think/answer 校验
            # (tool_call 阶段 LLM 只需输出 JSON function call，不需要标签)
            if "{" in (content[:100] or "") and '"name"' in (content[:200] or ""):
                break  # 看起来是 function call JSON

            try:
                _, think_text, _ = validate_think_answer(content)
                break  # 校验通过
            except ThinkAnswerError as e:
                print_warning(f"think/answer 格式校验不通过 (尝试 {attempt+1}/{max_format_retries+1}): {e}")
                if attempt < max_format_retries:
                    messages.append(
                        HumanMessage(content=(
                            f"【格式修正要求】\n"
                            f"你的上一次响应格式不符合规范: {e}\n\n"
                            f"请严格使用以下格式重新输出:\n"
                            f"think\n(你的内部推理)\n/think\n\n"
                            f"answer\n(你的对外输出)\n/answer\n\n"
                            f"注意: think 块必须在 answer 块之前，两个标签对必须完整闭合。"
                        ))
                    )
                else:
                    print_error(f"think/answer 格式校验最终失败，按原始输出继续")
                    think_text = self._extract_think(content)

        # 打印日志
        if think_text:
            print(f"\n[think] {think_text[:300]}...")
        else:
            content_preview = content[:300]
            print(f"[answer] {content_preview}...")

        # 保存消息到记忆层
        self._memory.save_message(
            session_id=state.get("session_id", ""),
            step=state.get("judge_retries", 0) * 100 + len(messages),
            role="assistant",
            content=content,
            think_text=think_text,
        )

        return {"messages": [response]}

    # ═════════════════════════════════════════════════════════════════
    # Reflection Node
    # ═════════════════════════════════════════════════════════════════

    def _reflection_node(self, state: AgentState) -> dict:
        """裁判模型独立审查修订质量"""
        print_section("Reflection 裁判审查")

        messages = state["messages"]
        retries = state.get("judge_retries", 0)

        # 提取合同文本和修订内容
        contract_text = state.get("contract_text", "")
        revised_content = ""
        for msg in messages:
            if isinstance(msg, AIMessage) and msg.content:
                if "修订后的完整合同" in msg.content:
                    revised_content = msg.content
                    break

        if not revised_content:
            # 从最近的 AI 消息提取
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:
                    revised_content = msg.content
                    break

        # 调用裁判模型
        judge_input = JUDGE_PROMPT.format(
            contract_text=contract_text[:5000] if contract_text else "（未获取到合同文本）",
            revised_content=revised_content[:8000],
        )

        try:
            judge_response = self._judge_llm.invoke([
                SystemMessage(content="你是独立的合同审查裁判。请以 JSON 格式输出审查结果。"),
                HumanMessage(content=judge_input),
            ])
            verdict = self._parse_judge_response(judge_response.content or "")
        except Exception as e:
            print_error(f"裁判模型调用失败: {e}")
            verdict = {"pass": True, "score": 3, "issues": [], "suggestions": []}

        score = verdict.get("score", 0)
        passed = verdict.get("pass", False) or score >= REFLECTION_CONFIG["pass_threshold"]
        issues = verdict.get("issues", [])
        suggestions = verdict.get("suggestions", [])

        print(f"  评分: {score}/5  {'✅ 通过' if passed else '❌ 不通过'}")
        if issues:
            for issue in issues:
                print(f"  ⚠ {issue}")

        # 保存裁判结果到记忆层
        self._memory.save_message(
            session_id=state.get("session_id", ""),
            step=len(messages),
            role="judge",
            content=f"score={score} pass={passed} issues={issues} suggestions={suggestions}",
        )

        if passed:
            return {"judge_retries": retries + 1}

        # 不通过：将裁判意见反馈给 LLM
        max_retries = REFLECTION_CONFIG.get("max_retries", 2)
        if retries >= max_retries:
            print_warning(f"已达最大重试次数 ({max_retries})，强制通过")
            return {}

        feedback = "【裁判审查反馈】\n"
        feedback += f"评分: {score}/5\n\n"
        if issues:
            feedback += "发现的问题:\n" + "\n".join(f"  - {i}" for i in issues) + "\n\n"
        if suggestions:
            feedback += "改进建议:\n" + "\n".join(f"  - {s}" for s in suggestions) + "\n\n"
        feedback += "请根据以上反馈重新修订合同，然后再次调用 finalize_revision。"

        return {
            "judge_retries": retries + 1,
            "messages": [HumanMessage(content=feedback)],
        }

    # ═════════════════════════════════════════════════════════════════
    # 路由
    # ═════════════════════════════════════════════════════════════════

    def _llm_router(self, state: AgentState) -> Literal["tools", "end"]:
        """LLM 输出后的路由: 调用工具 or 结束"""
        messages = state["messages"]
        last_msg = messages[-1]

        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        return "end"

    def _tool_router(self, state: AgentState) -> Literal["llm", "reflection"]:
        """工具执行后的路由: 回到 LLM or 进入裁判审查"""
        messages = state["messages"]
        last_msg = messages[-1]

        # 检查刚刚执行的工具是否是 finalize_revision
        if isinstance(last_msg, ToolMessage):
            if last_msg.name == "finalize_revision":
                # 检查工具是否返回了格式校验失败
                if "格式校验失败" in (last_msg.content or ""):
                    return "llm"  # 格式不对，回 LLM 修正
                return "reflection"  # 格式通过，进裁判审查

        return "llm"

    def _judge_router(self, state: AgentState) -> Literal["pass", "fail"]:
        """裁判审查后的路由: 通过 or 重新修订"""
        messages = state["messages"]
        last_msg = messages[-1]

        # 检查是否是不通过的反馈消息
        if isinstance(last_msg, HumanMessage) and "裁判审查反馈" in (last_msg.content or ""):
            return "fail"

        return "pass"

    # ═════════════════════════════════════════════════════════════════
    # 公共入口
    # ═════════════════════════════════════════════════════════════════

    async def process_contract(
        self,
        input_file: str,
        output_dir: str = None,
        output_file: str = None,
    ) -> str | None:
        """处理单份合同

        Args:
            input_file: 合同文件路径
            output_dir: 输出目录
            output_file: 输出文件名

        Returns:
            修订后的合同文本，或 None（失败时）
        """
        if self._graph is None:
            print_error("Agent 未初始化，请先调用 initialize()")
            return None

        # ── 准备路径 ──
        if output_dir is None:
            output_dir = self.config.get("output_dir", "data/outputs")
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{base_name}(revised)_{timestamp}.txt"
        output_path = os.path.join(output_dir, output_file)
        os.makedirs(output_dir, exist_ok=True)

        # ── 创建会话 ──
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._memory.create_session(
            session_id=session_id,
            contract_file=input_file,
            output_file=output_path,
        )

        print_section("开始处理合同")
        print(f"  输入: {input_file}")
        print(f"  输出: {output_path}")
        print(f"  会话: {session_id}")

        if not os.path.exists(input_file):
            print_error(f"找不到文件: {input_file}")
            return None

        # ── 构建初始消息 ──
        categories_str = "\n".join(
            f"{k}: {v}" for k, v in LEGAL_CATEGORIES.items()
        )
        system_content = SYSTEM_PROMPT.format(legal_categories=categories_str)

        initial_messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=(
                f"请按六阶段框架修订以下合同:\n\n"
                f"合同文件: {input_file}\n"
                f"输出路径: {output_path}\n\n"
                f"第一步: 立即调用 extract_document 工具获取合同全文，参数 file_path='{input_file}'。"
                f"不要在没有合同文本的情况下进行任何分析。获取文本后再按六阶段框架推进。"
                f"所有法律推理必须在 think 标签内展示。"
                f"修订完成后自查，通过后调用 finalize_revision。"
                f"注意: 最多进行 3 轮检索-修订循环，之后必须在 think 中自审并直接进入 OUTPUT。未完成条款标注'待进一步审查'。"
            )),
        ]

        # 保存用户消息
        self._memory.save_message(
            session_id=session_id, step=0, role="user",
            content=f"请修订合同: {input_file}",
        )

        # ── 运行 LangGraph ──
        initial_state: AgentState = {
            "messages": initial_messages,
            "session_id": session_id,
            "contract_file": input_file,
            "output_path": output_path,
            "contract_text": "",
            "judge_retries": 0,
            "finalize_called": False,
        }

        try:
            result = self._graph.invoke(
                initial_state,
                config={"recursion_limit": 20},
            )
        except GraphRecursionError:
            print_warning("Agent 达到最大推理步数，提取已完成的部分结果...")
            result = {}
        except Exception as e:
            print_error(f"Agent 执行失败: {e}")
            import traceback
            traceback.print_exc()
            self._memory.update_session_status(session_id, "failed")
            return None

        # ── 提取结果 ──
        final_messages = result.get("messages", [])
        revised_content = ""

        # 从最后的消息中查找修订内容
        for msg in reversed(final_messages):
            if isinstance(msg, AIMessage) and msg.content:
                if "修订后的完整合同" in msg.content:
                    revised_content = msg.content
                    break
            if isinstance(msg, ToolMessage) and msg.name == "finalize_revision":
                if "已保存到" in (msg.content or ""):
                    # 成功保存，找对应内容
                    break

        if not revised_content:
            # 取最后一个 AI 消息作为结果
            for msg in reversed(final_messages):
                if isinstance(msg, AIMessage) and msg.content:
                    revised_content = msg.content
                    break

        # ── 更新会话状态 ──
        message_count = len([m for m in final_messages
                            if isinstance(m, (HumanMessage, AIMessage))])
        self._memory.update_session_status(session_id, "completed", message_count)

        # ── 提取法律记忆 ──
        self._extract_legal_memories(session_id, final_messages)

        print_section("处理完成")
        print(f"  结果已保存到: {output_path}")
        print(f"  会话 ID: {session_id}")

        return revised_content

    # ═════════════════════════════════════════════════════════════════
    # 辅助方法
    # ═════════════════════════════════════════════════════════════════

    def _extract_think(self, content: str) -> str:
        """提取 R1 think 标签内的推理文本"""
        if not content:
            return ""
        if "think" in content and "/think" in content:
            try:
                start = content.index("think") + len("think")
                end = content.index("/think")
                return content[start:end].strip()
            except ValueError:
                pass
        return ""

    def _parse_judge_response(self, content: str) -> dict:
        """解析裁判模型的 JSON 输出"""
        try:
            import json
            # 尝试直接解析
            # 先找 JSON 块
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            elif "{" in content and "}" in content:
                start = content.index("{")
                end = content.rindex("}") + 1
                json_str = content[start:end]
            else:
                json_str = content
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, ValueError):
            # 解析失败，尝试从文本中提取关键信息
            score = 3
            issues = []
            suggestions = []

            # 尝试从文本中提取评分
            score_match = re.search(r'score["\s:]+(\d+\.?\d*)', content, re.IGNORECASE)
            if score_match:
                score = float(score_match.group(1))

            return {
                "pass": score >= REFLECTION_CONFIG["pass_threshold"],
                "score": score,
                "issues": issues,
                "suggestions": suggestions,
            }

    def _extract_legal_memories(self, session_id: str, messages: list):
        """从对话中提取法律知识，存入长期记忆"""
        try:
            for msg in messages:
                if isinstance(msg, ToolMessage) and msg.name == "retrieve_legal_references":
                    content = msg.content or ""
                    # 提取法条引用
                    law_refs = re.findall(
                        r'法条:\s*(.+?)(?:\n|$)',
                        content,
                    )
                    clause_texts = re.findall(
                        r'条款:\s*(.+?)(?:\n|$)',
                        content,
                    )
                    for clause, law in zip(clause_texts, law_refs):
                        self._memory.save_legal_memory(
                            clause_text=clause.strip(),
                            law_ref=law.strip(),
                            source_session=session_id,
                        )
        except Exception:
            pass  # 记忆提取失败不影响主流程

    # ═════════════════════════════════════════════════════════════════
    # 历史查询
    # ═════════════════════════════════════════════════════════════════

    def list_sessions(self, limit: int = 20) -> list[dict]:
        """列出最近的会话"""
        return self._memory.list_sessions(limit)

    def get_session_detail(self, session_id: str) -> dict | None:
        """获取会话详情（含所有消息）"""
        session = self._memory.get_session(session_id)
        if not session:
            return None
        messages = self._memory.get_session_messages(session_id)
        session["messages"] = messages
        return session

    def get_legal_memory_stats(self) -> dict:
        """获取法律记忆统计"""
        return self._memory.get_legal_memory_stats()

    def get_common_patterns(self, limit: int = 5) -> list[dict]:
        """获取常见修订模式"""
        return self._memory.get_common_patterns(limit)
