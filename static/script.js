// 全局状态
let currentStep = 1;
let uploadedFile = null;
let fileData = null;
let sheetPreviews = {};
let sheetColumns = {};
let headerRows = {};
let mappings = {};
let mappedResults = null;
let comparisonResults = null;
let currentComparisonFilter = 'all';
let currentComparisonTab = 0;

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
    return ['姓名', '电话', '身份证', '残疾证', '身份证到期时间', '残疾证到期时间', '残疾证等级', '残疾证类型', '残疾证号'];
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
document.getElementById('backToUploadBtn')?.addEventListener('click', () => {
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

            // 保留映射状态，包括"未映射"（空字符串）
            mappings[sheetName].fields[field] = value;
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

    // 清理空的字段映射
    Object.keys(mappings).forEach(sheetName => {
        if (mappings[sheetName] && mappings[sheetName].fields) {
            const cleanedFields = {};
            Object.entries(mappings[sheetName].fields).forEach(([field, value]) => {
                if (value && value.trim() !== '') {
                    cleanedFields[field] = value;
                }
            });
            mappings[sheetName].fields = cleanedFields;
        }
    });

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
            mappedResults = data.results;
            renderMappedDataView(); // 显示映射后的原始数据
            showToast('数据映射完成');
        } else {
            console.error('映射失败:', data.error);
            showToast(data.error, 'error');
            updateStep(3);
        }
    } catch (error) {
        console.error('请求失败:', error);
        showToast('映射失败，请重试', 'error');
        updateStep(3);
    }
});



// 渲染映射数据视图（环节4）
function renderMappedDataView() {
    if (!mappedResults) return;

    const totalSheets = mappedResults.length;
    const totalRecords = mappedResults.reduce((sum, r) => sum + (r.record_count || 0), 0);
    const successCount = mappedResults.filter(r => r.success).length;

    document.getElementById('mappingSummary').innerHTML = `
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

    document.getElementById('dataViewTabs').innerHTML = mappedResults.map((result, index) => `
        <button class="tab-btn ${index === 0 ? 'active' : ''}" data-index="${index}">
            ${result.name} (${result.record_count || 0}条)
        </button>
    `).join('');

    document.querySelectorAll('#dataViewTabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('#dataViewTabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            showMappedDataPanel(parseInt(e.target.dataset.index));
        });
    });

    showMappedDataPanel(0);
}

function showMappedDataPanel(index) {
    const result = mappedResults[index];
    if (!result) {
        document.getElementById('dataViewContent').innerHTML = '<p>暂无数据</p>';
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

    document.getElementById('dataViewContent').innerHTML = html;
}

// 环节4: 返回配置映射
const backToMappingBtn = document.getElementById('backToMappingBtn');
if (backToMappingBtn) {
    backToMappingBtn.addEventListener('click', () => {
        updateStep(3);
    });
}

// 环节4: 进入数据比对
const toComparisonBtn = document.getElementById('toComparisonBtn');
if (toComparisonBtn) {
    toComparisonBtn.addEventListener('click', () => {
        performDataComparison();
        updateStep(5);
    });
}

// 重新配置映射

// 数据比对 - 返回数据视图
const backToDataViewBtn = document.getElementById('backToDataViewBtn');
if (backToDataViewBtn) {
    backToDataViewBtn.addEventListener('click', () => {
        updateStep(4);
    });
}

// 数据比对 - 查看结果
const toResultsBtn = document.getElementById('toResultsBtn');
if (toResultsBtn) {
    toResultsBtn.addEventListener('click', () => {
        renderFinalResults();
        updateStep(6);
    });
}

// 结果页 - 返回比对
const backToComparisonBtn = document.getElementById('backToComparisonBtn');
if (backToComparisonBtn) {
    backToComparisonBtn.addEventListener('click', () => {
        updateStep(5);
    });
}

// 重置
const resetBtn = document.getElementById('resetBtn');
if (resetBtn) {
    resetBtn.addEventListener('click', () => {
        resetAll();
        updateStep(1);
    });
}

// 执行数据比对
function performDataComparison() {
    if (!mappedResults || mappedResults.length < 2) {
        showToast('需要至少2个Sheet的数据进行比对', 'error');
        return;
    }

    comparisonResults = [];
    const resultSheets = mappedResults.filter(r => r.success && r.data && r.data.length > 0);

    if (resultSheets.length < 2) {
        showToast('有效数据Sheet不足2个，无法比对', 'error');
        return;
    }

    // 构建人员字典 (姓名 + 残疾证号)
    const peopleDict = {};

    // 遍历所有Sheet的数据
    resultSheets.forEach((sheetResult, sheetIndex) => {
        const sheetName = sheetResult.name;

        sheetResult.data.forEach(record => {
            const key = getPersonKey(record);
            const standardFields = getStandardFields();

            if (key) {
                if (!peopleDict[key]) {
                    peopleDict[key] = {
                        key: key,
                        sheets: {},
                        matchCount: 0
                    };
                }
                peopleDict[key].sheets[sheetName] = record;
                peopleDict[key].matchCount++;

                // 添加缺失字段
                standardFields.forEach(field => {
                    if (!peopleDict[key][field]) {
                        peopleDict[key][field] = record[field] || '';
                    }
                });
            }
        });
    });

    // 转换为数组并标记匹配状态
    Object.values(peopleDict).forEach(person => {
        const isMatched = person.matchCount === resultSheets.length;
        comparisonResults.push({
            ...person,
            status: isMatched ? 'matched' : 'unmatched',
            statusText: isMatched ? '相同人' : '非相同人'
        });
    });

    // 排序：相同人在前
    comparisonResults.sort((a, b) => {
        if (a.status === b.status) {
            return a.key.localeCompare(b.key);
        }
        return a.status === 'matched' ? -1 : 1;
    });

    renderComparisonInterface();
}

function getPersonKey(record) {
    const name = record['姓名'] || '';
    const disabilityCard = record['残疾证'] || '';
    if (name && disabilityCard) {
        return `${name}_${disabilityCard}`;
    }
    return null;
}

// 渲染比对界面
function renderComparisonInterface() {
    if (!comparisonResults) {
        showToast('暂无比对数据', 'error');
        return;
    }

    // 统计
    const total = comparisonResults.length;
    const matched = comparisonResults.filter(p => p.status === 'matched').length;
    const unmatched = comparisonResults.filter(p => p.status === 'unmatched').length;

    document.getElementById('comparisonSummary').innerHTML = `
        <div class="summary-item">
            <h4>总人数</h4>
            <div class="value">${total}</div>
        </div>
        <div class="summary-item">
            <h4>相同人</h4>
            <div class="value" style="color: #28a745">${matched}</div>
        </div>
        <div class="summary-item">
            <h4>非相同人</h4>
            <div class="value" style="color: #dc3545">${unmatched}</div>
        </div>
    `;

    // 渲染Tab
    const sheetNames = mappedResults.filter(r => r.success).map(r => r.name);
    document.getElementById('comparisonTabs').innerHTML = sheetNames.map((name, index) => `
        <button class="comparison-tab ${index === 0 ? 'active' : ''}" data-index="${index}">
            ${name}
        </button>
    `).join('');

    // 绑定Tab事件
    document.querySelectorAll('.comparison-tab').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.comparison-tab').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentComparisonTab = parseInt(e.target.dataset.index);
            renderComparisonTable();
        });
    });

    // 绑定筛选按钮
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentComparisonFilter = e.target.dataset.filter;
            renderComparisonTable();
        });
    });

    // 绑定导出按钮
    document.getElementById('exportBtn').addEventListener('click', exportComparisonData);

    renderComparisonTable();
}

function renderComparisonTable() {
    const sheetName = mappedResults.filter(r => r.success)[currentComparisonTab].name;
    const standardFields = getStandardFields();

    let filteredData = comparisonResults;

    if (currentComparisonFilter !== 'all') {
        filteredData = comparisonResults.filter(p => p.status === currentComparisonFilter);
    }

    const tableHtml = `
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>状态</th>
                    <th>${sheetName}</th>
                    ${mappedResults.filter(r => r.success).map(r => r.name).filter(n => n !== sheetName).map(name => `<th>${name}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                ${filteredData.map(person => `
                    <tr class="${person.status}">
                        <td>${person.statusText}</td>
                        ${mappedResults.filter(r => r.success).map(r => r.name).map(name => {
                            const record = person.sheets[name];
                            return record ? `<td>${record['姓名'] || '-'}</td>` : '<td>-</td>';
                        }).join('')}
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    document.getElementById('comparisonContent').innerHTML = tableHtml;
}

// 导出比对数据
function exportComparisonData() {
    if (!comparisonResults) return;

    const standardFields = getStandardFields();
    const rows = [['状态', ...mappedResults.filter(r => r.success).map(r => r.name), ...standardFields]];

    comparisonResults.forEach(person => {
        const row = [person.statusText];
        mappedResults.filter(r => r.success).forEach(r => {
            const record = person.sheets[r.name];
            row.push(record ? record['姓名'] : '-');
        });
        standardFields.forEach(field => {
            row.push(person[field] || '');
        });
        rows.push(row);
    });

    const csvContent = rows.map(row => row.join(',')).join('\n');
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `数据比对结果_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
}

// 渲染最终结果
function renderFinalResults() {
    if (!mappedResults) return;

    const totalSheets = mappedResults.length;
    const totalRecords = mappedResults.reduce((sum, r) => sum + (r.record_count || 0), 0);
    const successCount = mappedResults.filter(r => r.success).length;

    document.getElementById('finalStats').innerHTML = `
        <div class="stat-card">
            <h3>总Sheet数</h3>
            <div class="value">${totalSheets}</div>
        </div>
        <div class="stat-card">
            <h3>总记录数</h3>
            <div class="value">${totalRecords}</div>
        </div>
        <div class="stat-card">
            <h3>总人数</h3>
            <div class="value">${comparisonResults ? comparisonResults.length : 0}</div>
        </div>
        <div class="stat-card">
            <h3>相同人</h3>
            <div class="value">${comparisonResults ? comparisonResults.filter(p => p.status === 'matched').length : 0}</div>
        </div>
    `;

    document.getElementById('finalTabs').innerHTML = mappedResults.map((result, index) => `
        <button class="tab-btn ${index === 0 ? 'active' : ''}" data-index="${index}">
            ${result.name} (${result.record_count || 0}条)
        </button>
    `).join('');

    document.querySelectorAll('#finalTabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('#finalTabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            showFinalResultPanel(parseInt(e.target.dataset.index));
        });
    });

    showFinalResultPanel(0);
}

function showFinalResultPanel(index) {
    const result = mappedResults[index];
    if (!result) {
        document.getElementById('finalContent').innerHTML = '<p>暂无数据</p>';
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

    document.getElementById('finalContent').innerHTML = html;
}
