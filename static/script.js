// 全局状态
let currentStep = 1;
let uploadedFile = null;
let fileData = null;
let sheetPreviews = {};
let sheetColumns = {};
let headerRows = {};
let mappings = {};

// DOM 元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const sheetCount = document.getElementById('sheetCount');
const sheetsList = document.getElementById('sheetsList');
const toast = document.getElementById('toast');

// 标准字段（可配置）
function getStandardFields() {
    return ['姓名', '电话', '身份证', '残疾证', '身份证到期时间', '残疾证到期时间', '残疾证等级', '残疾证类型'];
}

// 显示提示信息
function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 更新步骤
function updateStep(step) {
    document.querySelectorAll('.step').forEach(s => {
        const stepNum = parseInt(s.dataset.step);
        s.classList.remove('active', 'completed');
        if (stepNum === step) {
            s.classList.add('active');
        } else if (stepNum < step) {
            s.classList.add('completed');
        }
    });

    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`step${step}`).classList.add('active');

    currentStep = step;
}

// 文件上传相关
uploadArea.addEventListener('click', () => fileInput.click());
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});
uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});
uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

async function handleFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            uploadedFile = data.filename;
            fileData = data.sheets;

            fileName.textContent = file.name;
            sheetCount.textContent = `Sheet数量: ${data.sheet_count}`;

            sheetsList.innerHTML = data.sheets.map(sheet => `
                <div class="sheet-item">
                    <span class="sheet-name">${sheet.name}</span>
                    <span class="sheet-stats">${sheet.rows} 行 × ${sheet.columns} 列</span>
                </div>
            `).join('');

            uploadArea.style.display = 'none';
            fileInfo.style.display = 'block';
            showToast('文件上传成功');
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        showToast('上传失败，请重试', 'error');
    }
}

// 重新上传
document.getElementById('reuploadBtn').addEventListener('click', () => {
    resetAll();
    updateStep(1);
});

// 重置所有状态
function resetAll() {
    uploadedFile = null;
    fileData = null;
    sheetPreviews = {};
    sheetColumns = {};
    headerRows = {};
    mappings = {};
    fileInput.value = '';
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
}

// 跳转到预览步骤
document.getElementById('toPreviewBtn').addEventListener('click', async () => {
    await loadSheetPreviews();
    renderPreviewInterface();
    updateStep(2);
});

// 加载每个Sheet的预览数据
async function loadSheetPreviews() {
    if (!fileData || fileData.length === 0) {
        showToast('没有Sheet数据', 'error');
        return;
    }

    if (!uploadedFile) {
        showToast('文件名丢失', 'error');
        return;
    }

    for (const sheet of fileData) {
        try {
            const response = await fetch('/api/sheet-preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: uploadedFile,
                    sheet_name: sheet.name,
                    max_rows: CONFIG.maxPreviewRows
                })
            });

            const data = await response.json();
            if (data.success) {
                sheetPreviews[sheet.name] = data.data;
                // 默认表头在第1行（索引0）
                headerRows[sheet.name] = 0;
            } else {
                console.error(`加载 ${sheet.name} 预览失败:`, data.error);
                showToast(`加载 ${sheet.name} 预览失败: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error(`加载 ${sheet.name} 预览失败:`, error);
            showToast(`加载 ${sheet.name} 预览失败`, 'error');
        }
    }
}

// 渲染预览界面
function renderPreviewInterface() {
    const container = document.getElementById('previewSheets');

    container.innerHTML = fileData.map(sheet => {
        const preview = sheetPreviews[sheet.name] || [];
        const currentHeaderRow = headerRows[sheet.name] || 0;

        return `
            <div class="preview-sheet">
                <div class="preview-sheet-header">
                    <span class="preview-sheet-title">${sheet.name}</span>
                    <div class="header-row-selector">
                        <label>表头所在行:</label>
                        <select class="header-row-select-preview" data-sheet="${sheet.name}">
                            ${Array.from({length: CONFIG.headerRowOptions}, (_, i) => `
                                <option value="${i}" ${currentHeaderRow === i ? 'selected' : ''}>第 ${i + 1} 行</option>
                            `).join('')}
                        </select>
                    </div>
                </div>
                <div class="preview-table-container">
                    <table class="preview-table">
                        <thead>
                            <tr>
                                <th>行号</th>
                                ${preview.length > 0 ? preview[0].map((_, i) => `<th>列 ${i + 1}</th>`).join('') : ''}
                            </tr>
                        </thead>
                        <tbody>
                            ${preview.map((row, idx) => `
                                <tr class="${idx === currentHeaderRow ? 'header-row' : ''}">
                                    <td>${idx + 1}</td>
                                    ${row.map(cell => `<td>${cell}</td>`).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }).join('');

    bindPreviewEvents();
}

function bindPreviewEvents() {
    document.querySelectorAll('.header-row-select-preview').forEach(select => {
        select.addEventListener('change', (e) => {
            const sheetName = e.target.dataset.sheet;
            const headerRow = parseInt(e.target.value);
            headerRows[sheetName] = headerRow;

            // 高亮选中的表头行
            const table = e.target.closest('.preview-sheet').querySelector('.preview-table');
            table.querySelectorAll('tbody tr').forEach((tr, idx) => {
                if (idx === headerRow) {
                    tr.classList.add('header-row');
                } else {
                    tr.classList.remove('header-row');
                }
            });
        });
    });
}

// 上一步 - 返回上传
document.getElementById('backToUploadBtn').addEventListener('click', () => {
    updateStep(1);
});

// 跳转到映射步骤
document.getElementById('toMappingBtn').addEventListener('click', async () => {
    await loadSheetColumns();
    renderMappingInterface();
    updateStep(3);
});

// 加载每个Sheet的列名
async function loadSheetColumns() {
    for (const sheet of fileData) {
        const headerRow = headerRows[sheet.name] || 0;

        try {
            const response = await fetch('/api/columns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: uploadedFile,
                    sheet_name: sheet.name,
                    header_row: headerRow
                })
            });

            const data = await response.json();
            if (data.success) {
                sheetColumns[sheet.name] = data.columns;
            } else {
                console.error(`加载 ${sheet.name} 列名失败:`, data.error);
                showToast(`加载 ${sheet.name} 列名失败: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error(`加载 ${sheet.name} 列名失败:`, error);
            showToast(`加载 ${sheet.name} 列名失败`, 'error');
        }
    }
}

// 渲染映射界面
function renderMappingInterface() {
    const container = document.getElementById('mappingSheets');

    container.innerHTML = fileData.map(sheet => {
        const columns = sheetColumns[sheet.name] || [];
        const headerRow = headerRows[sheet.name] || 0;

        // 初始化映射
        if (!mappings[sheet.name]) {
            // 尝试自动匹配
            const autoFields = {};
            getStandardFields().forEach(field => {
                const matched = columns.find(col => col.includes(field));
                if (matched) {
                    autoFields[field] = matched;
                }
            });

            mappings[sheet.name] = {
                header_row: headerRow,
                fields: autoFields
            };
        }

        const mapping = mappings[sheet.name];

        return `
            <div class="mapping-sheet">
                <div class="mapping-sheet-header">
                    <span class="mapping-sheet-title">${sheet.name}</span>
                    <span class="auto-mapping-badge">表头: 第 ${headerRow + 1} 行</span>
                </div>
                <div class="field-mapping">
                    ${getStandardFields().map(field => `
                        <div class="field-mapping-item">
                            <label>${field}:</label>
                            <select class="field-select" data-sheet="${sheet.name}" data-field="${field}">
                                <option value="">-- 未映射 --</option>
                                ${columns.map(col => `
                                    <option value="${col}" ${mapping.fields[field] === col ? 'selected' : ''}>${col}</option>
                                `).join('')}
                            </select>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }).join('');

    bindMappingEvents();
}

function bindMappingEvents() {
    document.querySelectorAll('.field-select').forEach(select => {
        select.addEventListener('change', (e) => {
            const sheetName = e.target.dataset.sheet;
            const field = e.target.dataset.field;
            const value = e.target.value;

            if (!mappings[sheetName].fields) {
                mappings[sheetName].fields = {};
            }

            if (value) {
                mappings[sheetName].fields[field] = value;
            } else {
                delete mappings[sheetName].fields[field];
            }
        });
    });
}

// 上一步 - 返回预览
document.getElementById('backToPreviewBtn').addEventListener('click', () => {
    updateStep(2);
});

// 分析数据
document.getElementById('toAnalyzeBtn').addEventListener('click', async () => {
    updateStep(4);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: uploadedFile,
                mappings: mappings
            })
        });

        const data = await response.json();

        if (data.success) {
            window.analysisResults = data.results;
            renderResults(data.results);
            updateStep(5);
            showToast('数据分析完成');
        } else {
            showToast(data.error, 'error');
            updateStep(3);
        }
    } catch (error) {
        showToast('分析失败，请重试', 'error');
        updateStep(3);
    }
});

// 渲染结果
function renderResults(results) {
    const totalSheets = results.length;
    const totalRecords = results.reduce((sum, r) => sum + (r.record_count || 0), 0);
    const successCount = results.filter(r => r.success).length;

    document.getElementById('summaryStats').innerHTML = `
        <div class="stat-card">
            <h3>总Sheet数</h3>
            <div class="value">${totalSheets}</div>
        </div>
        <div class="stat-card">
            <h3>总记录数</h3>
            <div class="value">${totalRecords}</div>
        </div>
        <div class="stat-card">
            <h3>成功处理</h3>
            <div class="value">${successCount}</div>
        </div>
    `;

    // 更新页面标题
    document.querySelector('.results-header h2').textContent = '映射结果';

    document.getElementById('resultsTabs').innerHTML = results.map((result, index) => `
        <button class="tab-btn ${index === 0 ? 'active' : ''}" data-index="${index}">
            ${result.name} (${result.record_count || 0}条)
        </button>
    `).join('');

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            showResultPanel(parseInt(e.target.dataset.index));
        });
    });

    showResultPanel(0);
}

function showResultPanel(index) {
    const result = window.analysisResults[index];

    if (!result) {
        document.getElementById('resultsContent').innerHTML = '<p>暂无数据</p>';
        return;
    }

    const { mapping, data, success, error } = result;

    let html = '';

    if (!success) {
        html = `<div class="error-message">处理失败: ${error}</div>`;
    } else if (data.length === 0) {
        html = '<div class="no-data-message">没有提取到数据，请检查映射配置</div>';
    } else {
        html += `
            <div class="mapping-info">
                <h4>映射关系</h4>
                ${Object.entries(mapping).map(([field, col]) => `
                    <span class="mapping-item">${field} ← ${col}</span>
                `).join('')}
            </div>
            <table class="result-table">
                <thead>
                    <tr>
                        ${getStandardFields().map(field => `<th>${field}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.map(row => `
                        <tr>
                            ${getStandardFields().map(field => `<td>${row[field] || ''}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    document.getElementById('resultsContent').innerHTML = html;
}

// 重新配置映射
document.getElementById('backToMappingBtn').addEventListener('click', () => {
    updateStep(3);
});

// 重置
document.getElementById('resetBtn').addEventListener('click', () => {
    resetAll();
    updateStep(1);
});
