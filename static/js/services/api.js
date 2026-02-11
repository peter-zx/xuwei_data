/**
 * API服务模块
 */

import { APP_CONFIG } from '../utils/constants.js';

/**
 * 上传文件
 * @param {File} file - 文件对象
 * @returns {Promise<object>} 上传结果
 */
export async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${APP_CONFIG.API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

/**
 * 分析数据
 * @param {string} filepath - 文件路径
 * @param {object} mappingsConfig - 映射配置
 * @returns {Promise<object>} 分析结果
 */
export async function analyzeData(filepath, mappingsConfig) {
    const response = await fetch(`${APP_CONFIG.API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filepath,
            mappings_config: mappingsConfig
        })
    });

    return await response.json();
}

/**
 * 导出数据
 * @param {object} sheetResults - Sheet结果数据
 * @returns {Promise<Blob>} Excel文件
 */
export async function exportData(sheetResults) {
    const response = await fetch(`${APP_CONFIG.API_BASE_URL}/export`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sheet_results: sheetResults
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '导出失败');
    }

    return await response.blob();
}
