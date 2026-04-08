import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import tempfile
import zipfile
import asyncio
from datetime import datetime
import json

from backend.scanner import FileScanner, FileNode, count_files, get_selected_files
from converters.doc2pdf import Doc2PdfConverter, ConversionResult


app = FastAPI(title="文档转PDF工具")

shutdown_event = threading.Event()

BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"

STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ScanRequest(BaseModel):
    folder_path: str


class ConvertRequest(BaseModel):
    file_paths: List[str]
    output_dir: Optional[str] = None
    source_root: Optional[str] = None


class FileTreeResponse(BaseModel):
    success: bool
    tree_html: str = ""
    total_files: int = 0
    total_size: str = ""
    error: str = ""


class ConvertResponse(BaseModel):
    success: bool
    results: List[dict] = []
    total: int = 0
    successful: int = 0
    failed: int = 0


@app.get("/", response_class=HTMLResponse)
async def home():
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        return get_default_html()
    return index_path.read_text(encoding="utf-8")


def get_default_html():
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Doc2PDF Tool</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 16px; margin-bottom: 20px; text-align: center; }
        .header h1 { font-size: 2rem; margin-bottom: 10px; }
        .card { background: white; border-radius: 16px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
        .input-group { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
        .input-group input { flex: 1; padding: 12px 14px; border: 2px solid #e5e7eb; border-radius: 10px; font-size: 0.95rem; }
        .input-group input:focus { border-color: #667eea; outline: none; }
        .btn { padding: 12px 24px; border: none; border-radius: 10px; font-size: 0.95rem; font-weight: 600; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        .btn-success { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
        .btn-success:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(17, 153, 142, 0.4); }
        .btn-secondary { background: #6b7280; color: white; }
        .btn-secondary:hover { background: #5b6270; }
        .drop-zone { width: 100%; min-height: 150px; border: 3px dashed #d1d5db; border-radius: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; background: #fafafa; }
        .drop-zone:hover { border-color: #667eea; background: #f5f5ff; }
        .drop-zone.dragover { border-color: #667eea; background: #f0f0ff; }
        .drop-zone-content { text-align: center; }
        .file-tree { background: #f9fafb; border-radius: 12px; padding: 16px; max-height: 450px; overflow-y: auto; }
        .file-list { list-style: none; }
        .file-list li { padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: background 0.15s; display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
        .file-list li:hover { background: #e5e7eb; }
        .file-list li.folder { font-weight: 600; color: #374151; margin-bottom: 8px; }
        .file-list li input[type="checkbox"] { width: 18px; height: 18px; cursor: pointer; flex-shrink: 0; }
        .file-info { flex: 1; display: flex; justify-content: space-between; align-items: center; min-width: 0; }
        .file-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .file-size { color: #9ca3af; font-size: 0.85rem; margin-left: 12px; flex-shrink: 0; }
        .stats { display: flex; gap: 16px; margin-top: 16px; padding: 16px; background: #f3f4f6; border-radius: 12px; }
        .stat { flex: 1; text-align: center; padding: 12px; background: white; border-radius: 10px; }
        .stat-value { font-size: 1.5rem; font-weight: 700; color: #667eea; }
        .stat-label { font-size: 0.8rem; color: #6b7280; margin-top: 4px; }
        .progress-bar { height: 10px; background: #e5e7eb; border-radius: 5px; overflow: hidden; margin-top: 16px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); transition: width 0.3s; }
        .result-item { padding: 12px 16px; border-radius: 10px; margin-bottom: 10px; display: flex; align-items: center; gap: 12px; }
        .result-success { background: #d1fae5; color: #10b981; }
        .result-failed { background: #fee2e2; color: #ef4444; }
        .result-icon { font-size: 1rem; margin-right: 8px; }
        .result-info { flex: 1; }
        .result-name { font-weight: 500; font-size: 0.9rem; }
        .result-path { font-size: 0.8rem; opacity: 0.7; margin-top: 2px; }
        .hidden { display: none; }
        .log-container { background: #1e1e1e; border-radius: 8px; padding: 16px; max-height: 300px; overflow-y: auto; font-family: 'Consolas', monospace; font-size: 0.85rem; }
        .log-line { padding: 4px 0; border-bottom: 1px solid #333; }
        .log-line:last-child { border-bottom: none; }
        .log-success { color: #4caf50; }
        .log-error { color: #f44336; }
        .log-info { color: #2196f3; }
        .section-title { font-size: 1.1rem; font-weight: 600; color: #374151; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
        .hint { font-size: 0.85rem; color: #9ca3af; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="text-align: left;">
                    <h1>文档转PDF</h1>
                    <p>支持 Word/Excel/PPT/TXT 转换为 PDF</p>
                </div>
                <div style="text-align: right;">
                    <button class="btn btn-secondary" id="langToggle" onclick="toggleLanguage()" style="padding: 8px 16px; font-size: 0.85rem; margin-right: 8px;">EN / 中文</button>
                    <button class="btn btn-secondary" onclick="exitApp()" style="padding: 8px 16px; font-size: 0.85rem;">退出</button>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="section-title">1. 选择源文件夹</div>
            <div id="dropZone" class="drop-zone" onclick="browseFolder()">
                <div class="drop-zone-content">
                    <div style="font-size: 3rem; margin-bottom: 10px;">📁</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #374151;">点击选择文件夹</div>
                    <div style="font-size: 0.9rem; color: #9ca3af; margin-top: 8px;">或拖拽文件夹到此处</div>
                </div>
            </div>
            <input type="text" id="folderPath" class="hidden" value="">
            <div id="fileTree" class="file-tree hidden"></div>
            <div id="stats" class="stats hidden">
                <div class="stat">
                    <div class="stat-value" id="totalFiles">0</div>
                    <div class="stat-label">文件数</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="totalSize">0</div>
                    <div class="stat-label">总大小</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="selectedFiles">0</div>
                    <div class="stat-label">已选择</div>
                </div>
            </div>
            <div class="hint" id="hint">点击上方区域选择文件夹</div>
        </div>
        
        <div class="card">
            <div class="section-title">2. 输出设置</div>
            <div class="input-group">
                <input type="text" id="outputPath" placeholder="默认输出到桌面" value="">
                <button class="btn btn-secondary" onclick="browseOutput()">浏览</button>
                <button class="btn btn-success" id="convertBtn" onclick="startConvert()" disabled>开始转换</button>
            </div>
            <div id="progress" class="hidden">
                <p id="progressText" style="margin-bottom: 8px;">转换中...</p>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressBar" style="width: 0%"></div>
                </div>
            </div>
        </div>
        
        <div class="card hidden" id="resultsCard">
            <div class="section-title">3. 转换结果</div>
            <div id="results"></div>
        </div>
    </div>
    
    <script>
        const i18n = {
            zh: {
                title: '文档转PDF',
                subtitle: '支持 Word/Excel/PPT/TXT 转换为 PDF',
                step1: '1. 选择源文件夹',
                dropText: '点击选择文件夹',
                dropHint: '或拖拽文件夹到此处',
                hint: '点击上方区域选择文件夹',
                files: '文件数',
                totalSize: '总大小',
                selected: '已选择',
                clickSelect: '点击文件复选框选择要转换的文件',
                step2: '2. 输出设置',
                outputPlaceholder: '默认输出到桌面',
                browse: '浏览',
                startConvert: '开始转换',
                converting: '转换中...',
                step3: '3. 转换结果',
                complete: '[完成]',
                success: '成功',
                failed: '失败',
                reason: '原因',
                selectFilesAlert: '请选择要转换的文件',
                scanFailed: '扫描失败',
                convertFailed: '转换失败',
                selectFailed: '选择失败'
            },
            en: {
                title: 'Doc2PDF Tool',
                subtitle: 'Convert Word/Excel/PPT/TXT to PDF',
                step1: '1. Select Source Folder',
                dropText: 'Click to Select Folder',
                dropHint: 'or drag and drop folder here',
                hint: 'Click above to select folder',
                files: 'Files',
                totalSize: 'Total Size',
                selected: 'Selected',
                clickSelect: 'Click checkbox to select files',
                step2: '2. Output Settings',
                outputPlaceholder: 'Default: Output to Desktop',
                browse: 'Browse',
                startConvert: 'Start Convert',
                converting: 'Converting...',
                step3: '3. Conversion Results',
                complete: '[Complete]',
                success: 'Success',
                failed: 'Failed',
                reason: 'Reason',
                selectFilesAlert: 'Please select files to convert',
                scanFailed: 'Scan failed',
                convertFailed: 'Conversion failed',
                selectFailed: 'Selection failed'
            }
        };
        
        let currentLang = 'zh';
        let selectedFiles = new Set();
        let isProcessing = false;
        
        function toggleLanguage() {
            currentLang = currentLang === 'zh' ? 'en' : 'zh';
            applyTranslations();
        }
        
        function t(key) {
            return i18n[currentLang][key] || key;
        }
        
        function applyTranslations() {
            document.querySelector('.header h1').textContent = t('title');
            document.querySelector('.header p').textContent = t('subtitle');
            document.querySelectorAll('.section-title')[0].textContent = t('step1');
            document.querySelector('.drop-zone-content div:nth-child(2)').textContent = t('dropText');
            document.querySelector('.drop-zone-content div:nth-child(3)').textContent = t('dropHint');
            document.getElementById('hint').textContent = t('hint');
            document.querySelectorAll('.stat-label')[0].textContent = t('files');
            document.querySelectorAll('.stat-label')[1].textContent = t('totalSize');
            document.querySelectorAll('.stat-label')[2].textContent = t('selected');
            document.querySelectorAll('.section-title')[1].textContent = t('step2');
            document.getElementById('outputPath').placeholder = t('outputPlaceholder');
            document.querySelectorAll('.btn.btn-secondary')[1].textContent = t('browse');
            document.getElementById('convertBtn').textContent = t('startConvert');
            document.getElementById('progressText').textContent = t('converting');
            document.querySelectorAll('.section-title')[2].textContent = t('step3');
        }
        
        async function browseFolder() {
            if (isProcessing) return;
            isProcessing = true;
            try {
                const response = await fetch('/api/browse-folder');
                const data = await response.json();
                if (data.path) {
                    document.getElementById('folderPath').value = data.path;
                    scanFolder();
                }
            } catch (e) {
                alert(t('selectFailed') + ': ' + e.message);
            } finally {
                setTimeout(() => { isProcessing = false; }, 500);
            }
        }
        
        async function browseOutput() {
            try {
                const response = await fetch('/api/browse-output');
                const data = await response.json();
                if (data.path) {
                    document.getElementById('outputPath').value = data.path;
                }
            } catch (e) {
                alert(t('selectFailed') + ': ' + e.message);
            }
        }
        
        async function scanFolder() {
            const folderPath = document.getElementById('folderPath').value.trim();
            if (!folderPath) { alert(t('selectFailed')); return; }
            
            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({folder_path: folderPath})
                });
                const data = await response.json();
                
                if (!data.success) {
                    alert(t('scanFailed') + ': ' + data.error);
                    return;
                }
                
                document.getElementById('fileTree').innerHTML = '<ul class="file-list">' + data.tree_html + '</ul>';
                document.getElementById('fileTree').classList.remove('hidden');
                document.getElementById('stats').classList.remove('hidden');
                document.getElementById('totalFiles').textContent = data.total_files;
                document.getElementById('totalSize').textContent = data.total_size;
                document.getElementById('hint').textContent = t('clickSelect');
                document.getElementById('convertBtn').disabled = false;
                
                initCheckboxes();
            } catch (e) {
                alert(t('scanFailed') + ': ' + e.message);
            }
        }
        
        function initCheckboxes() {
            document.addEventListener('change', function(e) {
                if (e.target.classList.contains('folder-checkbox')) {
                    const folderPath = e.target.dataset.folders;
                    const isChecked = e.target.checked;
                    
                    document.querySelectorAll('.file-checkbox').forEach(cb => {
                        const filePath = cb.dataset.folders;
                        if (filePath === folderPath || filePath.startsWith(folderPath + '|')) {
                            cb.checked = isChecked;
                        }
                    });
                }
                updateSelection();
            });
        }
        
        function updateSelection() {
            selectedFiles.clear();
            document.querySelectorAll('.file-checkbox:checked').forEach(cb => {
                if (cb.dataset.path) {
                    selectedFiles.add(cb.dataset.path);
                }
            });
            document.getElementById('selectedFiles').textContent = selectedFiles.size;
        }
        
        async function startConvert() {
            if (selectedFiles.size === 0) {
                alert(t('selectFilesAlert'));
                return;
            }
            
            const outputPath = document.getElementById('outputPath').value.trim();
            const convertBtn = document.getElementById('convertBtn');
            const progress = document.getElementById('progress');
            
            convertBtn.disabled = true;
            progress.classList.remove('hidden');
            
            try {
                const response = await fetch('/api/convert', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        file_paths: Array.from(selectedFiles),
                        output_dir: outputPath || null,
                        source_root: document.getElementById('folderPath').value
                    })
                });
                
                const data = await response.json();
                showResults(data);
            } catch (e) {
                alert(t('convertFailed') + ': ' + e.message);
            } finally {
                convertBtn.disabled = false;
            }
        }
        
        function showResults(data) {
            const resultsCard = document.getElementById('resultsCard');
            const resultsDiv = document.getElementById('results');
            
            resultsCard.classList.remove('hidden');
            
            let html = '<div class="log-container">';
            
            const successCount = data.successful;
            const failedCount = data.failed;
            
            html += '<div class="log-line ' + (failedCount === 0 ? 'log-success' : 'log-error') + '" style="font-size:1.1rem; font-weight:600; padding:12px; text-align:center;">' + t('complete') + ' ' + t('success') + ': ' + successCount + ', ' + t('failed') + ': ' + failedCount + '</div>';
            
            const successByFolder = {};
            data.results.forEach(r => {
                if (r.success) {
                    const parts = r.original_path.split(/[/\\\\]/);
                    const last3 = parts.slice(-4, -1);
                    const folderName = last3.length >= 3 ? last3.join('/') : parts.slice(0, -1).join('/');
                    successByFolder[folderName] = (successByFolder[folderName] || 0) + 1;
                }
            });
            
            for (const folder in successByFolder) {
                html += '<div class="log-line log-success">' + folder + ': ' + successByFolder[folder] + ' ' + (currentLang === 'zh' ? '个' : 'files') + '</div>';
            }
            
            data.results.forEach((r, i) => {
                if (!r.success) {
                    html += '<div class="log-line log-error">[' + t('failed') + '] ' + r.original_path + '</div>';
                    html += '<div class="log-line log-error" style="padding-left:20px;">' + t('reason') + ': ' + r.error + '</div>';
                }
            });
            
            html += '</div>';
            
            resultsDiv.innerHTML = html;
        }
        
        async function exitApp() {
            if (!confirm(currentLang === 'zh' ? '确定要退出吗？' : 'Are you sure you want to exit?')) return;
            try {
                await fetch('/api/shutdown', {method: 'POST'});
            } catch (e) {}
            setTimeout(() => { window.close(); }, 500);
        }
    </script>
</body>
</html>"""


@app.get("/api/browse-folder")
async def browse_folder():
    import tkinter as tk
    from tkinter import filedialog
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    folder_path = filedialog.askdirectory(title="Select Folder")
    root.destroy()
    
    if folder_path:
        return {"path": folder_path}
    return {"path": ""}


@app.get("/api/browse-output")
async def browse_output():
    import tkinter as tk
    from tkinter import filedialog
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    folder_path = filedialog.askdirectory(title="Select Output Folder")
    root.destroy()
    
    if folder_path:
        return {"path": folder_path}
    return {"path": ""}


@app.post("/api/scan")
async def scan_folder(request: ScanRequest) -> FileTreeResponse:
    try:
        scanner = FileScanner(request.folder_path)
        tree = scanner.scan()
        
        if not tree:
            return FileTreeResponse(success=False, error="文件夹不存在或无法访问")
        
        tree_html = scanner.get_file_tree_html(tree)
        total = count_files(tree)
        total_size = _format_size(tree.size)
        
        return FileTreeResponse(
            success=True,
            tree_html=tree_html,
            total_files=total,
            total_size=total_size
        )
    except Exception as e:
        return FileTreeResponse(success=False, error=str(e))


@app.post("/api/convert")
async def convert_files(request: ConvertRequest) -> ConvertResponse:
    try:
        output_dir = request.output_dir or str(Path.home() / "Desktop" / ("Output_" + datetime.now().strftime("%m%d_%H%M%S")))
        source_root = request.source_root or None
        converter = Doc2PdfConverter(output_dir, source_root=source_root)
        
        results = converter.convert_batch(request.file_paths)
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return ConvertResponse(
            success=True,
            results=[{
                "success": r.success,
                "original_path": r.original_path,
                "output_path": r.output_path,
                "error": r.error
            } for r in results],
            total=len(results),
            successful=successful,
            failed=failed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shutdown")
async def shutdown():
    import os
    def shutdown_server():
        import time
        time.sleep(0.3)
        os._exit(0)
    threading.Thread(target=shutdown_server, daemon=True).start()
    return {"message": "shutting down"}
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )


def _format_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


if __name__ == "__main__":
    import threading
    import time
    import sys
    import webbrowser
    import os
    
    import uvicorn
    import logging
    import logging.config
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": "%(asctime)s - %(message)s"}},
        "handlers": {"default": {"formatter": "default", "class": "logging.StreamHandler", "stream": "ext://sys.stdout"}},
        "root": {"level": "INFO", "handlers": ["default"]},
    }
    logging.config.dictConfig(logging_config)
    
    import tkinter as tk
    from tkinter import ttk
    
    splash = tk.Tk()
    splash.title("Doc2PDF")
    splash.geometry("320x140")
    splash.resizable(False, False)
    splash.attributes("-topmost", True)
    
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    splash.geometry(f"320x140+{(screen_w-320)//2}+{(screen_h-140)//2}")
    
    tk.Label(splash, text="📄 Doc2PDF", font=("微软雅黑", 16, "bold")).pack(pady=15)
    tk.Label(splash, text="正在启动服务...", font=("微软雅黑", 10)).pack()
    progress = ttk.Progressbar(splash, mode="indeterminate", length=240)
    progress.pack(pady=15)
    progress.start(8)
    
    splash.update()
    
    server_config = uvicorn.Config(app, host="0.0.0.0", port=8503, log_config=logging_config)
    server = uvicorn.Server(server_config)
    
    def run_server():
        server.run()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    time.sleep(1.5)
    webbrowser.open('http://localhost:8503')
    
    def check_server():
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8503))
        sock.close()
        if result == 0:
            progress.stop()
            tk.Label(splash, text="✅ 服务已就绪", font=("微软雅黑", 9), fg="green").pack()
            splash.update()
            time.sleep(1)
            splash.destroy()
        else:
            splash.after(500, check_server)
    
    splash.after(500, check_server)
    
    def on_close():
        import ctypes
        kernel32 = ctypes.windll.kernel32
        pid = kernel32.GetCurrentProcessId()
        
        import subprocess
        subprocess.run(f'taskkill /PID {pid} /F', shell=True, capture_output=True)
    
    splash.protocol("WM_DELETE_WINDOW", on_close)
    splash.mainloop()
