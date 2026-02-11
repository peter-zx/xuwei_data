/**
 * 映射编辑器组件
 */

import { STANDARD_HEADERS, JIAGE_MAPPINGS } from '../utils/constants.js';

export class MappingEditor {
    constructor() {
        this.sheetInfo = {};
        this.mappingsConfig = {};
    }

    /**
     * 渲染映射编辑器
     * @param {object} sheetInfo - Sheet信息
     * @param {object} headerRows - 标题行配置
     */
    render(sheetInfo, headerRows = {}) {
        this.sheetInfo = sheetInfo;
        this.headerRows = headerRows;
        const container = document.getElementById('mappingContainer');
        if (!container) return;

        container.innerHTML = '';

        const sheetNames = Object.keys(sheetInfo);

        if (sheetNames.length === 0) {
            container.innerHTML = '<p class="text-center">没有找到Sheet</p>';
            return;
        }

        sheetNames.forEach(sheetName => {
            const card = this.createSheetCard(sheetName, sheetInfo[sheetName], headerRows[sheetName] || 1);
            container.appendChild(card);
        });
    }

    /**
     * 创建Sheet卡片
     */
    createSheetCard(sheetName, sheetData, headerRow = 1) {
        const card = document.createElement('div');
        card.className = 'sheet-mapping-card';

        const isJiageSheet = sheetName.includes('佳哥') && sheetName.includes('26');
        const autoMappings = this.getAutoMappings(sheetData.original_headers);

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
                    <input type="number" min="1" max="10" value="${headerRow}" id="header-row-${sheetName}">
                    <span style="color: var(--text-muted); font-size: 0.875rem;">当前设置: 第${headerRow}行</span>
                </div>

                <div class="headers-info">
                    <strong>原始表头:</strong>
                    <span>${sheetData.original_headers.join(', ') || '无'}</span>
                </div>

                <div class="mapping-grid">
                    ${STANDARD_HEADERS.map((header, index) => {
                        const autoValue = autoMappings[header] || '';
                        const jiageValue = isJiageSheet ? (JIAGE_MAPPINGS[header] || '') : '';
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
     */
    getAutoMappings(originalHeaders) {
        const mappings = {};

        if (!originalHeaders || originalHeaders.length === 0) {
            STANDARD_HEADERS.forEach(header => {
                mappings[header] = '';
            });
            return mappings;
        }

        STANDARD_HEADERS.forEach(header => {
            let found = false;

            for (let i = 0; i < originalHeaders.length; i++) {
                const originalHeader = String(originalHeaders[i] || '').toLowerCase();
                if (originalHeader && originalHeader.includes(header.toLowerCase())) {
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

    /**
     * 收集映射配置
     */
    collectMappings() {
        this.mappingsConfig = {};

        const sheetNames = Object.keys(this.sheetInfo);

        sheetNames.forEach(sheetName => {
            const sheetData = this.sheetInfo[sheetName];

            const headerRowInput = document.getElementById(`header-row-${sheetName}`);
            const headerRow = headerRowInput ? parseInt(headerRowInput.value) || 1 : 1;

            const customMappings = {};
            sheetData.standard_headers.forEach((header, index) => {
                const mappingInput = document.getElementById(`mapping-${sheetName}-${index}`);
                if (mappingInput && mappingInput.value.trim()) {
                    customMappings[header] = mappingInput.value.trim();
                }
            });

            this.mappingsConfig[sheetName] = {
                header_row: headerRow,
                custom_mappings: customMappings
            };
        });

        return this.mappingsConfig;
    }

    reset() {
        this.sheetInfo = {};
        this.mappingsConfig = {};

        const container = document.getElementById('mappingContainer');
        if (container) {
            container.innerHTML = '';
        }
    }
}
