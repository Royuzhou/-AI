/**
 * 合同修订与法律知识库管理系统 - 主 JavaScript 文件
 * 提供通用的工具函数和辅助方法
 */

// ==================== 通用工具函数 ====================

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小字符串
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * 格式化日期时间
 * @param {Date|string} date - 日期对象或日期字符串
 * @returns {string} 格式化后的日期时间字符串
 */
function formatDateTime(date) {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

/**
 * 显示通知消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success, error, info, warning)
 * @param {number} duration - 显示时长 (毫秒)
 */
function showNotification(message, type = 'info', duration = 3000) {
    // 移除已存在的通知
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }
    
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // 添加样式
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '1rem 2rem',
        borderRadius: '8px',
        color: 'white',
        fontWeight: '500',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        zIndex: '9999',
        animation: 'slideIn 0.3s ease'
    });
    
    // 根据类型设置背景色
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        info: '#17a2b8',
        warning: '#ffc107'
    };
    notification.style.background = colors[type] || colors.info;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

/**
 * 复制到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>} 是否成功
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('已复制到剪贴板！', 'success');
        return true;
    } catch (err) {
        console.error('复制失败:', err);
        showNotification('复制失败，请手动复制', 'error');
        return false;
    }
}

/**
 * 下载文件
 * @param {string} content - 文件内容
 * @param {string} filename - 文件名
 * @param {string} mimeType - MIME 类型
 */
function downloadFile(content, filename, mimeType = 'text/plain') {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification(`文件 ${filename} 已开始下载`, 'success');
}

/**
 * 防抖函数
 * @param {Function} func - 要执行的函数
 * @param {number} wait - 等待时间 (毫秒)
 * @returns {Function} 防抖后的函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 * @param {Function} func - 要执行的函数
 * @param {number} limit - 时间限制 (毫秒)
 * @returns {Function} 节流后的函数
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ==================== API 请求封装 ====================

/**
 * 发送 API 请求
 * @param {string} url - 请求 URL
 * @param {Object} options - 请求选项
 * @returns {Promise<any>} 响应数据
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API 请求失败:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

/**
 * GET 请求
 * @param {string} url - 请求 URL
 * @returns {Promise<any>} 响应数据
 */
async function getRequest(url) {
    return apiRequest(url, { method: 'GET' });
}

/**
 * POST 请求
 * @param {string} url - 请求 URL
 * @param {Object} data - 请求数据
 * @returns {Promise<any>} 响应数据
 */
async function postRequest(url, data) {
    return apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

// ==================== 本地存储封装 ====================

/**
 * 保存到本地存储
 * @param {string} key - 存储键
 * @param {any} value - 存储值
 */
function saveToLocal(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error('保存到本地存储失败:', error);
    }
}

/**
 * 从本地存储读取
 * @param {string} key - 存储键
 * @returns {any|null} 存储值
 */
function loadFromLocal(key) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    } catch (error) {
        console.error('从本地存储读取失败:', error);
        return null;
    }
}

/**
 * 从本地存储删除
 * @param {string} key - 存储键
 */
function removeFromLocal(key) {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.error('从本地存储删除失败:', error);
    }
}

// ==================== 表单验证 ====================

/**
 * 验证邮箱格式
 * @param {string} email - 邮箱地址
 * @returns {boolean} 是否有效
 */
function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * 验证 URL 格式
 * @param {string} url - URL 地址
 * @returns {boolean} 是否有效
 */
function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch (_) {
        return false;
    }
}

/**
 * 验证文件路径是否存在 (需要后端支持)
 * @param {string} path - 文件路径
 * @returns {Promise<boolean>} 是否存在
 */
async function validateFilePath(path) {
    try {
        const response = await fetch('/api/validate-path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const data = await response.json();
        return data.exists || false;
    } catch (error) {
        console.error('验证文件路径失败:', error);
        return false;
    }
}

// ==================== 动画效果 ====================

/**
 * 平滑滚动到元素
 * @param {string|Element} target - 目标元素或选择器
 * @param {Object} options - 滚动选项
 */
function scrollToElement(target, options = {}) {
    const element = typeof target === 'string' 
        ? document.querySelector(target) 
        : target;
    
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
            ...options
        });
    }
}

/**
 * 淡入效果
 * @param {Element} element - 目标元素
 * @param {number} duration - 持续时间 (毫秒)
 */
function fadeIn(element, duration = 300) {
    element.style.opacity = 0;
    element.style.display = 'block';
    
    const start = performance.now();
    
    function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        
        element.style.opacity = progress;
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    requestAnimationFrame(animate);
}

/**
 * 淡出效果
 * @param {Element} element - 目标元素
 * @param {number} duration - 持续时间 (毫秒)
 */
function fadeOut(element, duration = 300) {
    const start = performance.now();
    
    function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        
        element.style.opacity = 1 - progress;
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            element.style.display = 'none';
        }
    }
    
    requestAnimationFrame(animate);
}

// ==================== 键盘快捷键 ====================

/**
 * 注册键盘快捷键
 * @param {string} key - 按键 (如 'Ctrl+S', 'Enter', 'Escape')
 * @param {Function} handler - 处理函数
 */
function registerShortcut(key, handler) {
    document.addEventListener('keydown', function(event) {
        const keyParts = key.split('+');
        const mainKey = keyParts.pop().toLowerCase();
        
        const modifiersMatch = keyParts.every(part => {
            switch(part.toLowerCase()) {
                case 'ctrl': return event.ctrlKey;
                case 'alt': return event.altKey;
                case 'shift': return event.shiftKey;
                case 'meta': return event.metaKey;
                default: return false;
            }
        });
        
        if (modifiersMatch && event.key.toLowerCase() === mainKey) {
            event.preventDefault();
            handler(event);
        }
    });
}

// ==================== 加载状态管理 ====================

/**
 * 显示加载指示器
 * @param {string} targetId - 目标元素 ID
 * @param {string} message - 加载消息
 */
function showLoading(targetId, message = '加载中...') {
    const target = document.getElementById(targetId);
    if (!target) return;
    
    const loader = document.createElement('div');
    loader.className = 'loading-indicator';
    loader.innerHTML = `
        <div class="spinner"></div>
        <p>${message}</p>
    `;
    
    // 添加加载指示器样式
    Object.assign(loader.style, {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
        gap: '1rem'
    });
    
    target.innerHTML = '';
    target.appendChild(loader);
}

/**
 * 隐藏加载指示器
 * @param {string} targetId - 目标元素 ID
 */
function hideLoading(targetId) {
    const target = document.getElementById(targetId);
    if (!target) return;
    
    const loader = target.querySelector('.loading-indicator');
    if (loader) {
        loader.remove();
    }
}

// ==================== 导出模块 ====================

// 如果需要在其他脚本中使用，可以导出这些函数
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatFileSize,
        formatDateTime,
        showNotification,
        copyToClipboard,
        downloadFile,
        debounce,
        throttle,
        apiRequest,
        getRequest,
        postRequest,
        saveToLocal,
        loadFromLocal,
        removeFromLocal,
        isValidEmail,
        isValidUrl,
        validateFilePath,
        scrollToElement,
        fadeIn,
        fadeOut,
        registerShortcut,
        showLoading,
        hideLoading
    };
}
