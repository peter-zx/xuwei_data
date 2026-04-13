import sys
import time
import socket
import threading
import webbrowser
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.settings import get_settings, PROJECT_ROOT
from app.core import get_logger, register_exception_handlers
from app.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = get_logger("startup")
    logger.info(f"正在启动 {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"运行环境: {settings.ENV}")
    logger.info(f"上传目录: {settings.paths.UPLOAD_DIR}")
    logger.info(f"输出目录: {Path.home() / 'Desktop' / 'Output_时间戳'}")
    
    yield
    
    logger = get_logger("startup")
    logger.info("正在关闭...")


settings = get_settings()
logger = get_logger("startup")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="文档转PDF转换工具",
    lifespan=lifespan
)

register_exception_handlers(app)

app.include_router(router, prefix="/api")

static_dir = PROJECT_ROOT / "app" / "static"
templates_dir = PROJECT_ROOT / "app" / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def home():
    index_path = templates_dir / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return get_default_html()


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
        .section-title { font-size: 1.1rem; font-weight: 600; color: #374151; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
        .drop-zone { width: 100%; min-height: 120px; border: 3px dashed #d1d5db; border-radius: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; background: #fafafa; margin-bottom: 16px; }
        .drop-zone:hover { border-color: #667eea; background: #f5f5ff; }
        .drop-zone.dragover { border-color: #667eea; background: #f0f0ff; }
        .drop-zone-content { text-align: center; }
        .btn { padding: 12px 24px; border: none; border-radius: 10px; font-size: 0.95rem; font-weight: 600; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        .btn-success { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
        .btn-success:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(17, 153, 142, 0.4); }
        .btn-secondary { background: #6b7280; color: white; }
        .btn-secondary:hover { background: #5b6270; }
        .input-group { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
        .input-group input { flex: 1; padding: 12px 14px; border: 2px solid #e5e7eb; border-radius: 10px; font-size: 0.95rem; }
        .input-group input:focus { border-color: #667eea; outline: none; }
        .file-tree { background: #f9fafb; border-radius: 12px; padding: 16px; max-height: 400px; overflow-y: auto; }
        .file-list { list-style: none; }
        .file-list li { padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: background 0.15s; display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
        .file-list li:hover { background: #e5e7eb; }
        .file-list li.folder { font-weight: 600; color: #374151; margin-bottom: 8px; }
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
        .hidden { display: none; }
        .hint { font-size: 0.85rem; color: #9ca3af; margin-top: 8px; }
        .log-container { background: #1e1e1e; border-radius: 8px; padding: 16px; max-height: 300px; overflow-y: auto; font-family: 'Consolas', monospace; font-size: 0.85rem; color: #fff; }
        .log-line { padding: 4px 0; border-bottom: 1px solid #333; }
        .log-line:last-child { border-bottom: none; }
        .log-success { color: #4caf50; }
        .log-error { color: #f44336; }
        .log-info { color: #2196f3; }
        .tab-bar { display: flex; gap: 8px; margin-bottom: 16px; }
        .tab-btn { padding: 10px 20px; border: none; border-radius: 8px; background: #e5e7eb; color: #6b7280; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .tab-btn.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
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
                <button class="btn btn-secondary" onclick="exitApp()">退出</button>
            </div>
        </div>
        
        <div class="card">
            <div class="section-title">1. 选择源文件夹</div>
            <div class="tab-bar">
                <button class="tab-btn active" id="tabFolder" onclick="switchTab('folder')">📁 文件夹</button>
                <button class="tab-btn" id="tabUpload" onclick="switchTab('upload')">📤 上传文件</button>
            </div>
            
            <div id="folderTab">
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
            
            <div id="uploadTab" class="hidden">
                <div id="uploadZone" class="drop-zone" onclick="document.getElementById('fileInput').click()">
                    <div class="drop-zone-content">
                        <div style="font-size: 3rem; margin-bottom: 10px;">📤</div>
                        <div style="font-size: 1.1rem; font-weight: 600; color: #374151;">拖拽文件到此处或点击上传</div>
                        <div style="font-size: 0.9rem; color: #9ca3af; margin-top: 8px;">支持格式: DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, PDF</div>
                    </div>
                    <input type="file" id="fileInput" multiple accept=".doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.pdf" style="display: none;">
                </div>
                <div id="uploadFileList" class="file-list hidden" style="max-height: 250px; overflow-y: auto;"></div>
            </div>
        </div>
        
        <div class="card">
            <div class="section-title">2. 输出设置</div>
            <div class="input-group">
                <input type="text" id="outputPath" placeholder="默认输出到桌面 Output_时间戳 文件夹" value="">
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
        let currentTab = 'folder';
        let selectedFiles = new Set();
        let uploadedFiles = [];
        let scannedFiles = [];
        let isProcessing = false;
        
        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('tabFolder').classList.toggle('active', tab === 'folder');
            document.getElementById('tabUpload').classList.toggle('active', tab === 'upload');
            document.getElementById('folderTab').classList.toggle('hidden', tab !== 'folder');
            document.getElementById('uploadTab').classList.toggle('hidden', tab !== 'upload');
        }
        
        async function browseFolder() {
            if (isProcessing) return;
            try {
                const response = await fetch('/api/browse-folder');
                const data = await response.json();
                if (data.path) {
                    document.getElementById('folderPath').value = data.path;
                    scanFolder();
                }
            } catch (e) {
                alert('选择失败: ' + e.message);
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
                alert('选择失败: ' + e.message);
            }
        }
        
        async function scanFolder() {
            const folderPath = document.getElementById('folderPath').value.trim();
            if (!folderPath) return;
            
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
                
                scannedFiles = [];
                selectedFiles.clear();
                
                document.getElementById('fileTree').innerHTML = data.tree_html;
                document.getElementById('fileTree').classList.remove('hidden');
                document.getElementById('stats').classList.remove('hidden');
                document.getElementById('totalFiles').textContent = data.total_files;
                document.getElementById('totalSize').textContent = data.total_size;
                document.getElementById('hint').textContent = '点击文件复选框选择要转换的文件';
                document.getElementById('convertBtn').disabled = true;
                
                initTreeCheckboxes();
            } catch (e) {
                alert('扫描失败: ' + e.message);
            }
        }
        
        function initTreeCheckboxes() {
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
                    updateSelection();
                }
                if (e.target.classList.contains('file-checkbox')) {
                    updateSelection();
                }
            });
        }
        
        function updateSelection() {
            selectedFiles.clear();
            document.querySelectorAll('.file-checkbox:checked').forEach(cb => {
                if (cb.dataset.path) {
                    selectedFiles.add(cb.dataset.path);
                    scannedFiles.push({ path: cb.dataset.path, name: cb.closest('.file-row').querySelector('.file-name')?.textContent || '' });
                }
            });
            document.getElementById('selectedFiles').textContent = selectedFiles.size;
            document.getElementById('convertBtn').disabled = selectedFiles.size === 0;
        }
        
        const uploadDropZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        
        uploadDropZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadDropZone.classList.add('dragover'); });
        uploadDropZone.addEventListener('dragleave', () => uploadDropZone.classList.remove('dragover'));
        uploadDropZone.addEventListener('drop', (e) => { e.preventDefault(); uploadDropZone.classList.remove('dragover'); handleFiles(e.dataTransfer.files); });
        fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
        
        async function handleFiles(files) {
            const formData = new FormData();
            for (let file of files) {
                formData.append('files', file);
            }
            
            try {
                const response = await fetch('/api/upload/batch', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.results) {
                    uploadedFiles = uploadedFiles.concat(data.results.filter(r => r.success).map(r => ({
                        id: r.file_id,
                        name: r.filename,
                        size: r.file_size
                    })));
                    updateUploadFileList();
                }
            } catch (e) {
                console.error('上传失败:', e);
            }
        }
        
        function updateUploadFileList() {
            const list = document.getElementById('uploadFileList');
            
            if (uploadedFiles.length === 0) {
                list.classList.add('hidden');
                return;
            }
            
            list.classList.remove('hidden');
            list.innerHTML = uploadedFiles.map((f, i) => `
                <li style="background: #f9fafb;">
                    <input type="checkbox" onchange="toggleUploadFile('${f.id}', this.checked)" style="width:18px; height:18px;">
                    <span class="file-name">${f.name}</span>
                    <span class="file-size">${formatSize(f.size)}</span>
                </li>
            `).join('');
        }
        
        function toggleUploadFile(id, checked) {
            if (checked) {
                selectedFiles.add('upload:' + id);
            } else {
                selectedFiles.delete('upload:' + id);
            }
            document.getElementById('convertBtn').disabled = selectedFiles.size === 0;
        }
        
        function formatSize(bytes) {
            for (let unit of ['B', 'KB', 'MB', 'GB']) {
                if (bytes < 1024) return bytes.toFixed(1) + ' ' + unit;
                bytes /= 1024;
            }
            return bytes.toFixed(1) + ' TB';
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
            
            const fileIds = [];
            const filePaths = [];
            
            selectedFiles.forEach(key => {
                if (key.startsWith('upload:')) {
                    fileIds.push(key.substring(7));
                } else {
                    filePaths.push(key);
                }
            });
            
            try {
                const folderPath = document.getElementById('folderPath').value;
                const outputPath = document.getElementById('outputPath').value.trim();
                const progress = document.getElementById('progress');
                const progressBar = document.getElementById('progressBar');
                
                progress.classList.remove('hidden');
                progressBar.style.width = '50%';
                
                const response = await fetch('/api/convert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file_ids: fileIds,
                        file_paths: filePaths,
                        preserve_structure: true,
                        source_root: folderPath || null,
                        output_dir: outputPath || null
                    })
                });
                
                progressBar.style.width = '100%';
                
                const data = await response.json();
                showResults(data);
            } catch (e) {
                alert('转换失败: ' + e.message);
            } finally {
                convertBtn.disabled = false;
                setTimeout(() => {
                    document.getElementById('progress').classList.add('hidden');
                    document.getElementById('progressBar').style.width = '0%';
                }, 1000);
            }
        }
        
        function showResults(data) {
            const resultsCard = document.getElementById('resultsCard');
            const resultsDiv = document.getElementById('results');
            
            resultsCard.classList.remove('hidden');
            
            let html = '<div class="log-container">';
            
            const successCount = data.successful || 0;
            const failedCount = data.failed || 0;
            
            html += '<div class="log-line ' + (failedCount === 0 ? 'log-success' : 'log-error') + '" style="font-size:1.1rem; font-weight:600; padding:12px; text-align:center;">[完成] 成功: ' + successCount + ', 失败: ' + failedCount + '</div>';
            
            if (data.results) {
                data.results.forEach(r => {
                    if (!r.success) {
                        html += '<div class="log-line log-error">[' + (r.success ? '成功' : '失败') + '] ' + r.original_path + '</div>';
                        if (r.error) {
                            html += '<div class="log-line log-error" style="padding-left:20px;">原因: ' + r.error + '</div>';
                        }
                    } else {
                        html += '<div class="log-line log-success">✓ ' + r.original_path.split(/[/\\\\]/).pop() + '</div>';
                    }
                });
            }
            
            html += '</div>';
            resultsDiv.innerHTML = html;
        }
        
        function toggleFolder(folderId) {
            const content = document.getElementById(folderId + '_content');
            const icon = document.getElementById(folderId + '_icon');
            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.textContent = '📁 ' + icon.textContent.replace('📂 ', '');
            } else {
                content.style.display = 'none';
                icon.textContent = '📂 ' + icon.textContent.replace('📁 ', '');
            }
        }
        
        async function exitApp() {
            if (!confirm('确定要退出吗？')) return;
            try {
                await fetch('/api/shutdown', {method: 'POST'});
            } catch (e) {}
            setTimeout(() => { window.close(); }, 500);
        }
    </script>
</body>
</html>"""


def check_port(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0


def kill_port(port: int):
    import subprocess
    try:
        result = subprocess.run(f'netstat -ano | findstr :{port}', capture_output=True, text=True, shell=True)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'LISTENING' in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p.isdigit() and i > 0 and parts[i-1] == 'LISTENING':
                        subprocess.run(f'taskkill /PID {p} /F', capture_output=True, shell=True)
                        logger.info(f"已终止端口 {port} 上的进程, PID: {p}")
                        break
    except Exception as e:
        logger.error(f"终止端口 {port} 失败: {e}")


def start_server():
    import uvicorn
    
    port = settings.server.PORT
    
    if check_port(port):
        logger.info(f"端口 {port} 已被占用，正在清理...")
        kill_port(port)
        time.sleep(1)
    
    logger.info(f"正在启动服务 http://{settings.server.HOST}:{port}")
    
    uvicorn.run(
        app,
        host=settings.server.HOST,
        port=port,
        reload=settings.server.RELOAD,
        log_config=None
    )


if __name__ == "__main__":
    print("=" * 50)
    print(f"   {settings.APP_NAME} 文档转PDF工具 v{settings.VERSION}")
    print("=" * 50)
    
    print(f"\n[信息] 运行环境: {settings.ENV}")
    print(f"[信息] 服务地址: http://{settings.server.HOST}:{settings.server.PORT}")
    
    if not settings.server.RELOAD:
        threading.Thread(target=start_server, daemon=True).start()
        
        for i in range(20):
            time.sleep(0.3)
            if check_port(settings.server.PORT):
                print(f"[OK] 服务已就绪!")
                break
        else:
            print("[失败] 服务启动失败!")
            sys.exit(1)
        
        print("\n[信息] 正在打开浏览器...")
        time.sleep(0.5)
        webbrowser.open(f'http://localhost:{settings.server.PORT}')
        
        print("\n" + "=" * 50)
        print("服务已启动，按 Ctrl+C 停止。")
        print("=" * 50)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[信息] 正在关闭...")
            sys.exit(0)
    else:
        start_server()
