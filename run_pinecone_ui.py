"""
Pinecone 向量数据库管理界面 - 快速启动脚本
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pinecone_ui.app import app

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Pinecone 向量数据库管理界面")
    print("=" * 70)
    print(f"📍 访问地址：http://localhost:5051")
    print(f"📁 上传目录：{project_root / 'pinecone_ui' / 'data' / 'uploads'}")
    print("=" * 70)
    print("\n功能列表:")
    print("  ✅ 连接状态监控")
    print("  ✅ 索引管理（创建/删除/统计）")
    print("  ✅ 文件上传")
    print("  ✅ 向量查询")
    print("  ✅ 配置管理")
    print("=" * 70)
    
    app.run(debug=True, port=5051, host='0.0.0.0')
