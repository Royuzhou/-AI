"""
UI 启动前检查脚本
验证所有依赖和配置是否正确
"""

import sys
import os
from pathlib import Path


def check_dependencies():
    """检查依赖包"""
    print("=" * 80)
    print("检查依赖包...")
    print("=" * 80)
    
    required_packages = [
        'flask',
        'openai',
        'pinecone',
        'python-docx',
        'PyPDF2',
        'pymupdf',
        'paddleocr',
        'Pillow'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print("\n⚠️  以下包未安装:")
        for pkg in missing:
            print(f"   pip install {pkg}")
        return False
    
    print("\n✅ 所有依赖包已安装\n")
    return True


def check_config_files():
    """检查配置文件"""
    print("=" * 80)
    print("检查配置文件...")
    print("=" * 80)
    
    config_files = [
        'config.py',
        'data/knowledge_base/kb_config.json'
    ]
    
    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file}")
        else:
            print(f"❌ {config_file} (不存在)")
            all_exist = False
    
    print()
    return all_exist


def check_templates():
    """检查模板文件"""
    print("=" * 80)
    print("检查模板文件...")
    print("=" * 80)
    
    templates = [
        'ui/templates/index.html',
        'ui/templates/contract_revision.html',
        'ui/templates/pinecone_manager.html'
    ]
    
    all_exist = True
    for template in templates:
        if Path(template).exists():
            print(f"✅ {template}")
        else:
            print(f"❌ {template} (不存在)")
            all_exist = False
    
    print()
    return all_exist


def check_static_files():
    """检查静态文件"""
    print("=" * 80)
    print("检查静态文件...")
    print("=" * 80)
    
    static_files = [
        'ui/static/style.css',
        'ui/static/main.js'
    ]
    
    all_exist = True
    for static_file in static_files:
        if Path(static_file).exists():
            print(f"✅ {static_file}")
        else:
            print(f"❌ {static_file} (不存在)")
            all_exist = False
    
    print()
    return all_exist


def check_api_keys():
    """检查 API Key 配置"""
    print("=" * 80)
    print("检查 API 配置...")
    print("=" * 80)
    
    # 检查 DeepSeek API Key
    try:
        from config import CONFIG
        api_key = CONFIG.get('qwen_config', {}).get('api_key', '')
        
        if api_key and api_key.startswith('sk-'):
            masked_key = f"{api_key[:10]}...{api_key[-5:]}"
            print(f"✅ DeepSeek API Key: {masked_key}")
        else:
            print("⚠️  DeepSeek API Key 未配置或格式不正确")
    except Exception as e:
        print(f"❌ 无法读取配置：{e}")
    
    # 检查 Pinecone API Key
    try:
        kb_config_path = Path('data/knowledge_base/kb_config.json')
        if kb_config_path.exists():
            import json
            with open(kb_config_path, 'r', encoding='utf-8') as f:
                kb_config = json.load(f)
            
            pinecone_key = kb_config.get('pinecone_api_key', '')
            if pinecone_key:
                masked_key = f"{pinecone_key[:10]}...{pinecone_key[-5:]}"
                print(f"✅ Pinecone API Key: {masked_key}")
            else:
                print("⚠️  Pinecone API Key 未配置")
        else:
            print("⚠️  kb_config.json 不存在")
    except Exception as e:
        print(f"❌ 无法读取 Pinecone配置：{e}")
    
    print()


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("合同修订与法律知识库管理系统 - 启动前检查")
    print("=" * 80 + "\n")
    
    # 执行检查
    deps_ok = check_dependencies()
    configs_ok = check_config_files()
    templates_ok = check_templates()
    static_ok = check_static_files()
    
    check_api_keys()
    
    # 总结
    print("=" * 80)
    print("检查总结")
    print("=" * 80)
    
    all_ok = deps_ok and configs_ok and templates_ok and static_ok
    
    if all_ok:
        print("✅ 所有检查通过！系统已准备就绪。\n")
        print("下一步:")
        print("运行命令：python ui/app.py")
        print("访问地址：http://localhost:5000")
    else:
        print("❌ 部分检查未通过，请先修复问题。\n")
        print("修复建议:")
        if not deps_ok:
            print("1. 安装缺失的依赖包")
        if not configs_ok:
            print("2. 创建或修复配置文件")
        if not templates_ok:
            print("3. 创建或修复模板文件")
        if not static_ok:
            print("4. 创建或修复静态文件")
    
    print("=" * 80 + "\n")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
