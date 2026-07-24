/* 知识库管理逻辑 */

let kbSelectedFile = null;

document.addEventListener('DOMContentLoaded', () => {
    refreshStatus();
    // 拖拽上传
    const area = document.getElementById('upload-area');
    area.addEventListener('dragover', e => { e.preventDefault(); area.classList.add('drag-over'); });
    area.addEventListener('dragleave', () => area.classList.remove('drag-over'));
    area.addEventListener('drop', e => {
        e.preventDefault();
        area.classList.remove('drag-over');
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
});

function onFileSelected(event) {
    if (event.target.files.length) handleFile(event.target.files[0]);
}

function handleFile(file) {
    kbSelectedFile = file;
    document.getElementById('upload-filename').textContent = file.name;
    document.getElementById('upload-file-info').classList.remove('d-none');
    document.getElementById('process-result').innerHTML = '';
}

function clearFile() {
    kbSelectedFile = null;
    document.getElementById('upload-file-info').classList.add('d-none');
    document.getElementById('kb-file-input').value = '';
}

async function processDocument() {
    if (!kbSelectedFile) { showToast('请先选择文件', 'warning'); return; }
    const progress = document.getElementById('process-progress');
    const btn = document.getElementById('process-btn');
    progress.classList.remove('d-none');
    btn.disabled = true;

    try {
        // Step 1: 上传
        const formData = new FormData();
        formData.append('file', kbSelectedFile);
        const uploadResp = await fetch('/api/kb/upload', { method: 'POST', body: formData });
        const uploadData = await uploadResp.json();
        if (!uploadData.success) throw new Error(uploadData.error);

        // Step 2: 处理
        const chunkSize = parseInt(document.getElementById('chunk-size').value) || 500;
        const processResp = await fetch('/api/kb/process', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({filepath: uploadData.path, chunk_size: chunkSize})
        });
        const processData = await processResp.json();

        const resultDiv = document.getElementById('process-result');
        if (processData.success) {
            resultDiv.innerHTML = `<div class="alert alert-success">
                <i class="bi bi-check-circle"></i> 处理完成! 文件: ${processData.filename}, 分块: ${processData.chunks}, 向量: ${processData.vectors}
            </div>`;
            refreshStatus();
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">处理失败: ${processData.error}</div>`;
        }
    } catch (e) {
        document.getElementById('process-result').innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
    } finally {
        progress.classList.add('d-none');
        btn.disabled = false;
    }
}

async function searchKB() {
    const query = document.getElementById('search-query').value.trim();
    if (!query) return;
    const resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '<p class="text-muted">搜索中...</p>';
    try {
        const resp = await fetch(`/api/kb/search?q=${encodeURIComponent(query)}&top_k=5`);
        const data = await resp.json();
        if (!data.results || !data.results.length) {
            resultsDiv.innerHTML = '<p class="text-muted">未找到匹配结果</p>';
            return;
        }
        resultsDiv.innerHTML = data.results.map((r, i) => `
            <div class="search-result-item">
                <div class="d-flex justify-content-between">
                    <strong>#${i+1}</strong>
                    <span class="search-result-score">相似度: ${(r.score||0).toFixed(4)}</span>
                </div>
                <p class="mt-1 mb-0 small">${escapeHtml(r.text||'')}</p>
                ${r.source ? `<small class="text-muted">来源: ${escapeHtml(r.source)}</small>` : ''}
            </div>
        `).join('');
    } catch (e) {
        resultsDiv.innerHTML = '<p class="text-danger">搜索失败</p>';
    }
}

async function refreshStatus() {
    try {
        const resp = await fetch('/api/kb/status');
        const data = await resp.json();
        document.getElementById('stat-vectors').textContent = data.total_vectors ?? '--';
        document.getElementById('stat-dimension').textContent = data.dimension ?? '--';
        document.getElementById('stat-connected').textContent = data.connected ? '已连接' : '未连接';
    } catch (e) {
        document.getElementById('stat-connected').textContent = '错误';
    }
}
