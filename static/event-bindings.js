// 按钮和事件绑定配置
// 集中管理所有DOM元素绑定关系，避免修改时导致错误

const DOM_BINDINGS = {
    // 文件上传相关
    uploadArea: {
        selector: '#uploadArea',
        events: ['click', 'dragover', 'dragleave', 'drop'],
        handlers: {
            click: function() {
                document.getElementById('fileInput').click();
            },
            dragover: function(e) {
                e.preventDefault();
                this.classList.add('dragover');
            },
            dragleave: function() {
                this.classList.remove('dragover');
            },
            drop: function(e) {
                e.preventDefault();
                this.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0 && typeof handleFile === 'function') {
                    handleFile(files[0]);
                }
            }
        }
    },
    fileInput: {
        selector: '#fileInput',
        events: ['change'],
        handlers: {
            change: function(e) {
                if (e.target.files.length > 0 && typeof handleFile === 'function') {
                    handleFile(e.target.files[0]);
                }
            }
        }
    },

    // 按钮绑定
    reuploadBtn: {
        selector: '#reuploadBtn',
        events: ['click'],
        handlers: {
            click: () => {
                resetAll();
                updateStep(1);
            }
        }
    },
    toPreviewBtn: {
        selector: '#toPreviewBtn',
        events: ['click'],
        handlers: {
            click: async () => {
                await loadSheetPreviews();
                renderPreviewInterface();
                updateStep(2);
            }
        }
    },
    backToUploadBtn: {
        selector: '#backToUploadBtn',
        events: ['click'],
        handlers: {
            click: () => updateStep(1)
        }
    },
    toMappingBtn: {
        selector: '#toMappingBtn',
        events: ['click'],
        handlers: {
            click: async () => {
                await loadSheetColumns();
                renderMappingInterface();
                updateStep(3);
            }
        }
    },
    backToPreviewBtn: {
        selector: '#backToPreviewBtn',
        events: ['click'],
        handlers: {
            click: () => updateStep(2)
        }
    },
    toAnalyzeBtn: {
        selector: '#toAnalyzeBtn',
        events: ['click'],
        handlers: {
            click: async () => {
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
                        
                        // 保存映射配置到缓存
                        if (fileId) {
                            saveMappingCache(fileId, mappings, headerRows);
                        }
                        
                        renderMappedDataView();
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
            }
        }
    },
    backToMappingBtn: {
        selector: '#backToMappingBtn',
        events: ['click'],
        handlers: {
            click: () => updateStep(3)
        }
    },
    toComparisonBtn: {
        selector: '#toComparisonBtn',
        events: ['click'],
        handlers: {
            click: async () => {
                await performDataComparison();
                updateStep(5);
            }
        }
    },
    backToDataViewBtn: {
        selector: '#backToDataViewBtn',
        events: ['click'],
        handlers: {
            click: () => updateStep(4)
        }
    },
    toResultsBtn: {
        selector: '#toResultsBtn',
        events: ['click'],
        handlers: {
            click: () => {
                renderFinalResults();
                updateStep(6);
            }
        }
    },
    backToComparisonBtn: {
        selector: '#backToComparisonBtn',
        events: ['click'],
        handlers: {
            click: () => updateStep(5)
        }
    },
    resetBtn: {
        selector: '#resetBtn',
        events: ['click'],
        handlers: {
            click: () => {
                resetAll();
                updateStep(1);
            }
        }
    },
    exportBtn: {
        selector: '#exportBtn',
        events: ['click'],
        handlers: {
            click: () => {
                // 延迟调用，确保函数已定义
                setTimeout(() => {
                    if (typeof exportComparisonData === 'function') {
                        exportComparisonData();
                    } else {
                        console.error('exportComparisonData 函数未定义');
                    }
                }, 0);
            }
        }
    }
};

// 初始化所有事件绑定
function initializeEventBindings() {
    // 延迟初始化，确保script.js中的函数已加载
    setTimeout(() => {
        for (const [key, binding] of Object.entries(DOM_BINDINGS)) {
            const element = document.querySelector(binding.selector);
            if (!element) {
                console.warn(`元素不存在: ${binding.selector} (${key})`);
                continue;
            }

            // 将元素保存到全局变量
            window[key] = element;

            // 绑定事件
            binding.events.forEach(event => {
                const handler = binding.handlers[event];
                if (handler) {
                    // 使用bind确保this指向正确
                    element.addEventListener(event, handler);
                }
            });
        }
        console.log('✓ 事件绑定初始化完成');
    }, 500);
}

// DOM加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEventBindings);
} else {
    initializeEventBindings();
}
