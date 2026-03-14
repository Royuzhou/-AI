"""
本地 FAISS 知识库构建脚本
无需 Docker 或云服务，完全离线运行
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ultrarag.client import main as ultrarag_main

if __name__ == "__main__":
    # 使用 kb_local_faiss 配置启动 UI
    config_file = "examples/kb_local_faiss.yaml"
    
    print("=" * 60)
    print("UltraRAG 本地知识库 (FAISS 后端)")
    print("=" * 60)
    print(f"配置文件：{config_file}")
    print("向量后端：FAISS (本地)")
    print("嵌入模型：MiniCPM-Embedding-Light")
    print("=" * 60)
    print()
    
    # 启动 UI
    sys.argv = ["ultrarag", "run", config_file]
    ultrarag_main()
