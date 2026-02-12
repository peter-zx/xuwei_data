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
let fileId = null; // 文件唯一标识
let cachedConfig = null; // 缓存的配置

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

            // 生成文件ID并检查缓存
            fileId = generateFileId(file.name, file.size, data.sheet_count);
            cachedConfig = loadMappingCache(fileId);
            
            if (cachedConfig) {
                showToast('已加载上次配置的映射', 'success');
            }

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

    // 如果有缓存配置，优先使用
    if (cachedConfig && !Object.keys(mappings).length) {
        headerRows = cachedConfig.headerRows || {};
        mappings = cachedConfig.mappings || {};
    }

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

// 执行数据比对
async function performDataComparison() {
    try {
        const response = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: uploadedFile,
                mappings: mappings
            })
        });

        const data = await response.json();

        if (data.success) {
            comparisonResults = data;
            renderComparisonInterface();
            showToast('比对完成');
        } else {
            console.error('比对失败:', data.error);
            showToast(data.error, 'error');
        }
    } catch (error) {
        console.error('比对请求失败:', error);
        showToast('比对失败，请重试', 'error');
    }
}

// 渲染比对界面
function renderComparisonInterface() {
    if (!comparisonResults) {
        showToast('暂无比对数据', 'error');
        return;
    }

    const { stats, sheet_names, people_list } = comparisonResults;

    // 显示统计
    document.getElementById('comparisonSummary').innerHTML = `
        <div class="summary-item">
            <h4>总人数</h4>
            <div class="value">${stats.total}</div>
        </div>
        <div class="summary-item">
            <h4>相同人</h4>
            <div class="value" style="color: #28a745">${stats.same_count}</div>
        </div>
        <div class="summary-item">
            <h4>非相同人</h4>
            <div class="value" style="color: #dc3545">${stats.diff_count}</div>
        </div>
    `;

    // 渲染筛选按钮
    document.getElementById('comparisonTabs').innerHTML = `
        <button class="comparison-tab active" data-filter="all">全部 (${stats.total})</button>
        <button class="comparison-tab" data-filter="same">相同人 (${stats.same_count})</button>
        <button class="comparison-tab" data-filter="diff">非相同人 (${stats.diff_count})</button>
        <input type="text" id="compareSearchInput" placeholder="搜索姓名..." class="search-input">
        <button class="btn btn-success" onclick="exportComparisonView()">导出</button>
    `;

    // 绑定筛选事件
    document.querySelectorAll('.comparison-tab').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.comparison-tab').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentComparisonFilter = e.target.dataset.filter;
            renderComparisonTable();
        });
    });

    currentComparisonFilter = 'all';
    renderComparisonTable();
}

// 导出比对数据
function exportComparisonData() {
    if (!comparisonResults) return;

    const standardFields = getStandardFields();
    const rows = [['状态', '姓名', ...standardFields.filter(f => f !== '姓名')]];

    comparisonResults.complete_groups.forEach(group => {
        rows.push(['完善', ...standardFields.map(field => group[field] || '')]);
    });

    comparisonResults.incomplete_groups.forEach(group => {
        rows.push(['不完善', ...standardFields.map(field => group[field] || '')]);
    });

    const csvContent = rows.map(row => row.join(',')).join('\n');
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `数据比对结果_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
}

function renderComparisonTable() {
    const { sheet_names, people_list } = comparisonResults;
    let filteredList = people_list;

    // 筛选
    if (currentComparisonFilter === 'same') {
        filteredList = people_list.filter(p => p._is_same);
    } else if (currentComparisonFilter === 'diff') {
        filteredList = people_list.filter(p => !p._is_same);
    }

    if (filteredList.length === 0) {
        document.getElementById('comparisonContent').innerHTML = '<p class="no-data-message">暂无数据</p>';
        return;
    }

    // 三列并排布局
    const columns = ['序号', '姓名', '身份证', '残疾证号'];

    let html = '<div class="compare-grid">';

    sheet_names.forEach((sheetName, sheetIndex) => {
        // 计算该sheet实际有数据的记录数
        const sheetDataCount = filteredList.filter(p => p._sheets[sheetName]).length;
        
        html += `
            <div class="compare-column">
                <div class="compare-column-header">${sheetName} (${sheetDataCount}条)</div>
                <table class="compare-table">
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${col}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${filteredList.map((person, rowIndex) => {
                            const record = person._sheets[sheetName];
                            const isDiff = !person._is_same;
                            const rowClass = isDiff ? 'row-diff' : '';

                            if (record) {
                                return `
                                    <tr class="${rowClass}" data-key="${person._key}" data-sheet="${sheetName}" data-row="${record._row_index}">
                                        <td class="row-number">${rowIndex + 1}</td>
                                        <td class="editable" data-field="姓名">${record['姓名'] || '-'}</td>
                                        <td class="editable" data-field="身份证">${record['身份证'] || '-'}</td>
                                        <td class="editable" data-field="残疾证号">${record['残疾证号'] || '-'}</td>
                                    </tr>
                                `;
                            } else {
                                return `
                                    <tr class="row-empty">
                                        <td class="row-number">${rowIndex + 1}</td>
                                        <td colspan="3">-</td>
                                    </tr>
                                `;
                            }
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    });

    html += '</div>';

    document.getElementById('comparisonContent').innerHTML = html;

    // 绑定搜索
    const searchInput = document.getElementById('compareSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const keyword = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('.compare-table tbody tr');
            rows.forEach(row => {
                const name = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';
                row.style.display = name.includes(keyword) ? '' : 'none';
            });
        });
    }

    // 绑定双击编辑
    document.querySelectorAll('.editable').forEach(cell => {
        cell.addEventListener('dblclick', (e) => {
            const cell = e.target;
            if (cell.querySelector('input')) return; // 已经在编辑中

            const oldValue = cell.textContent;
            const field = cell.dataset.field;
            const row = cell.closest('tr');
            const key = row.dataset.key;
            const sheetName = row.dataset.sheet;

            cell.innerHTML = `<input type="text" value="${oldValue}" class="edit-input">`;
            const input = cell.querySelector('input');
            input.focus();
            input.select();

            const saveEdit = () => {
                const newValue = input.value.trim();
                cell.textContent = newValue || '-';

                // 更新数据
                if (comparisonResults && comparisonResults.people_list) {
                    const person = comparisonResults.people_list.find(p => p._key === key);
                    if (person && person._sheets[sheetName]) {
                        person._sheets[sheetName][field] = newValue;
                    }
                }

                showToast('已编辑');
            };

            input.addEventListener('blur', saveEdit);
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') saveEdit();
            });
        });
    });
}

function exportComparisonView() {
    const { sheet_names, people_list } = comparisonResults;
    let filteredList = people_list;

    if (currentComparisonFilter === 'same') {
        filteredList = people_list.filter(p => p._is_same);
    } else if (currentComparisonFilter === 'diff') {
        filteredList = people_list.filter(p => !p._is_same);
    }

    const rows = [['序号', ...sheet_names.map(s => `${s}_姓名`), ...sheet_names.map(s => `${s}_身份证`), ...sheet_names.map(s => `${s}_残疾证号`), '状态']];

    filteredList.forEach((person, idx) => {
        const row = [idx + 1];
        sheet_names.forEach(sheet => {
            const record = person._sheets[sheet];
            row.push(record ? record['姓名'] || '' : '');
        });
        sheet_names.forEach(sheet => {
            const record = person._sheets[sheet];
            row.push(record ? record['身份证'] || '' : '');
        });
        sheet_names.forEach(sheet => {
            const record = person._sheets[sheet];
            row.push(record ? record['残疾证号'] || '' : '');
        });
        row.push(person._is_same ? '相同' : '非相同');
        rows.push(row);
    });

    const csvContent = rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `比对结果_${currentComparisonFilter}_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
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
    if (!comparisonResults) return;

    const { stats, complete_groups, incomplete_groups } = comparisonResults;

    document.getElementById('finalStats').innerHTML = `
        <div class="stat-card">
            <h3>总人数</h3>
            <div class="value">${stats.total_groups}</div>
        </div>
        <div class="stat-card">
            <h3>完善数据</h3>
            <div class="value">${stats.complete_count}</div>
        </div>
        <div class="stat-card">
            <h3>不完善数据</h3>
            <div class="value">${stats.incomplete_count}</div>
        </div>
    `;

    document.getElementById('finalTabs').innerHTML = `
        <button class="tab-btn active" data-type="complete">完善数据 (${stats.complete_count})</button>
        <button class="tab-btn" data-type="incomplete">不完善数据 (${stats.incomplete_count})</button>
    `;

    document.querySelectorAll('#finalTabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('#finalTabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentFinalTab = e.target.dataset.type;
            showFinalResultPanel();
        });
    });

    currentFinalTab = 'complete';
    showFinalResultPanel();
}

let currentFinalTab = 'complete';

function showFinalResultPanel() {
    const standardFields = getStandardFields();
    let dataToRender = currentFinalTab === 'complete' ? comparisonResults.complete_groups : comparisonResults.incomplete_groups;

    if (!dataToRender || dataToRender.length === 0) {
        document.getElementById('finalContent').innerHTML = '<p>暂无数据</p>';
        return;
    }

    const html = `
        <table class="result-table">
            <thead>
                <tr>
                    ${standardFields.map(field => `<th>${field}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                ${dataToRender.map(group => `
                    <tr class="${group._is_complete ? 'complete' : 'incomplete'}">
                        ${standardFields.map(field => `<td>${group[field] || '-'}</td>`).join('')}
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    document.getElementById('finalContent').innerHTML = html;
}
