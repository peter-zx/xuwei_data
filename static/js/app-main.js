/**
 * 主应用模块
 * 整合所有组件，管理应用状态
 */

import { StepIndicator } from './components/StepIndicator.js';
import { FileUploader } from './components/FileUploader.js';
import { MappingEditor } from './components/MappingEditor.js';
import { ResultsViewer } from './components/ResultsViewer.js';
import { analyzeData as analyzeDataAPI } from './services/api.js';
import { STEP_CONFIG } from './utils/constants.js';
import { showToast } from './utils/helpers.js';

class Application {
    constructor() {
        this.state = {
            currentStep: STEP_CONFIG.UPLOAD,
            filepath: '',
            sheetInfo: {},
            sheetResults: {}
        };

        this.components = {
            stepIndicator: new StepIndicator(),
            fileUploader: null,
            mappingEditor: new MappingEditor(),
            resultsViewer: new ResultsViewer()
        };

        this.init();
    }

    init() {
        // 初始化文件上传器
        this.components.fileUploader = new FileUploader(
            this.handleUploadSuccess.bind(this)
        );

        console.log('应用已启动');
    }

    /**
     * 处理上传成功
     */
    handleUploadSuccess(result) {
        this.state.filepath = result.filepath;
        this.state.sheetInfo = result.sheet_info;

        // 显示映射设置
        this.components.mappingEditor.render(result.sheet_info);

        // 跳转到第二步
        this.goToStep(STEP_CONFIG.MAPPING);
    }

    /**
     * 分析数据
     */
    async handleAnalyze() {
        const mappingsConfig = this.components.mappingEditor.collectMappings();

        // 跳转到分析步骤
        this.goToStep(STEP_CONFIG.ANALYZING);

        try {
            const result = await analyzeDataAPI(this.state.filepath, mappingsConfig);

            if (result.success) {
                this.state.sheetResults = result.sheet_results;
                showToast('数据分析完成', 'success');

                // 显示结果
                this.components.resultsViewer.render(result.sheet_results);

                // 跳转到结果步骤
                this.goToStep(STEP_CONFIG.RESULT);
            } else {
                showToast(result.error || '分析失败', 'error');
                this.goToStep(STEP_CONFIG.MAPPING);
            }
        } catch (error) {
            console.error('分析错误:', error);
            showToast('分析失败，请重试', 'error');
            this.goToStep(STEP_CONFIG.MAPPING);
        }
    }

    /**
     * 导出数据
     */
    handleExport() {
        this.components.resultsViewer.export();
    }

    /**
     * 重置应用
     */
    handleReset() {
        this.state = {
            currentStep: STEP_CONFIG.UPLOAD,
            filepath: '',
            sheetInfo: {},
            sheetResults: {}
        };

        this.components.fileUploader.reset();
        this.components.mappingEditor.reset();
        this.components.resultsViewer.reset();
        this.components.stepIndicator.reset();

        this.goToStep(STEP_CONFIG.UPLOAD);
    }

    /**
     * 跳转到指定步骤
     */
    goToStep(step) {
        this.state.currentStep = step;
        this.components.stepIndicator.update(step);

        // 切换步骤内容
        document.querySelectorAll('.step-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`step-${step}`).classList.add('active');
    }
}

// 创建全局应用实例
const app = new Application();

// 导出全局函数供HTML调用
window.analyzeData = () => app.handleAnalyze();
window.exportData = () => app.handleExport();
window.resetApp = () => app.handleReset();
window.goToStep = (step) => app.goToStep(step);
window.resetUpload = () => app.components.fileUploader.reset();

export default app;
