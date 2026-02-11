/**
 * Sheet预览组件
 * 显示Sheet前5行数据，允许用户设置标题所在行
 */

import { STANDARD_HEADERS } from '../utils/constants.js';

export class SheetPreview {
    constructor(onConfirm) {
        this.onConfirm = onConfirm;
        this.sheetInfo = {};
        this.headerRows = {};
    }

    /**
     * 渲染Sheet预览
     */
    render(sheetInfo) {
        this.sheetInfo = sheetInfo;
        const container = document.getElementById('previewContainer');
        if (!container) return;

        container.innerHTML = '';

        const sheetNames = Object.keys(sheetInfo);

        if (sheetNames.length === 0) {
            container.innerHTML = '<p class="text-center">没有找到Sheet</p>';
            return;
        }

        sheetNames.forEach(sheetName => {
            const previewCard = this.createPreviewCard(sheetName, sheetInfo[sheetName]);
            container.appendChild(previewCard);
        });
    }

    /**
     * 创建预览卡片
     */
    createPreviewCard(sheetName, sheetData) {
        const card = document.createElement('div');
        card.className = 'sheet-preview-card';

        // 模拟前5行数据（实际应该从后端获取）
        const previewData = this.generatePreviewData(sheetData);

        const headerHtml = `
            <div class="preview-card-header">
                <h3><i class="fas fa-file-alt"></i> ${sheetName}</h3>
                <span class="info-badge">共 ${sheetData.row_count} 行, ${sheetData.col_count} 列</span>
            </div>
        `;

        const bodyHtml = `
            <div class="preview-card-body">
                <div class="header-row-setting">
                    <label for="header-row-${sheetName}">
                        <i class="fas fa-heading"></i> 标题所在行：
                    </label>
                    <input
                        type="number"
                        id="header-row-${sheetName}"
                        min="1"
                        max="10"
                        value="1"
                        class="header-row-input"
                        onchange="this.updatePreview('${sheetName}')"
                    >
                    <span class="hint">默认第1行（请根据实际数据调整）</span>
                </div>

                <div class="preview-table-container">
                    <table class="preview-table">
                        <thead>
                            <tr id="preview-header-${sheetName}">
                                ${previewData[0].map((cell, index) =>
                                    `<th>${cell || ''}</th>`
                                ).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${previewData.slice(1).map(row =>
                                `<tr>${row.map(cell => `<td>${cell || ''}</td>`).join('')}</tr>`
                            ).join('')}
                        </tbody>
                    </table>
                </div>

                <div class="preview-info">
                    <p><i class="fas fa-info-circle"></i> 提示：请查看上方表格，确认标题所在的行号，然后在输入框中设置正确的标题行。</p>
                </div>
            </div>
        `;

        card.innerHTML = headerHtml + bodyHtml;

        // 绑定输入框事件
        const input = card.querySelector(`#header-row-${sheetName}`);
        input.addEventListener('change', () => this.updatePreview(sheetName));

        return card;
    }

    /**
     * 生成预览数据（模拟前5行）
     */
    generatePreviewData(sheetData) {
        const headers = sheetData.original_headers || [];
        const rowCount = Math.min(5, sheetData.row_count || 5);
        const colCount = sheetData.col_count || headers.length;

        // 生成前5行数据
        const data = [];
        for (let i = 0; i < rowCount; i++) {
            const row = [];
            for (let j = 0; j < colCount; j++) {
                if (i === 0) {
                    // 第一行显示原始表头
                    row.push(headers[j] || `列${j + 1}`);
                } else {
                    // 其他行显示模拟数据
                    row.push(`数据${i}-${j + 1}`);
                }
            }
            data.push(row);
        }

        return data;
    }

    /**
     * 更新预览（当用户修改标题行时）
     */
    updatePreview(sheetName) {
        const input = document.getElementById(`header-row-${sheetName}`);
        const headerRow = parseInt(input.value) || 1;

        // 更新存储的标题行
        this.headerRows[sheetName] = headerRow;

        // 可以在这里添加逻辑来高亮显示标题行
        console.log(`${sheetName} 标题行设置为: ${headerRow}`);
    }

    /**
     * 收集标题行配置
     */
    collectHeaderRows() {
        const sheetNames = Object.keys(this.sheetInfo);

        sheetNames.forEach(sheetName => {
            const input = document.getElementById(`header-row-${sheetName}`);
            if (input) {
                this.headerRows[sheetName] = parseInt(input.value) || 1;
            }
        });

        return this.headerRows;
    }

    /**
     * 确认并继续
     */
    confirm() {
        const headerRows = this.collectHeaderRows();
        this.onConfirm(headerRows);
    }

    /**
     * 重置
     */
    reset() {
        this.sheetInfo = {};
        this.headerRows = {};

        const container = document.getElementById('previewContainer');
        if (container) {
            container.innerHTML = '';
        }
    }
}
