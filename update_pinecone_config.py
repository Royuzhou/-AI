"""
Pinecone API Key 更新工具
帮助你快速更新和验证 Pinecone配置
"""

import json
from pathlib import Path


def update_pinecone_config(api_key: str, index_name: str = "software"):
    """
    更新 Pinecone配置文件
    
    Args:
        api_key: Pinecone API Key
        index_name: 索引名称（默认：software）
    """
    print("=" * 80)
    print("更新 Pinecone配置")
    print("=" * 80)
    
    # 配置文件路径
    config_paths = [
        Path('data/knowledge_base/kb_config.json'),
        Path('UltraRAG/data/knowledge_base/kb_config.json')
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            print(f"\n📁 找到配置文件：{config_path}")
            
            try:
                # 读取现有配置
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新配置
                config['pinecone_api_key'] = api_key
                config['pinecone_index'] = index_name
                
                # 保存配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                print(f"✅ 配置已更新!")
                print(f"\n新配置:")
                print(f"  - API Key: {api_key[:10]}...{api_key[-5:]}")
                print(f"  - 索引名称：{index_name}")
                
                return True
                
            except Exception as e:
                print(f"❌ 更新失败：{e}")
                return False
    
    print("\n❌ 未找到配置文件")
    return False


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("Pinecone API Key 配置工具")
    print("=" * 80)
    print("\n请按照以下步骤获取 Pinecone API Key:")
    print("1. 访问 https://app.pinecone.io/")
    print("2. 登录你的账户")
    print("3. 点击左侧菜单的 'API Keys'")
    print("4. 复制你的 API Key (以 pcsk_ 开头)")
    print("=" * 80)
    
    # 输入新的 API Key
    new_api_key = input("\n请输入新的 Pinecone API Key: ").strip()
    
    if not new_api_key:
        print("\n⚠️  API Key 不能为空")
        return
    
    if not new_api_key.startswith('pcsk_'):
        print("\n⚠️  警告：API Key 应该以 'pcsk_' 开头")
        confirm = input("确定要继续吗？(y/n): ").strip().lower()
        if confirm != 'y':
            return
    
    # 输入索引名称
    index_name = input("\n请输入索引名称 (默认：software): ").strip()
    if not index_name:
        index_name = "software"
    
    # 更新配置
    if update_pinecone_config(new_api_key, index_name):
        print("\n" + "=" * 80)
        print("✅ 配置更新成功!")
        print("=" * 80)
        print("\n下一步:")
        print("1. 运行测试脚本：python test_pinecone_connection.py")
        print("2. 启动 UI 服务：python ui/app.py")
        print("3. 访问知识库管理页面：http://localhost:5000/pinecone")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ 配置更新失败")
        print("=" * 80)


if __name__ == "__main__":
    main()
