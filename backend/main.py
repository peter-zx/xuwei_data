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
        .result-icon { font-size: 1.2rem; }
        .result-info { flex: 1; }
        .result-name { font-weight: 600; }
        .result-path { font-size: 0.85rem; opacity: 0.8; margin-top: 2px; }
        .hidden { display: none; }
        .section-title { font-size: 1.1rem; font-weight: 600; color: #374151; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
        .hint { font-size: 0.85rem; color: #9ca3af; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Doc2PDF</h1>
            <p>Word/Excel/PPT/TXT to PDF Converter</p>
        </div>
        
        <div class="card">
            <div class="section-title">1. Select Source Folder</div>
            <div id="dropZone" class="drop-zone" onclick="browseFolder()">
                <div class="drop-zone-content">
                    <div style="font-size: 3rem; margin-bottom: 10px;">📁</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #374151;">Click to Select Folder</div>
                    <div style="font-size: 0.9rem; color: #9ca3af; margin-top: 8px;">or drag and drop a folder here</div>
                </div>
            </div>
            <input type="text" id="folderPath" class="hidden" value="">
            <div id="fileTree" class="file-tree hidden"></div>
            <div id="stats" class="stats hidden">
                <div class="stat">
                    <div class="stat-value" id="totalFiles">0</div>
                    <div class="stat-label">Files</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="totalSize">0</div>
                    <div class="stat-label">Total Size</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="selectedFiles">0</div>
                    <div class="stat-label">Selected</div>
                </div>
            </div>
            <div class="hint" id="hint">Click the box above to select a folder</div>
        </div>
        
        <div class="card">
            <div class="section-title">2. Output Settings</div>
            <div class="input-group">
                <input type="text" id="outputPath" placeholder="Default: Desktop" value="">
                <button class="btn btn-secondary" onclick="browseOutput()">Browse</button>
                <button class="btn btn-success" id="convertBtn" onclick="startConvert()" disabled>Convert</button>
            </div>
            <div id="progress" class="hidden">
                <p id="progressText" style="margin-bottom: 8px;">Converting...</p>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressBar" style="width: 0%"></div>
                </div>
            </div>
        </div>
        
        <div class="card hidden" id="resultsCard">
            <div class="section-title">3. Results</div>
            <div id="results"></div>
        </div>
    </div>
    
    <script>
        let selectedFiles = new Set();
        
        async function browseFolder() {
            try {
                const response = await fetch('/api/browse-folder');
                const data = await response.json();
                if (data.path) {
                    document.getElementById('folderPath').value = data.path;
                    scanFolder();
                }
            } catch (e) {
                alert('Browse failed: ' + e.message);
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
                alert('Browse failed: ' + e.message);
            }
        }
        
        async function scanFolder() {
            const folderPath = document.getElementById('folderPath').value.trim();
            if (!folderPath) { alert('Please enter folder path'); return; }
            
            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({folder_path: folderPath})
                });
                const data = await response.json();
                
                if (!data.success) {
                    alert('Scan failed: ' + data.error);
                    return;
                }
                
                document.getElementById('fileTree').innerHTML = '<ul class="file-list">' + data.tree_html + '</ul>';
                document.getElementById('fileTree').classList.remove('hidden');
                document.getElementById('stats').classList.remove('hidden');
                document.getElementById('totalFiles').textContent = data.total_files;
                document.getElementById('totalSize').textContent = data.total_size;
                document.getElementById('hint').textContent = 'Click files to select/deselect for conversion';
                document.getElementById('convertBtn').disabled = false;
                
                initCheckboxes();
            } catch (e) {
                alert('Scan failed: ' + e.message);
            }
        }
        
        function initCheckboxes() {
            document.querySelectorAll('.file-row input[type="checkbox"]').forEach(checkbox => {
                checkbox.addEventListener('change', updateSelection);
            });
            
            document.querySelectorAll('.folder-header input[type="checkbox"]').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    toggleFolder(this);
                });
            });
        }
        
        function toggleFolder(checkbox) {
            const files = checkbox.dataset.files;
            console.log('toggleFolder called, files:', files);
            if (!files) {
                console.log('No files in dataset');
                return;
            }
            
            const fileList = files.split('|');
            console.log('File list:', fileList);
            const isChecked = checkbox.checked;
            
            let checkedCount = 0;
            fileList.forEach(path => {
                const cb = document.querySelector(`.file-checkbox[data-path="${path}"]`);
                if (cb) {
                    cb.checked = isChecked;
                    checkedCount++;
                }
            });
            console.log('Checked:', checkedCount, 'files');
            
            updateSelection();
        }
        
        function updateSelection() {
            selectedFiles.clear();
            document.querySelectorAll('input.file-checkbox[type="checkbox"]:checked').forEach(cb => {
                if (cb.dataset.path) {
                    selectedFiles.add(cb.dataset.path);
                }
            });
            document.getElementById('selectedFiles').textContent = selectedFiles.size;
        }
        
        async function startConvert() {
            if (selectedFiles.size === 0) {
                alert('Please select files to convert');
                return;
            }
            if (selectedFiles.size === 0) {
                alert('Please select files to convert');
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
                alert('Convert failed: ' + e.message);
            } finally {
                convertBtn.disabled = false;
            }
        }
        
        function showResults(data) {
            const resultsCard = document.getElementById('resultsCard');
            const resultsDiv = document.getElementById('results');
            
            resultsCard.classList.remove('hidden');
            
            let html = '';
            data.results.forEach(r => {
                const cls = r.success ? 'result-success' : 'result-failed';
                const icon = r.success ? '&#10004;' : '&#10008;';
                const name = r.original_path.split(/[/\\\\]/).pop();
                html += '<div class="result-item ' + cls + '">';
                html += '<span class="result-icon">' + icon + '</span>';
                html += '<div class="result-info">';
                html += '<div class="result-name">' + name + '</div>';
                html += '<div class="result-path">' + (r.success ? r.output_path : r.error) + '</div>';
                html += '</div></div>';
            });
            
            html = '<p style="margin-bottom: 12px; font-weight: 600;">Success: ' + data.successful + '/' + data.total + ' files</p>' + html;
            resultsDiv.innerHTML = html;
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
        output_dir = request.output_dir or str(Path.home() / "Desktop" / "Doc2PDF_Output" / datetime.now().strftime("%Y%m%d_%H%M%S"))
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


@app.get("/api/download/{filename}")
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)
