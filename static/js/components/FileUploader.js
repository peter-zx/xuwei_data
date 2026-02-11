/**
 * 文件上传组件
 */

import { showToast, validateFile, formatFileSize } from '../utils/helpers.js';
import { uploadFile } from '../services/api.js';

export class FileUploader {
    constructor(onUploadSuccess) {
        this.onUploadSuccess = onUploadSuccess;
        this.init();
    }

    init() {
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');

        if (!uploadZone || !fileInput) return;

        // 拖拽事件
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleUpload(files[0]);
            }
        });

        // 文件选择事件
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleUpload(e.target.files[0]);
            }
        });
    }

    async handleUpload(file) {
        // 验证文件
        const validation = validateFile(file);
        if (!validation.valid) {
            showToast(validation.message, 'error');
            return;
        }

        try {
            // 显示文件预览
            this.showFilePreview(file);

            // 上传文件
            const result = await uploadFile(file);

            if (result.success) {
                showToast('文件上传成功', 'success');
                this.onUploadSuccess(result);
            } else {
                showToast(result.error || '上传失败', 'error');
                this.hideFilePreview();
            }
        } catch (error) {
            console.error('上传错误:', error);
            showToast('上传失败，请重试', 'error');
            this.hideFilePreview();
        }
    }

    showFilePreview(file) {
        const preview = document.getElementById('filePreview');
        const fileName = document.getElementById('fileName');
        const fileSheets = document.getElementById('fileSheets');

        if (!preview || !fileName || !fileSheets) return;

        fileName.textContent = file.name;
        fileSheets.textContent = `文件大小: ${formatFileSize(file.size)}`;

        preview.style.display = 'block';
    }

    hideFilePreview() {
        const preview = document.getElementById('filePreview');
        if (preview) {
            preview.style.display = 'none';
        }
    }

    reset() {
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.value = '';
        }
        this.hideFilePreview();
    }
}
