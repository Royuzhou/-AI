"""
合同修订与法律知识库管理系统
整合合同修订和 Pinecone 向量数据库管理功能
简化版本 - 暂时跳过合同修订 Agent 的初始化
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
import json

# 添加 UltraRAG 到路径
ultrarag_path = Path(__file__).parent.parent / 'UltraRAG' / 'src'
sys.path.insert(0, str(ultrarag_path))

# 导入 Pinecone 管理器
try:
    from ultrarag.ui.backend.pinecone_manager import PineconeManager
except ImportError as e:
    print(f"⚠️  无法导入 PineconeManager: {e}")
    PineconeManager = None


app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# 初始化 Pinecone 管理器
pinecone_mgr = None
if PineconeManager:
    try:
        # 从配置文件加载 API Key
        kb_config_path = Path(__file__).parent.parent / 'data' / 'knowledge_base' / 'kb_config.json'
        if kb_config_path.exists():
            with open(kb_config_path, 'r', encoding='utf-8') as f:
                kb_config = json.load(f)
            api_key = kb_config.get('pinecone_api_key', '')
            
            if api_key:
                pinecone_mgr = PineconeManager(api_key=api_key)
                print("✅ Pinecone 管理器初始化成功")
            else:
                print("⚠️  Pinecone API Key 未在配置文件中找到")
        else:
            print(f"⚠️  配置文件不存在：{kb_config_path}")
    except Exception as e:
        print(f"⚠️  Pinecone 管理器初始化失败：{e}")
else:
    print("⚠️  PineconeManager 类不可用")

# 合同修订 Agent (暂时不初始化)
contract_agent = None
print("⚠️  合同修订 Agent 暂未初始化 (需要修复依赖)")


# ==================== 主页面路由 ====================

@app.route('/')
def index():
    """主页 - 功能选择"""
    return render_template('index.html')


# ==================== 合同修订模块路由 ====================

@app.route('/contract')
def contract_page():
    """合同修订页面"""
    return render_template('contract_revision.html')


@app.route('/api/contract/process', methods=['POST'])
def process_contract():
    """处理合同修订请求"""
    # TODO: 实现合同处理逻辑
    return jsonify({
        'success': False,
        'error': '合同修订功能正在升级中，请稍后使用'
    }), 503


@app.route('/api/contract/files', methods=['GET'])
def list_contract_files():
    """列出合同文件目录"""
    try:
        data_dir = Path(__file__).parent.parent / 'data' / 'contracts'
        
        if not data_dir.exists():
            return jsonify({
                'success': True,
                'files': [],
                'message': '合同目录不存在'
            })
        
        files = []
        for ext in ['*.pdf', '*.docx', '*.doc']:
            for file in data_dir.glob(ext):
                files.append({
                    'name': file.name,
                    'path': str(file.absolute()),
                    'size': file.stat().st_size
                })
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== Pinecone 管理模块路由 ====================

@app.route('/pinecone')
def pinecone_page():
    """Pinecone 管理页面"""
    return render_template('pinecone_manager.html')


@app.route('/api/pinecone/status', methods=['GET'])
def get_pinecone_status():
    """获取 Pinecone 连接状态"""
    try:
        if not pinecone_mgr:
            return jsonify({
                'success': False,
                'status': 'disconnected',
                'message': 'Pinecone 管理器未初始化'
            })
        
        status = pinecone_mgr.get_status()
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e)
        })


@app.route('/api/pinecone/config', methods=['GET'])
def get_pinecone_config():
    """获取 Pinecone配置"""
    try:
        config = pinecone_mgr.load_kb_config() if pinecone_mgr else {}
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/pinecone/config', methods=['POST'])
def update_pinecone_config():
    """更新 Pinecone配置"""
    try:
        data = request.json
        
        if not pinecone_mgr:
            return jsonify({
                'success': False,
                'error': 'Pinecone 管理器未初始化'
            }), 500
        
        # 更新配置
        pinecone_mgr.save_kb_config(data)
        
        # 重新初始化以应用新配置
        pinecone_mgr.initialize()
        
        return jsonify({
            'success': True,
            'message': '配置已更新'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/pinecone/upload', methods=['POST'])
def upload_document():
    """上传并处理文档"""
    try:
        if not pinecone_mgr:
            return jsonify({
                'success': False,
                'error': 'Pinecone 管理器未初始化'
            }), 500
        
        data = request.json
        file_path = data.get('file_path', '')
        chunk_backend = data.get('chunk_backend', 'default')
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': '请提供文件路径'
            }), 400
        
        # 处理文档
        result = pinecone_mgr.process_document(file_path, chunk_backend)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/pinecone/search', methods=['POST'])
def search_vectors():
    """向量搜索"""
    try:
        if not pinecone_mgr:
            return jsonify({
                'success': False,
                'error': 'Pinecone 管理器未初始化'
            }), 500
        
        data = request.json
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({
                'success': False,
                'error': '请提供查询文本'
            }), 400
        
        # 执行搜索
        results = pinecone_mgr.search(query, top_k)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/pinecone/stats', methods=['GET'])
def get_pinecone_stats():
    """获取统计信息"""
    try:
        if not pinecone_mgr:
            return jsonify({
                'success': False,
                'error': 'Pinecone 管理器未初始化'
            }), 500
        
        stats = pinecone_mgr.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# ==================== 静态文件路由 ====================

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory(app.static_folder, filename)


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({
        'success': False,
        'error': '页面未找到'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500


# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'status': 'running',
        'services': {
            'contract_revision': False,  # 暂未启用
            'pinecone_manager': pinecone_mgr is not None
        }
    })


if __name__ == '__main__':
    print("=" * 80)
    print("合同修订与法律知识库管理系统")
    print("=" * 80)
    print(f"合同修订服务：❌ 暂未启用 (依赖问题)")
    print(f"Pinecone 服务：{'✅ 就绪' if pinecone_mgr else '❌ 未就绪'}")
    print("=" * 80)
    print("访问地址：http://localhost:5000")
    print("=" * 80 + "\n")
    print("注意:")
    print("- Pinecone 管理功能已完全可用")
    print("- 合同修订功能需要修复 transformers 依赖后启用")
    print("=" * 80 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
