/* 配置页逻辑 — 用户 API 配置 */

document.addEventListener('DOMContentLoaded', loadAllConfig);

async function loadAllConfig() {
    try {
        const resp = await fetch('/api/config');
        const cfg = await resp.json();
        // DeepSeek
        if (cfg.deepseek) {
            document.getElementById('ds-api-key').value = cfg.deepseek.api_key || '';
            document.getElementById('ds-base-url').value = cfg.deepseek.base_url || 'https://api.deepseek.com/v1';
            document.getElementById('ds-model').value = cfg.deepseek.model || 'deepseek-chat';
        }
        // Pinecone
        if (cfg.pinecone) {
            document.getElementById('pc-api-key').value = cfg.pinecone.api_key || '';
            document.getElementById('pc-index').value = cfg.pinecone.index_name || 'software';
            document.getElementById('pc-topk').value = cfg.pinecone.top_k || 3;
        }
    } catch (e) {
        showToast('加载配置失败', 'danger');
    }
}

/* ── DeepSeek ── */

async function testDeepSeek() {
    const resultDiv = document.getElementById('ds-test-result');
    resultDiv.innerHTML = '<span class="text-muted">正在测试...</span>';
    try {
        const resp = await fetch('/api/config/test/deepseek', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                api_key: document.getElementById('ds-api-key').value,
                base_url: document.getElementById('ds-base-url').value,
                model: document.getElementById('ds-model').value,
            })
        });
        const data = await resp.json();
        if (data.connected) {
            resultDiv.innerHTML = `<span class="test-success"><i class="bi bi-check-circle"></i> 连接成功! 模型: ${data.model}</span>`;
        } else {
            resultDiv.innerHTML = `<span class="test-error"><i class="bi bi-x-circle"></i> 连接失败: ${data.error}</span>`;
        }
    } catch (e) {
        resultDiv.innerHTML = '<span class="test-error">请求异常</span>';
    }
}

async function saveDeepSeek() {
    await fetch('/api/config/deepseek', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            api_key: document.getElementById('ds-api-key').value,
            base_url: document.getElementById('ds-base-url').value,
            model: document.getElementById('ds-model').value,
        })
    });
    showToast('DeepSeek 配置已保存', 'success');
}

/* ── Pinecone ── */

async function testPinecone() {
    const resultDiv = document.getElementById('pc-test-result');
    resultDiv.innerHTML = '<span class="text-muted">正在测试...</span>';
    try {
        const resp = await fetch('/api/config/test/pinecone', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                api_key: document.getElementById('pc-api-key').value,
            })
        });
        const data = await resp.json();
        if (data.connected) {
            resultDiv.innerHTML = `<span class="test-success"><i class="bi bi-check-circle"></i> 连接成功! 索引: ${(data.indexes||[]).join(', ')}</span>`;
        } else {
            resultDiv.innerHTML = `<span class="test-error"><i class="bi bi-x-circle"></i> 连接失败: ${data.error}</span>`;
        }
    } catch (e) {
        resultDiv.innerHTML = '<span class="test-error">请求异常</span>';
    }
}

async function savePinecone() {
    await fetch('/api/config/pinecone', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            api_key: document.getElementById('pc-api-key').value,
            index_name: document.getElementById('pc-index').value,
            top_k: parseInt(document.getElementById('pc-topk').value) || 3,
        })
    });
    showToast('Pinecone 配置已保存', 'success');
}

