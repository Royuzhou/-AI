"""
UltraRAG 复杂 RAG 迭代流程快速启动脚本
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ultrarag.client import main as ultrarag_main

def print_banner():
    """打印欢迎横幅"""
    print("=" * 70)
    print(" " * 20 + "UltraRAG 复杂 RAG 迭代系统")
    print("=" * 70)
    print()
    print("📚 支持的功能:")
    print("   ✅ 多轮迭代检索")
    print("   ✅ 智能查询重写")
    print("   ✅ Cross-Encoder 重排序")
    print("   ✅ 多维度质量评估")
    print("   ✅ 自动收敛判断")
    print()
    print("=" * 70)

def print_config_options():
    """打印配置选项"""
    print("\n【可用配置选项】")
    print()
    print("1. 完整配置 (推荐生产环境)")
    print("   命令：ultrarag run examples/complex_rag_iterative.yaml")
    print("   特点：3 轮迭代 + 重排序 + 评估，耗时 5-10 分钟")
    print()
    print("2. 简化配置 (推荐开发测试)")
    print("   命令：ultrarag run examples/simple_rag_iterative.yaml")
    print("   特点：2 轮迭代 + 基础检索，耗时 2-3 分钟")
    print()
    print("=" * 70)

def check_prerequisites():
    """检查前置条件"""
    print("\n【检查前置条件】")
    
    # 检查 1: kb_config.json
    config_path = "data/knowledge_base/kb_config.json"
    if os.path.exists(config_path):
        print(f"✅ 知识库配置文件存在：{config_path}")
        
        # 读取并检查 URI
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        uri = config.get('milvus', {}).get('uri', '')
        token = config.get('milvus', {}).get('token', '')
        
        if 'pinecone.io' in uri:
            print(f"✅ Pinecone 云服务已配置")
            if token and token != "YOUR_PINECONE_API_KEY":
                print(f"✅ API Key 已设置")
            else:
                print(f"⚠️  API Key 未设置或为默认值，请手动修改 kb_config.json")
        else:
            print(f"ℹ️  使用 Milvus 服务：{uri}")
    else:
        print(f"❌ 知识库配置文件不存在：{config_path}")
        return False
    
    # 检查 2: YAML 配置文件
    yaml_files = [
        "examples/complex_rag_iterative.yaml",
        "examples/simple_rag_iterative.yaml"
    ]
    
    for yaml_file in yaml_files:
        if os.path.exists(yaml_file):
            print(f"✅ 配置文件存在：{yaml_file}")
        else:
            print(f"❌ 配置文件不存在：{yaml_file}")
            return False
    
    return True

def main():
    """主函数"""
    print_banner()
    
    # 检查前置条件
    if not check_prerequisites():
        print("\n❌ 前置条件检查失败，请修复后重试")
        return
    
    print_config_options()
    
    # 获取用户选择
    print("\n请选择运行模式 (输入数字):")
    print("1 - 完整配置 (complex_rag_iterative.yaml)")
    print("2 - 简化配置 (simple_rag_iterative.yaml)")
    print("3 - 退出")
    
    choice = input("\n您的选择：").strip()
    
    if choice == "1":
        config_file = "examples/complex_rag_iterative.yaml"
    elif choice == "2":
        config_file = "examples/simple_rag_iterative.yaml"
    elif choice == "3":
        print("\n👋 再见!")
        return
    else:
        print("\n❌ 无效选择，请输入 1、2 或 3")
        return
    
    # 运行 UltraRAG
    print(f"\n🚀 正在启动 UltraRAG...")
    print(f"   配置文件：{config_file}")
    print(f"   输出目录：output/")
    print()
    
    try:
        sys.argv = ["ultrarag", "run", config_file]
        ultrarag_main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 运行出错：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
