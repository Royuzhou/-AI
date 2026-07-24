/* 合同修订逻辑 */

let revisionTaskId = null;
let pollTimer = null;

function onContractFileSelected(event) {
    if (!event.target.files.length) return;
    const file = event.target.files[0];
    document.getElementById('contract-filename').textContent = file.name;
    document.getElementById('contract-file-info').classList.remove('d-none');
    document.getElementById('revise-btn').disabled = false;
    // 存储文件引用用于上传
    window._contractFile = file;
}

function clearContractFile() {
    window._contractFile = null;
    document.getElementById('contract-file-info').classList.add('d-none');
    document.getElementById('revise-btn').disabled = true;
    document.getElementById('contract-file-input').value = '';
}

async function startRevision() {
    const file = window._contractFile;
    if (!file) { showToast('请先选择合同文件', 'warning'); return; }

    document.getElementById('revision-progress').classList.remove('d-none');
    document.getElementById('revision-result').classList.add('d-none');
    document.getElementById('revision-error').classList.add('d-none');
    document.getElementById('revise-btn').disabled = true;

    try {
        // Step 1: Upload
        const formData = new FormData();
        formData.append('file', file);
        const uploadResp = await fetch('/api/contract/upload', { method: 'POST', body: formData });
        const uploadData = await uploadResp.json();
        if (!uploadData.success) throw new Error(uploadData.error);

        // Step 2: Start revision
        const reviseResp = await fetch('/api/contract/revise', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({filepath: uploadData.path})
        });
        const reviseData = await reviseResp.json();
        if (!reviseData.success) throw new Error(reviseData.error);

        revisionTaskId = reviseData.task_id;
        pollTaskStatus();
    } catch (e) {
        document.getElementById('revision-progress').classList.add('d-none');
        document.getElementById('revision-error').classList.remove('d-none');
        document.getElementById('revision-error').textContent = '错误: ' + e.message;
        document.getElementById('revise-btn').disabled = false;
    }
}

async function pollTaskStatus() {
    if (!revisionTaskId) return;
    try {
        const resp = await fetch(`/api/contract/status/${revisionTaskId}`);
        const data = await resp.json();
        if (data.status === 'completed') {
            document.getElementById('revision-progress').classList.add('d-none');
            displayResult(data.result);
        } else if (data.status === 'failed') {
            document.getElementById('revision-progress').classList.add('d-none');
            const errDiv = document.getElementById('revision-error');
            errDiv.classList.remove('d-none');
            errDiv.innerHTML = `<strong>修订失败:</strong> ${escapeHtml(data.error||'')}`;
            document.getElementById('revise-btn').disabled = false;
        } else {
            pollTimer = setTimeout(pollTaskStatus, 3000);
        }
    } catch (e) {
        pollTimer = setTimeout(pollTaskStatus, 5000);
    }
}

function displayResult(resultText) {
    document.getElementById('revision-result').classList.remove('d-none');
    document.getElementById('revised-content').textContent = resultText || '(空)';
    document.getElementById('revise-btn').disabled = false;

    // 解析修改建议
    const suggestionsList = document.getElementById('suggestions-list');
    if (resultText && resultText.includes('修改建议')) {
        const parts = resultText.split('【修改建议清单】');
        if (parts.length > 1) {
            const sugText = parts[1];
            const items = sugText.split(/\d+\.\s+/).filter(s => s.trim());
            suggestionsList.innerHTML = items.map(s => {
                const posMatch = s.match(/修改位置[：:]\s*(.+)/);
                const origMatch = s.match(/原文[：:]\s*(.+)/);
                const revMatch = s.match(/修改为[：:]\s*(.+)/);
                const reasonMatch = s.match(/修改原因[：:]\s*(.+)/);
                const lawMatch = s.match(/法条依据[：:]\s*(.+)/);
                return `<div class="suggestion-card">
                    ${posMatch ? `<div><strong>📍 ${escapeHtml(posMatch[1])}</strong></div>` : ''}
                    ${origMatch ? `<div class="mt-1"><small class="text-muted">原文</small><div class="bg-light p-2 rounded">${escapeHtml(origMatch[1])}</div></div>` : ''}
                    ${revMatch ? `<div class="mt-1"><small class="text-muted">修改为</small><div class="bg-success bg-opacity-10 p-2 rounded">${escapeHtml(revMatch[1])}</div></div>` : ''}
                    ${reasonMatch ? `<div class="mt-1"><small class="text-muted">原因</small><div class="p-1">${escapeHtml(reasonMatch[1])}</div></div>` : ''}
                    ${lawMatch ? `<div class="mt-1"><span class="badge bg-info">📜 ${escapeHtml(lawMatch[1])}</span></div>` : ''}
                </div>`;
            }).join('');
        }
    }
}

function downloadResult() {
    if (revisionTaskId) {
        window.open(`/api/contract/download/${revisionTaskId}`, '_blank');
    }
}
