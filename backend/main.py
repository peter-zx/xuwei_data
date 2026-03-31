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
    <title>文档转PDF工具</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 16px; margin-bottom: 20px; text-align: center; }
        .header h1 { font-size: 2rem; margin-bottom: 10px; }
        .card { background: white; border-radius: 16px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
        .input-group { display: flex; gap: 12px; margin-bottom: 20px; }
        .input-group input { flex: 1; padding: 14px 16px; border: 2px solid #e5e7eb; border-radius: 12px; font-size: 1rem; }
        .btn { padding: 14px 28px; border: none; border-radius: 12px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        .btn-success { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
        .file-tree { background: #f9fafb; border-radius: 12px; padding: 16px; max-height: 400px; overflow-y: auto; }
        .file-item { display: flex; align-items: center; padding: 8px 12px; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
        .file-item:hover { background: #e5e7eb; }
        .file-item input[type="checkbox"] { width: 18px; height: 18px; margin-right: 12px; cursor: pointer; }
        .file-icon { margin-right: 8px; }
        .file-name { flex: 1; }
        .file-size { color: #9ca3af; font-size: 0.85rem; }
        .folder { font-weight: 600; color: #374151; }
        .stats { display: flex; gap: 20px; margin-top: 16px; padding: 16px; background: #f3f4f6; border-radius: 12px; }
        .stat { text-align: center; }
        .stat-value { font-size: 1.5rem; font-weight: 700; color: #667eea; }
        .stat-label { font-size: 0.85rem; color: #6b7280; }
        .progress-bar { height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin-top: 16px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); transition: width 0.3s; }
        .result-item { padding: 12px; border-radius: 8px; margin-bottom: 8px; }
        .result-success { background: #d1fae5; color: #10b981; }
        .result-failed { background: #fee2e2; color: #ef4444; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 文档转PDF工具</h1>
            <p>支持 Word、Excel、PPT、TXT 转 PDF</p>
        </div>
        
        <div class="card">
            <h3 style="margin-bottom: 16px;">📁 选择文件夹</h3>
            <div class="input-group">
                <input type="text" id="folderPath" placeholder="请输入文件夹路径,例如: C:\\Users\\Documents" value="">
                <button class="btn btn-primary" onclick="scanFolder()">🔍 扫描</button>
            </div>
            
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
        </div>
        
        <div class="card">
            <h3 style="margin-bottom: 16px;">⚙️ 转换设置</h3>
            <div class="input-group">
                <input type="text" id="outputPath" placeholder="输出目录 (留空则使用默认)" value="">
                <button class="btn btn-success" id="convertBtn" onclick="startConvert()" disabled>📥 开始转换</button>
            </div>
            
            <div id="progress" class="hidden">
                <p id="progressText">准备中...</p>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressBar" style="width: 0%"></div>
                </div>
            </div>
        </div>
        
        <div class="card hidden" id="resultsCard">
            <h3 style="margin-bottom: 16px;">📊 转换结果</h3>
            <div id="results"></div>
        </div>
    </div>
    
    <script>
        let selectedFiles = new Set();
        let allFiles = [];
        
        async function scanFolder() {
            const folderPath = document.getElementById('folderPath').value.trim();
            if (!folderPath) { alert('请输入文件夹路径'); return; }
            
            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({folder_path: folderPath})
                });
                const data = await response.json();
                
                if (!data.success) {
                    alert('扫描失败: ' + data.error);
                    return;
                }
                
                document.getElementById('fileTree').innerHTML = data.tree_html;
                document.getElementById('fileTree').classList.remove('hidden');
                document.getElementById('stats').classList.remove('hidden');
                document.getElementById('totalFiles').textContent = data.total_files;
                document.getElementById('totalSize').textContent = data.total_size;
                document.getElementById('convertBtn').disabled = false;
                
                initTreeInteraction();
            } catch (e) {
                alert('扫描失败: ' + e.message);
            }
        }
        
        function initTreeInteraction() {
            document.querySelectorAll('.file-item').forEach(item => {
                item.addEventListener('click', function(e) {
                    if (e.target.type === 'checkbox') return;
                    const checkbox = this.querySelector('input[type="checkbox"]');
                    checkbox.checked = !checkbox.checked;
                    updateSelection();
                });
            });
        }
        
        function updateSelection() {
            selectedFiles.clear();
            document.querySelectorAll('.file-item input[type="checkbox"]:checked').forEach(cb => {
                const path = cb.closest('.file-item').dataset.path;
                selectedFiles.add(path);
            });
            document.getElementById('selectedFiles').textContent = selectedFiles.size;
        }
        
        async function startConvert() {
            if (selectedFiles.size === 0) {
                alert('请选择要转换的文件');
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
                        output_dir: outputPath || null
                    })
                });
                
                const data = await response.json();
                showResults(data);
            } catch (e) {
                alert('转换失败: ' + e.message);
            } finally {
                convertBtn.disabled = false;
            }
        }
        
        function showResults(data) {
            const resultsCard = document.getElementById('resultsCard');
            const resultsDiv = document.getElementById('results');
            
            resultsCard.classList.remove('hidden');
            
            let html = `<p style="margin-bottom: 16px;">成功: ${data.successful}/${data.total}个文件</p>`;
            
            data.results.forEach(r => {
                const cls = r.success ? 'result-success' : 'result-failed';
                const status = r.success ? '✓' : '✗';
                const msg = r.success ? r.output_path : r.error;
                html += `<div class="result-item ${cls}">${status} ${r.original_path}<br><small>${msg}</small></div>`;
            });
            
            resultsDiv.innerHTML = html;
        }
    </script>
</body>
</html>"""


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
        output_dir = request.output_dir or str(OUTPUT_DIR / datetime.now().strftime("%Y%m%d_%H%M%S"))
        converter = Doc2PdfConverter(output_dir)
        
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
