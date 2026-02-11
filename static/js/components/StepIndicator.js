/**
 * 步骤指示器组件
 */

import { STEP_CONFIG } from '../utils/constants.js';

export class StepIndicator {
    constructor() {
        this.steps = document.querySelectorAll('.step-item');
        this.currentStep = STEP_CONFIG.UPLOAD;
    }

    /**
     * 更新步骤指示器
     * @param {number} step - 当前步骤
     */
    update(step) {
        this.currentStep = step;

        this.steps.forEach((item, index) => {
            const stepNum = index + 1;
            item.classList.remove('active', 'completed');

            if (stepNum < step) {
                item.classList.add('completed');
            } else if (stepNum === step) {
                item.classList.add('active');
            }
        });
    }

    /**
     * 重置到第一步
     */
    reset() {
        this.update(STEP_CONFIG.UPLOAD);
    }
}
