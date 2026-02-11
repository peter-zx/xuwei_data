// ===== 应用状态管理 =====
const AppState = {
    currentStep: 1,
    filepath: '',
    sheetInfo: {},
    mappingsConfig: {},
    sheetResults: {}
};

// ===== 工具函数 =====

/**
 * 显示Toast提示
 * @param {string} message - 提示消息
 * @param {string} type - 提示类型 (success, error, info, warning)
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
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
 * 切换到指定步骤
 * @param {number} step - 步骤编号
 */
function goToStep(step) {
    // 更新步骤指示器
    document.querySelectorAll('.step-item').forEach((item, index) => {
        const stepNum = index + 1;
        item.classList.remove('active', 'completed');
        if (stepNum < step) {
            item.classList.add('completed');
        } else if (stepNum === step) {
            item.classList.add('active');
        }
    });

    // 切换步骤内容
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`step-${step}`).classList.add('active');

    AppState.currentStep = step;
}

/**
 * 重置应用状态
 */
function resetApp() {
    AppState.currentStep = 1;
    AppState.filepath = '';
    AppState.sheetInfo = {};
    AppState.mappingsConfig = {};
    AppState.sheetResults = {};

    // 重置文件输入
    document.getElementById('fileInput').value = '';

    // 隐藏文件预览
    document.getElementById('filePreview').style.display = 'none';

    // 清空映射容器
    document.getElementById('mappingContainer').innerHTML = '';

    // 清空结果容器
    document.getElementById('resultsContainer').innerHTML = '';

    // 返回第一步
    goToStep(1);
}

// ===== 文件上传功能 =====

// 初始化拖拽上传
function initDragAndDrop() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    if (!uploadZone || !fileInput) return;

    // 拖拽事件
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    // 点击上传
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });

    // 文件选择事件
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

/**
 * 处理文件上传
 * @param {File} file - 上传的文件
 */
async function handleFileUpload(file) {
    // 验证文件类型
    const validExtensions = ['.xlsx', '.xls'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(fileExtension)) {
        showToast('请上传 .xlsx 或 .xls 格式的文件', 'error');
        return;
    }

    // 验证文件大小（16MB）
    if (file.size > 16 * 1024 * 1024) {
        showToast('文件大小不能超过 16MB', 'error');
        return;
    }

    try {
        // 显示文件预览
        showFilePreview(file);

        // 上传文件
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            AppState.filepath = data.filepath;
            AppState.sheetInfo = data.sheet_info;

            showToast('文件上传成功', 'success');

            // 显示映射设置
            showMappingSettings();

            // 跳转到第二步
            goToStep(2);
        } else {
            showToast(data.error || '上传失败', 'error');
            hideFilePreview();
        }
    } catch (error) {
        console.error('上传错误:', error);
        showToast('上传失败，请重试', 'error');
        hideFilePreview();
    }
}

/**
 * 显示文件预览
 * @param {File} file - 文件对象
 */
function showFilePreview(file) {
    const preview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const fileSheets = document.getElementById('fileSheets');

    fileName.textContent = file.name;
    fileSheets.textContent = `文件大小: ${(file.size / 1024).toFixed(2)} KB`;

    preview.style.display = 'block';
}

/**
 * 隐藏文件预览
 */
function hideFilePreview() {
    document.getElementById('filePreview').style.display = 'none';
}

/**
 * 重置上传
 */
function resetUpload() {
    document.getElementById('fileInput').value = '';
    hideFilePreview();
}

// ===== 映射设置功能 =====

/**
 * 显示映射设置
 */
function showMappingSettings() {
    const container = document.getElementById('mappingContainer');
    container.innerHTML = '';

    const sheetNames = Object.keys(AppState.sheetInfo);

    if (sheetNames.length === 0) {
        container.innerHTML = '<p class="text-center">没有找到Sheet</p>';
        return;
    }

    sheetNames.forEach(sheetName => {
        const sheetData = AppState.sheetInfo[sheetName];
        const sheetCard = createSheetMappingCard(sheetName, sheetData);
        container.appendChild(sheetCard);
    });
}

/**
 * 创建Sheet映射卡片
 * @param {string} sheetName - Sheet名称
 * @param {object} sheetData - Sheet数据
 * @returns {HTMLElement}
 */
function createSheetMappingCard(sheetName, sheetData) {
    const card = document.createElement('div');
    card.className = 'sheet-mapping-card';

    // 判断是否为佳哥sheet
    const isJiageSheet = sheetName.includes('佳哥') && sheetName.includes('26');

    // 预定义映射（佳哥sheet）
    const jiageMappings = {
        '姓名': 'A2',
        '电话': 'B2',
        '身份证': 'D2',
        '残疾证': 'J2',
        '身份证到期时间': 'I2',
        '残疾证到期时间': 'M2',
        '残疾证等级': 'L2',
        '残疾证类型': 'K2'
    };

    // 自动映射
    const autoMappings = getAutoMappings(sheetData.original_headers);

    const headerHtml = `
        <div class="sheet-card-header">
            <h3>${sheetName}</h3>
            ${isJiageSheet ? '<span class="badge">佳哥26年数据信息</span>' : ''}
        </div>
    `;

    const bodyHtml = `
        <div class="sheet-card-body">
            <div class="row-setting">
                <label>表头所在行:</label>
                <input type="number" min="1" max="10" value="1" id="header-row-${sheetName}">
                <span style="color: var(--text-muted); font-size: 0.875rem;">默认第1行</span>
            </div>

            <div class="headers-info">
                <strong>原始表头:</strong>
                <span>${sheetData.original_headers.join(', ') || '无'}</span>
            </div>

            <div class="mapping-grid">
                ${sheetData.standard_headers.map((header, index) => {
                    const autoValue = autoMappings[header] || '';
                    const jiageValue = isJiageSheet ? (jiageMappings[header] || '') : '';
                    const defaultValue = jiageValue || autoValue;

                    return `
                        <div class="mapping-item">
                            <label>${header}</label>
                            <div class="mapping-input-group">
                                <input type="text"
                                       id="mapping-${sheetName}-${index}"
                                       placeholder="如: A2 或 姓名"
                                       value="${defaultValue}">
                                <span class="mapping-hint">${defaultValue ? `自动: ${defaultValue}` : '未匹配'}</span>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;

    card.innerHTML = headerHtml + bodyHtml;
    return card;
}

/**
 * 获取自动映射
 * @param {Array} originalHeaders - 原始表头列表
 * @returns {object} 映射对象
 */
function getAutoMappings(originalHeaders) {
    const mappings = {};
    const standardHeaders = [
        '姓名', '电话', '身份证', '残疾证',
        '身份证到期时间', '残疾证到期时间',
        '残疾证等级', '残疾证类型'
    ];

    if (!originalHeaders || originalHeaders.length === 0) {
        standardHeaders.forEach(header => {
            mappings[header] = '';
        });
        return mappings;
    }

    standardHeaders.forEach(header => {
        let found = false;

        // 简单的自动匹配
        for (let i = 0; i < originalHeaders.length; i++) {
            const originalHeader = String(originalHeaders[i] || '').toLowerCase();
            if (originalHeader && originalHeader.includes(header.toLowerCase())) {
                // 转换为Excel列字母
                const columnLetter = String.fromCharCode(65 + i);
                mappings[header] = columnLetter;
                found = true;
                break;
            }
        }

        if (!found) {
            mappings[header] = '';
        }
    });

    return mappings;
}

// ===== 数据分析功能 =====

/**
 * 分析数据
 */
async function analyzeData() {
    // 收集映射配置
    collectMappings();

    // 跳转到分析步骤
    goToStep(3);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filepath: AppState.filepath,
                mappings_config: AppState.mappingsConfig
            })
        });

        const data = await response.json();

        if (data.success) {
            AppState.sheetResults = data.sheet_results;
            showToast('数据分析完成', 'success');

            // 显示结果
            showResults();

            // 跳转到结果步骤
            goToStep(4);
        } else {
            showToast(data.error || '分析失败', 'error');
            goToStep(2);
        }
    } catch (error) {
        console.error('分析错误:', error);
        showToast('分析失败，请重试', 'error');
        goToStep(2);
    }
}

/**
 * 收集映射配置
 */
function collectMappings() {
    AppState.mappingsConfig = {};

    const sheetNames = Object.keys(AppState.sheetInfo);

    sheetNames.forEach(sheetName => {
        const sheetData = AppState.sheetInfo[sheetName];

        // 获取表头行号
        const headerRowInput = document.getElementById(`header-row-${sheetName}`);
        const headerRow = headerRowInput ? parseInt(headerRowInput.value) || 1 : 1;

        // 获取自定义映射
        const customMappings = {};
        sheetData.standard_headers.forEach((header, index) => {
            const mappingInput = document.getElementById(`mapping-${sheetName}-${index}`);
            if (mappingInput && mappingInput.value.trim()) {
                customMappings[header] = mappingInput.value.trim();
            }
        });

        AppState.mappingsConfig[sheetName] = {
            header_row: headerRow,
            custom_mappings: customMappings
        };
    });
}

// ===== 结果展示功能 =====

/**
 * 显示结果
 */
function showResults() {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';

    const sheetNames = Object.keys(AppState.sheetResults);

    if (sheetNames.length === 0) {
        container.innerHTML = '<p class="text-center">没有结果数据</p>';
        return;
    }

    sheetNames.forEach(sheetName => {
        const sheetData = AppState.sheetResults[sheetName];
        const resultCard = createResultCard(sheetName, sheetData);
        container.appendChild(resultCard);
    });
}

/**
 * 创建结果卡片
 * @param {string} sheetName - Sheet名称
 * @param {object} sheetData - Sheet数据
 * @returns {HTMLElement}
 */
function createResultCard(sheetName, sheetData) {
    const card = document.createElement('div');
    card.className = 'sheet-result-card';

    const headerHtml = `
        <div class="sheet-result-header">
            <h3>${sheetName}</h3>
            <span class="record-count">共 ${sheetData.row_count || 0} 条记录</span>
        </div>
    `;

    const tableHtml = `
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>序号</th>
                        ${sheetData.standard_headers.map(header => `<th>${header}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    <tr class="mapping-row">
                        <td>映射关系</td>
                        ${sheetData.matched_headers.map(mapping => `<td>${mapping || '未映射'}</td>`).join('')}
                    </tr>
                    ${sheetData.data.map(row => `
                        <tr>
                            ${row.map(cell => `<td>${cell || ''}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

    card.innerHTML = headerHtml + tableHtml;
    return card;
}

// ===== 数据导出功能 =====

/**
 * 导出数据
 */
async function exportData() {
    if (!AppState.sheetResults || Object.keys(AppState.sheetResults).length === 0) {
        showToast('没有可导出的数据', 'warning');
        return;
    }

    try {
        showToast('正在导出...', 'info');

        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sheet_results: AppState.sheetResults
            })
        });

        if (response.ok) {
            // 下载文件
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `数据整理结果_${new Date().getTime()}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showToast('导出成功', 'success');
        } else {
            const data = await response.json();
            showToast(data.error || '导出失败', 'error');
        }
    } catch (error) {
        console.error('导出错误:', error);
        showToast('导出失败，请重试', 'error');
    }
}

// ===== 初始化 =====

/**
 * 初始化应用
 */
function initApp() {
    // 初始化拖拽上传
    initDragAndDrop();

    console.log('数据处理工具已启动');
}

// DOM加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
