/* 公共函数 */

/** 显示 Toast 通知 */
function showToast(message, type = 'primary') {
    const container = document.getElementById('toast-container');
    const id = 'toast-' + Date.now();
    const bgMap = {primary:'#667eea', success:'#198754', danger:'#dc3545', warning:'#ffc107'};
    const iconMap = {primary:'info-circle', success:'check-circle', danger:'exclamation-triangle', warning:'exclamation-circle'};
    const html = `
        <div id="${id}" class="toast custom-toast align-items-center text-bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body"><i class="bi bi-${iconMap[type]||'info-circle'} me-2"></i>${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>`;
    container.insertAdjacentHTML('beforeend', html);
    const el = document.getElementById(id);
    const toast = new bootstrap.Toast(el, {delay: 3500});
    toast.show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
}

/** 显示/隐藏加载态 */
function toggleLoading(elem, show) {
    if (show) { elem.classList.add('d-none'); } else { elem.classList.remove('d-none'); }
}

/** 转义 HTML */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/** 格式化日期 */
function formatDate(isoStr) {
    if (!isoStr) return '';
    return isoStr.replace('T', ' ').substring(0, 19);
}
