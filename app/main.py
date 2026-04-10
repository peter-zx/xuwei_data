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
    logger.info(f"输出目录: {settings.paths.OUTPUT_DIR}")
    
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
        .drop-zone { width: 100%; min-height: 150px; border: 3px dashed #d1d5db; border-radius: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; background: #fafafa; margin-bottom: 16px; }
        .drop-zone:hover { border-color: #667eea; background: #f5f5ff; }
        .drop-zone.dragover { border-color: #667eea; background: #f0f0ff; }
        .drop-zone-content { text-align: center; }
        .btn { padding: 12px 24px; border: none; border-radius: 10px; font-size: 0.95rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        .btn-success { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
        .btn-success:hover { transform: translateY(-2px); }
        .file-list { list-style: none; max-height: 300px; overflow-y: auto; }
        .file-item { padding: 12px; border-radius: 8px; margin-bottom: 8px; background: #f9fafb; display: flex; align-items: center; gap: 12px; }
        .file-item input[type="checkbox"] { width: 18px; height: 18px; }
        .file-name { flex: 1; }
        .file-size { color: #9ca3af; font-size: 0.85rem; }
        .progress-bar { height: 10px; background: #e5e7eb; border-radius: 5px; overflow: hidden; margin-top: 16px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); transition: width 0.3s; }
        .result-item { padding: 12px 16px; border-radius: 10px; margin-bottom: 10px; }
        .result-success { background: #d1fae5; color: #10b981; }
        .result-failed { background: #fee2e2; color: #ef4444; }
        .stats { display: flex; gap: 16px; margin-top: 16px; }
        .stat { flex: 1; text-align: center; padding: 16px; background: #f3f4f6; border-radius: 10px; }
        .stat-value { font-size: 1.5rem; font-weight: 700; color: #667eea; }
        .stat-label { font-size: 0.8rem; color: #6b7280; margin-top: 4px; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>文档转PDF工具</h1>
            <p>支持 Word/Excel/PPT/TXT 转换为 PDF</p>
        </div>
        
        <div class="card">
            <h2 style="margin-bottom: 16px;">1. 上传文件</h2>
            <div id="dropZone" class="drop-zone">
                <div class="drop-zone-content">
                    <div style="font-size: 3rem; margin-bottom: 10px;">📁</div>
                    <div style="font-size: 1.1rem; font-weight: 600;">拖拽文件到此处或点击上传</div>
                    <div style="font-size: 0.9rem; color: #9ca3af; margin-top: 8px;">支持格式: DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, PDF</div>
                </div>
                <input type="file" id="fileInput" multiple accept=".doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.pdf" style="display: none;">
            </div>
            
            <div id="fileList" class="file-list hidden"></div>
            
            <div id="stats" class="stats hidden">
                <div class="stat">
                    <div class="stat-value" id="totalFiles">0</div>
                    <div class="stat-label">文件数</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="totalSize">0</div>
                    <div class="stat-label">总大小</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2 style="margin-bottom: 16px;">2. 开始转换</h2>
            <button class="btn btn-success" id="convertBtn" onclick="startConvert()" disabled>开始转换</button>
            
            <div id="progress" class="hidden" style="margin-top: 16px;">
                <p id="progressText">转换中...</p>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressBar" style="width: 0%"></div>
                </div>
            </div>
        </div>
        
        <div class="card hidden" id="resultsCard">
            <h2 style="margin-bottom: 16px;">3. 转换结果</h2>
            <div id="results"></div>
        </div>
    </div>
    
    <script>
        let uploadedFiles = [];
        let selectedFiles = new Set();
        
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); handleFiles(e.dataTransfer.files); });
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
                    updateFileList();
                }
            } catch (e) {
                console.error('上传失败:', e);
            }
        }
        
        function updateFileList() {
            const list = document.getElementById('fileList');
            const stats = document.getElementById('stats');
            
            if (uploadedFiles.length === 0) {
                list.classList.add('hidden');
                stats.classList.add('hidden');
                return;
            }
            
            list.classList.remove('hidden');
            stats.classList.remove('hidden');
            
            list.innerHTML = uploadedFiles.map(f => `
                <div class="file-item">
                    <input type="checkbox" onchange="toggleFile('${f.id}')">
                    <span class="file-name">${f.name}</span>
                    <span class="file-size">${formatSize(f.size)}</span>
                </div>
            `).join('');
            
            document.getElementById('totalFiles').textContent = uploadedFiles.length;
            document.getElementById('totalSize').textContent = formatSize(uploadedFiles.reduce((a, f) => a + f.size, 0));
            
            document.getElementById('convertBtn').disabled = selectedFiles.size === 0;
        }
        
        function toggleFile(id) {
            if (selectedFiles.has(id)) selectedFiles.delete(id);
            else selectedFiles.add(id);
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
            if (selectedFiles.size === 0) return;
            
            const convertBtn = document.getElementById('convertBtn');
            const progress = document.getElementById('progress');
            
            convertBtn.disabled = true;
            progress.classList.remove('hidden');
            
            try {
                const response = await fetch('/api/convert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_ids: Array.from(selectedFiles), preserve_structure: true })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('resultsCard').classList.remove('hidden');
                    document.getElementById('results').innerHTML = `
                        <div class="result-item result-success">
                            任务已创建: ${data.task_id}
                        </div>
                    `;
                }
            } catch (e) {
                console.error('转换失败:', e);
            } finally {
                convertBtn.disabled = false;
            }
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
