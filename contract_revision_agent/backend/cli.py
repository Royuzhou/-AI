"""
合同修订智能体 — CLI 运维入口

命令:
  python cli.py revise <file>          合同修订
  python cli.py kb-update --url <url>   从 URL 更新 RAG 知识库
  python cli.py kb-update --name <名称>  搜索法律名称并更新
  python cli.py kb-status              查看知识库状态
  python cli.py serve                  启动 Web API 服务器
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse


def cmd_revise(args):
    """CLI 合同修订"""
    from config import CONFIG
    from src.agent import ContractRevisionAgent

    fp = args.file
    if not os.path.exists(fp):
        print(f"错误: 找不到文件 '{fp}'")
        return

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "outputs")
    os.makedirs(output_dir, exist_ok=True)

    async def _run():
        agent = ContractRevisionAgent(CONFIG)
        await agent.initialize()
        result = await agent.process_contract(fp, output_dir=output_dir)
        if result:
            print(f"\n修订完成! 结果已保存到 {output_dir}")
        else:
            print("\n修订失败")
        return result

    asyncio.run(_run())


def cmd_kb_update(args):
    """CLI RAG 知识库更新"""
    from src.rag import run_rag_pipeline

    url = args.url or ""
    name = args.name or ""

    if not url and not name:
        print("错误: 需要指定 --url 或 --name")
        return

    print(f"正在更新 RAG 知识库...")
    if url:
        print(f"  URL: {url}")
    if name:
        print(f"  名称: {name}")

    result = run_rag_pipeline(url=url, law_name=name)
    print(f"\n结果: {result['status']}")
    print(f"  分块数: {result['chunks']}")
    print(f"  入库向量: {result['upserted']}")
    if result.get("errors"):
        print(f"  错误: {result['errors']}")


def cmd_kb_status(args):
    """查看知识库状态"""
    from pinecone import Pinecone
    from config import PINECONE_CONFIG

    try:
        pc = Pinecone(api_key=PINECONE_CONFIG["api_key"])
        index = pc.Index(PINECONE_CONFIG["index_name"])
        stats = index.describe_index_stats()
        print(f"Pinecone 索引: {PINECONE_CONFIG['index_name']}")
        print(f"  向量总数: {stats.get('total_vector_count', 'N/A')}")
        print(f"  维度: {stats.get('dimension', 'N/A')}")
    except Exception as e:
        print(f"查询失败: {e}")


def cmd_serve(args):
    """启动 Web API 服务器"""
    from run import app
    print("=" * 60)
    print("  Contract Revision Agent API")
    print("  http://localhost:8080")
    print("=" * 60)
    app.run(debug=False, host="0.0.0.0", port=8080)


def cmd_tool(args):
    """单独调用某个工具函数"""
    if args.tool_name == "extract":
        from src.tools.functions import extract_document
        print(extract_document.invoke(args.file))
    elif args.tool_name == "search":
        from src.tools.functions import retrieve_legal_references
        print(retrieve_legal_references.invoke(args.query))
    elif args.tool_name == "kb-status":
        cmd_kb_status(args)
    else:
        print(f"未知工具: {args.tool_name}")
        print("可用: extract, search, kb-status")


def main():
    parser = argparse.ArgumentParser(description="合同修订智能体 CLI")
    sub = parser.add_subparsers(dest="command")

    # revise
    p = sub.add_parser("revise", help="修订合同")
    p.add_argument("file", help="合同文件路径")
    p.set_defaults(func=cmd_revise)

    # kb-update
    p = sub.add_parser("kb-update", help="更新 RAG 知识库")
    p.add_argument("--url", default="", help="法律法规 URL")
    p.add_argument("--name", default="", help="法律名称（搜索用）")
    p.set_defaults(func=cmd_kb_update)

    # kb-status
    p = sub.add_parser("kb-status", help="查看知识库状态")
    p.set_defaults(func=cmd_kb_status)

    # serve
    p = sub.add_parser("serve", help="启动 Web API 服务")
    p.set_defaults(func=cmd_serve)

    # tool — 单独调用工具
    p = sub.add_parser("tool", help="单独调用某个工具函数")
    p.add_argument("tool_name", help="工具名: extract / search / kb-status")
    p.add_argument("--file", default="", help="文件路径 (extract)")
    p.add_argument("--query", default="", help="检索关键词 (search)")
    p.set_defaults(func=cmd_tool)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    args.func(args)
    parser = argparse.ArgumentParser(description="合同修订智能体 CLI")
    sub = parser.add_subparsers(dest="command")

    # revise
    p = sub.add_parser("revise", help="修订合同")
    p.add_argument("file", help="合同文件路径")
    p.set_defaults(func=cmd_revise)

    # kb-update
    p = sub.add_parser("kb-update", help="更新 RAG 知识库")
    p.add_argument("--url", default="", help="法律法规 URL")
    p.add_argument("--name", default="", help="法律名称（搜索用）")
    p.set_defaults(func=cmd_kb_update)

    # kb-status
    p = sub.add_parser("kb-status", help="查看知识库状态")
    p.set_defaults(func=cmd_kb_status)

    # serve
    p = sub.add_parser("serve", help="启动 Web API 服务")
    p.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
