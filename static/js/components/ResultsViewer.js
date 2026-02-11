/**
 * 结果查看器组件 - Excel式标签切换
 */

import { exportData } from '../services/api.js';
import { showToast } from '../utils/helpers.js';

export class ResultsViewer {
    constructor() {
        this.sheetResults = {};
    }

    /**
     * 渲染结果
     */
    render(sheetResults) {
        this.sheetResults = sheetResults;
        const container = document.getElementById('resultsContainer');
        if (!container) return;

        container.innerHTML = '';

        const sheetNames = Object.keys(sheetResults);

        if (sheetNames.length === 0) {
            container.innerHTML = '<p class="text-center">没有结果数据</p>';
            return;
        }

        // 创建Sheet标签导航
        const tabsContainer = this.createTabs(sheetNames);
        container.appendChild(tabsContainer);

        // 创建Sheet内容区域
        const contentContainer = document.createElement('div');
        contentContainer.className = 'sheets-content';

        sheetNames.forEach((sheetName, index) => {
            const sheetContent = this.createSheetContent(sheetName, sheetResults[sheetName], index === 0);
            contentContainer.appendChild(sheetContent);
        });

        container.appendChild(contentContainer);
    }

    /**
     * 创建Sheet标签导航
     */
    createTabs(sheetNames) {
        const tabsContainer = document.createElement('div');
        tabsContainer.className = 'sheet-tabs';

        sheetNames.forEach((sheetName, index) => {
            const sheetData = this.sheetResults[sheetName];
            const tab = document.createElement('div');
            tab.className = `sheet-tab ${index === 0 ? 'active' : ''}`;
            tab.dataset.sheet = sheetName;
            tab.innerHTML = `
                <i class="fas fa-table"></i>
                <span>${sheetName}</span>
                <span class="record-badge">${sheetData.row_count || 0}条</span>
            `;

            tab.addEventListener('click', () => this.switchSheet(sheetName));

            tabsContainer.appendChild(tab);
        });

        return tabsContainer;
    }

    /**
     * 切换Sheet
     */
    switchSheet(sheetName) {
        document.querySelectorAll('.sheet-tab').forEach(tab => {
            if (tab.dataset.sheet === sheetName) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });

        document.querySelectorAll('.sheet-content').forEach(content => {
            if (content.dataset.sheet === sheetName) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
    }

    /**
     * 创建Sheet内容
     */
    createSheetContent(sheetName, sheetData, isActive) {
        const content = document.createElement('div');
        content.className = `sheet-content ${isActive ? 'active' : ''}`;
        content.dataset.sheet = sheetName;

        const card = document.createElement('div');
        card.className = 'sheet-result-card';

        const headerHtml = `
            <div class="sheet-result-header">
                <h3><i class="fas fa-file-excel"></i> ${sheetName}</h3>
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
        content.appendChild(card);

        return content;
    }

    /**
     * 导出数据
     */
    async export() {
        if (!this.sheetResults || Object.keys(this.sheetResults).length === 0) {
            showToast('没有可导出的数据', 'warning');
            return;
        }

        try {
            showToast('正在导出...', 'info');

            const blob = await exportData(this.sheetResults);

            // 下载文件
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `数据整理结果_${Date.now()}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showToast('导出成功', 'success');
        } catch (error) {
            console.error('导出错误:', error);
            showToast('导出失败，请重试', 'error');
        }
    }

    reset() {
        this.sheetResults = {};

        const container = document.getElementById('resultsContainer');
        if (container) {
            container.innerHTML = '';
        }
    }
}
