/* 历史记录逻辑 */

document.addEventListener('DOMContentLoaded', loadSessions);

async function loadSessions() {
    const tbody = document.getElementById('sessions-body');
    try {
        const resp = await fetch('/api/sessions');
        const sessions = await resp.json();
        if (!sessions || !sessions.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">暂无历史记录</td></tr>';
            return;
        }
        const statusIcon = {completed: '✅', running: '🔄', failed: '❌'};
        tbody.innerHTML = sessions.map(s => `
            <tr>
                <td>${formatDate(s.created_at)}</td>
                <td>${escapeHtml(s.contract_file||'?')}</td>
                <td>${s.session_id}</td>
                <td>${statusIcon[s.status]||'❓'} ${s.status||''}</td>
                <td><button class="btn btn-sm btn-outline-primary" onclick="viewDetail(${s.session_id})"><i class="bi bi-eye"></i> 详情</button></td>
            </tr>
        `).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">加载失败</td></tr>';
    }
}

async function viewDetail(sessionId) {
    const body = document.getElementById('detail-body');
    body.innerHTML = '<p class="text-center text-muted">加载中...</p>';
    const modal = new bootstrap.Modal(document.getElementById('detail-modal'));
    modal.show();

    try {
        const resp = await fetch(`/api/sessions/${sessionId}`);
        const data = await resp.json();
        if (data.error) { body.innerHTML = `<p class="text-danger">${data.error}</p>`; return; }

        const statusIcon = {completed: '✅', running: '🔄', failed: '❌'};
        let html = `
            <div class="mb-3">
                <strong>会话 ID:</strong> ${data.session_id}<br>
                <strong>时间:</strong> ${formatDate(data.created_at)}<br>
                <strong>合同:</strong> ${escapeHtml(data.contract_file||'')}<br>
                <strong>输出:</strong> ${escapeHtml(data.output_file||'')}<br>
                <strong>状态:</strong> ${statusIcon[data.status]||''} ${data.status}
            </div>
            <hr><h6>对话记录</h6>
        `;

        const messages = data.messages || [];
        const roleLabels = {user:'👤 用户', assistant:'🤖 Agent', tool:'🔧 工具', judge:'⚖️ 裁判'};
        const roleBg = {user:'', assistant:'bg-light', tool:'bg-warning bg-opacity-10', judge:'bg-info bg-opacity-10'};

        messages.forEach(m => {
            const bg = roleBg[m.role] || '';
            html += `<div class="mb-2 p-2 rounded ${bg}">`;
            html += `<small class="text-muted">[Step ${m.step}] ${roleLabels[m.role]||m.role}</small><br>`;
            if (m.think_text) {
                html += `<details><summary class="text-primary small">🧠 think</summary><pre class="small p-2 bg-white rounded" style="white-space:pre-wrap">${escapeHtml(m.think_text||'')}</pre></details>`;
            }
            if (m.content) {
                html += `<pre class="small mb-0 mt-1" style="white-space:pre-wrap">${escapeHtml((m.content||'').substring(0, 500))}</pre>`;
            }
            if (m.tool_name) html += `<small class="text-muted">🔧 ${escapeHtml(m.tool_name)}</small>`;
            html += '</div>';
        });

        body.innerHTML = html;
    } catch (e) {
        body.innerHTML = '<p class="text-danger">加载详情失败</p>';
    }
}
