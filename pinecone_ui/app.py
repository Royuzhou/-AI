"""
Pinecone 向量数据库独立管理界面
直接连接 Pinecone 云服务，提供完整的知识库管理功能
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "UltraRAG" / "ui" / "backend"))

from pinecone_manager import PineconeManager, load_pinecone_config, get_pinecone_client

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# 配置
UPLOAD_FOLDER = Path(__file__).parent / 'data' / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

def get_pinecone_manager():
    """获取 Pinecone 管理器实例"""
    config = load_pinecone_config()
    api_key = config.get('api_key', '')
    if not api_key:
        return None
    return PineconeManager(api_key=api_key)

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/connection/status')
def get_connection_status():
    """获取 Pinecone 连接状态"""
    try:
        config = load_pinecone_config()
        pc = get_pinecone_manager()
        
        if not pc:
            return jsonify({
                'status': 'disconnected',
                'message': 'API Key 未配置',
                'config': config
            })
        
        # 测试连接并获取索引列表
        indexes = pc.list_indexes()
        
        return jsonify({
            'status': 'connected',
            'message': f'已连接到 Pinecone',
            'indexes': indexes,
            'config': {
                'index_name': config.get('index_name', 'default'),
                'dimension': config.get('dimension', 768),
                'metric': config.get('metric', 'cosine'),
                'cloud': config.get('cloud', 'aws'),
                'region': config.get('region', 'us-east-1')
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'indexes': []
        }), 500

@app.route('/api/indexes', methods=['GET'])
def list_indexes():
    """获取所有索引"""
    try:
        pc = get_pinecone_manager()
        if not pc:
            return jsonify({'error': 'Pinecone 未配置'}), 400
        
        indexes = pc.list_indexes()
        stats = {}
        
        for index_name in indexes:
            try:
                stats[index_name] = pc.get_index_stats(index_name)
            except:
                stats[index_name] = {'error': '无法获取统计信息'}
        
        return jsonify({
            'indexes': indexes,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/indexes/create', methods=['POST'])
def create_index():
    """创建新索引"""
    try:
        data = request.json
        index_name = data.get('name')
        dimension = data.get('dimension', 768)
        metric = data.get('metric', 'cosine')
        
        if not index_name:
            return jsonify({'error': '索引名称不能为空'}), 400
        
        pc = get_pinecone_manager()
        if not pc:
            return jsonify({'error': 'Pinecone 未配置'}), 400
        
        pc.create_index(index_name, dimension=dimension, metric=metric)
        
        return jsonify({
            'success': True,
            'message': f'索引 {index_name} 创建成功'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/indexes/<index_name>/delete', methods=['DELETE'])
def delete_index(index_name):
    """删除索引"""
    try:
        pc = get_pinecone_manager()
        if not pc:
            return jsonify({'error': 'Pinecone 未配置'}), 400
        
        pc.delete_index(index_name)
        
        return jsonify({
            'success': True,
            'message': f'索引 {index_name} 删除成功'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/indexes/<index_name>/stats', methods=['GET'])
def get_index_stats(index_name):
    """获取索引统计信息"""
    try:
        pc = get_pinecone_manager()
        if not pc:
            return jsonify({'error': 'Pinecone 未配置'}), 400
        
        stats = pc.get_index_stats(index_name)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件上传'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        # 保存文件
        filename = file.filename
        filepath = UPLOAD_FOLDER / filename
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': str(filepath)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query_vectors():
    """向量查询"""
    try:
        data = request.json
        index_name = data.get('index_name')
        vector = data.get('vector')
        top_k = data.get('top_k', 10)
        include_metadata = data.get('include_metadata', True)
        
        if not index_name or not vector:
            return jsonify({'error': '缺少必要参数'}), 400
        
        pc = get_pinecone_manager()
        if not pc:
            return jsonify({'error': 'Pinecone 未配置'}), 400
        
        results = pc.query(index_name, vector, top_k=top_k, include_metadata=include_metadata)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upsert', methods=['POST'])
def upsert_vectors():
    """插入/更新向量"""
    try:
        data = request.json
        index_name = data.get('index_name')
        vectors = data.get('vectors')  # [(id, vector, metadata)]
        
        if not index_name or not vectors:
            return jsonify({'error': '缺少必要参数'}), 400
        
        pc = get_pinecone_manager()
        if not pc:
            return jsonify({'error': 'Pinecone 未配置'}), 400
        
        result = pc.upsert(index_name, vectors)
        
        return jsonify({
            'success': True,
            'upserted_count': result.get('upserted_count', len(vectors))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取当前配置"""
    config = load_pinecone_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        new_config = request.json
        config_path = project_root / "UltraRAG" / "data" / "knowledge_base" / "kb_config.json"
        
        # 读取现有配置
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 更新 Pinecone 配置
        if 'pinecone' not in config:
            config['pinecone'] = {}
        
        config['pinecone'].update(new_config)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 70)
    print("Pinecone 向量数据库管理界面")
    print("=" * 70)
    print(f"访问地址：http://localhost:5051")
    print(f"上传目录：{UPLOAD_FOLDER}")
    print("=" * 70)
    app.run(debug=True, port=5051, host='0.0.0.0')
