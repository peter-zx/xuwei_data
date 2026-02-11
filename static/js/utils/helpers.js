/**
 * 工具函数
 */

/**
 * 显示Toast提示
 * @param {string} message - 提示消息
 * @param {string} type - 提示类型 (success, error, info, warning)
 */
export function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        info: 'fa-info-circle',
        warning: 'fa-exclamation-triangle'
    };

    toast.innerHTML = `
        <i class="fas ${icons[type]} toast-icon"></i>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    // 3秒后自动移除
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * 验证文件
 * @param {File} file - 文件对象
 * @returns {object} 验证结果 {valid: boolean, message: string}
 */
export function validateFile(file) {
    const { ALLOWED_EXTENSIONS, MAX_FILE_SIZE } = require('./constants');

    const extension = '.' + file.name.split('.').pop().toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
        return {
            valid: false,
            message: '请上传 .xlsx 或 .xls 格式的文件'
        };
    }

    if (file.size > MAX_FILE_SIZE) {
        return {
            valid: false,
            message: '文件大小不能超过 16MB'
        };
    }

    return { valid: true };
}

/**
 * 获取Excel列字母
 * @param {number} index - 列索引（0-based）
 * @returns {string} 列字母
 */
export function getColumnLetter(index) {
    let column = '';
    let temp = index;
    while (temp >= 0) {
        column = String.fromCharCode((temp % 26) + 65) + column;
        temp = Math.floor(temp / 26) - 1;
    }
    return column;
}
