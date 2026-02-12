// 映射配置缓存管理
// 使用 localStorage 存储用户配置的映射关系，下次上传相同文件时自动加载

const MAPPING_CACHE_KEY = 'excel_mapping_cache';

/**
 * 生成文件唯一标识
 * 使用文件名 + 文件大小 + sheet数量组合
 */
function generateFileId(filename, fileSize, sheetCount) {
    return `${filename}_${fileSize}_${sheetCount}`;
}

/**
 * 获取所有缓存
 */
function getAllCache() {
    try {
        const cache = localStorage.getItem(MAPPING_CACHE_KEY);
        return cache ? JSON.parse(cache) : {};
    } catch (e) {
        console.error('读取映射缓存失败:', e);
        return {};
    }
}

/**
 * 保存所有缓存
 */
function saveAllCache(cache) {
    try {
        localStorage.setItem(MAPPING_CACHE_KEY, JSON.stringify(cache));
    } catch (e) {
        console.error('保存映射缓存失败:', e);
        // 如果存储满了，清理旧缓存
        if (e.name === 'QuotaExceededError') {
            cleanOldCache();
            try {
                localStorage.setItem(MAPPING_CACHE_KEY, JSON.stringify(cache));
            } catch (e2) {
                console.error('清理后仍无法保存:', e2);
            }
        }
    }
}

/**
 * 清理旧缓存（保留最近10个）
 */
function cleanOldCache() {
    const cache = getAllCache();
    const entries = Object.entries(cache);
    
    if (entries.length <= 10) return;
    
    // 按时间戳排序
    entries.sort((a, b) => (b[1].timestamp || 0) - (a[1].timestamp || 0));
    
    // 只保留前10个
    const newCache = {};
    entries.slice(0, 10).forEach(([key, value]) => {
        newCache[key] = value;
    });
    
    localStorage.setItem(MAPPING_CACHE_KEY, JSON.stringify(newCache));
    console.log('已清理旧映射缓存');
}

/**
 * 保存映射配置到缓存
 */
function saveMappingCache(fileId, mappings, headerRows) {
    const cache = getAllCache();
    
    cache[fileId] = {
        mappings: mappings,
        headerRows: headerRows,
        timestamp: Date.now()
    };
    
    saveAllCache(cache);
    console.log('映射配置已缓存:', fileId);
}

/**
 * 加载映射配置
 */
function loadMappingCache(fileId) {
    const cache = getAllCache();
    const cached = cache[fileId];
    
    if (cached) {
        console.log('加载缓存映射配置:', fileId);
        return {
            mappings: cached.mappings,
            headerRows: cached.headerRows
        };
    }
    
    return null;
}

/**
 * 检查是否有缓存
 */
function hasMappingCache(fileId) {
    const cache = getAllCache();
    return fileId in cache;
}

/**
 * 清除指定文件的缓存
 */
function removeMappingCache(fileId) {
    const cache = getAllCache();
    delete cache[fileId];
    saveAllCache(cache);
    console.log('已清除缓存:', fileId);
}

/**
 * 清除所有缓存
 */
function clearAllMappingCache() {
    localStorage.removeItem(MAPPING_CACHE_KEY);
    console.log('已清除所有映射缓存');
}
