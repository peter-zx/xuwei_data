import time
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from pydantic import BaseModel

from config.settings import get_settings
from app.core import get_logger, ConversionError
from app.core.scanner import FileScanner, count_files
from app.core.converter import get_converter
from app.services import get_file_service, get_task_service
from app.models.schemas import (
    UploadResponse,
    TaskResponse,
    TaskStatusResponse,
    HealthResponse,
)


class ScanRequest(BaseModel):
    folder_path: str


class ConvertRequest(BaseModel):
    file_ids: List[str] = []
    file_paths: List[str] = []
    preserve_structure: bool = True
    source_root: Optional[str] = None
    output_dir: Optional[str] = None
    # 新增：客户端模式（True = 转换由客户端完成）
    client_mode: bool = False
    client_id: Optional[str] = None


class ClientRegisterRequest(BaseModel):
    hostname: str
    os_version: str


class ClientTaskResultRequest(BaseModel):
    task_id: str
    client_id: str
    results: List[dict]  # [{file_id, success, pdf_path, error, processing_time}]


logger = get_logger("api")
router = APIRouter()
settings = get_settings()
start_time = time.time()


def _format_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="正常",
        version=settings.VERSION,
        environment=settings.ENV,
        uptime=time.time() - start_time
    )


@router.get("/browse-folder")
async def browse_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return JSONResponse({"success": False, "error": "云端环境不支持文件夹浏览，请使用上传功能"})
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    folder_path = filedialog.askdirectory(title="选择文件夹")
    root.destroy()
    
    if folder_path:
        return {"path": folder_path}
    return {"path": ""}


@router.post("/browse-output")
async def browse_output():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return JSONResponse({"success": False, "error": "云端环境不支持文件夹浏览，请使用上传功能"})
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    folder_path = filedialog.askdirectory(title="选择输出文件夹")
    root.destroy()
    
    if folder_path:
        return {"path": folder_path}
    return {"path": ""}


@router.post("/scan")
async def scan_folder(request: ScanRequest):
    try:
        scanner = FileScanner(request.folder_path)
        tree = scanner.scan()
        
        if not tree:
            return JSONResponse({
                "success": False,
                "error": "文件夹不存在或无法访问"
            })
        
        tree_html = scanner.get_file_tree_html(tree)
        total = count_files(tree)
        
        return JSONResponse({
            "success": True,
            "tree_html": tree_html,
            "total_files": total,
            "total_size": _format_size(tree.size),
            "root_name": tree.name
        })
    except Exception as e:
        logger.exception(f"扫描失败: {request.folder_path}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        })


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    file_service = get_file_service()
    
    try:
        file_info = await file_service.save_upload(file)
        
        return UploadResponse(
            success=True,
            file_id=file_info.id,
            filename=file_info.original_name,
            file_size=file_info.file_size,
            message="文件上传成功"
        )
    except Exception as e:
        logger.exception(f"上传失败: {file.filename}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload/batch")
async def upload_files(files: List[UploadFile] = File(...)):
    file_service = get_file_service()
    
    results = []
    for file in files:
        try:
            file_info = await file_service.save_upload(file)
            results.append({
                "success": True,
                "file_id": file_info.id,
                "filename": file_info.original_name,
                "file_size": file_info.file_size
            })
        except Exception as e:
            results.append({
                "success": False,
                "filename": file.filename,
                "error": str(e)
            })
    
    successful = sum(1 for r in results if r.get("success", False))
    return JSONResponse({
        "success": True,
        "total": len(files),
        "successful": successful,
        "failed": len(files) - successful,
        "results": results
    })


@router.get("/files")
async def list_files():
    file_service = get_file_service()
    files = file_service.list_files()
    
    return JSONResponse({
        "success": True,
        "files": [
            {
                "id": f.id,
                "filename": f.original_name,
                "size": f.file_size,
                "size_formatted": _format_size(f.file_size),
                "extension": f.extension,
                "upload_time": f.upload_time.isoformat()
            }
            for f in files
        ]
    })


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    file_service = get_file_service()
    
    if file_service.delete_file(file_id):
        return JSONResponse({"success": True, "message": "文件已删除"})
    else:
        raise HTTPException(status_code=404, detail="文件不存在")


@router.post("/convert")
async def convert_files(request: ConvertRequest):
    file_service = get_file_service()
    
    file_paths = []
    
    for file_id in request.file_ids:
        file_path = file_service.get_file_path(file_id)
        if file_path and file_path.exists():
            file_paths.append(str(file_path))
        else:
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_id}")
    
    for path in request.file_paths:
        if Path(path).exists():
            file_paths.append(path)
        else:
            raise HTTPException(status_code=404, detail=f"文件不存在: {path}")
    
    if not file_paths:
        raise HTTPException(status_code=400, detail="未选择文件")
    
    converter = get_converter(
        output_dir=request.output_dir,
        source_root=request.source_root
    )
    results = converter.convert_batch(file_paths)
    
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    return JSONResponse({
        "success": True,
        "total": len(results),
        "successful": successful,
        "failed": failed,
        "results": [
            {
                "success": r.success,
                "original_path": r.original_path,
                "output_path": r.output_path,
                "error": r.error,
                "file_size": r.file_size,
                "processing_time": r.processing_time
            }
            for r in results
        ]
    })


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    task_service = get_task_service()
    task = task_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskStatusResponse(
        success=True,
        task_id=task.task_id,
        status=task.status,
        total_files=task.total_files,
        processed_files=task.processed_files,
        successful=task.successful,
        failed=task.failed,
        results=[
            {
                "success": r.success,
                "original_path": r.original_path,
                "output_path": r.output_path,
                "error": r.error,
                "file_size": r.file_size,
                "processing_time": r.processing_time
            }
            for r in task.results
        ],
        error_message=task.error_message
    )


@router.get("/tasks")
async def list_tasks():
    task_service = get_task_service()
    tasks = task_service.list_tasks()
    
    return JSONResponse({
        "success": True,
        "tasks": [
            {
                "task_id": t.task_id,
                "status": t.status.value,
                "total_files": t.total_files,
                "processed_files": t.processed_files,
                "successful": t.successful,
                "failed": t.failed,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None
            }
            for t in tasks[-10:]
        ]
    })


# ══════════════════════════════════════════════════════
#  客户端调度接口（客户端模式）
# ══════════════════════════════════════════════════════

@router.post("/client/register")
async def client_register(request: ClientRegisterRequest):
    """
    客户端启动时注册，获取 client_id
    """
    from app.services.client_dispatcher import get_dispatcher
    
    dispatcher = get_dispatcher()
    client_id = dispatcher.register_client(
        hostname=request.hostname,
        os_version=request.os_version
    )
    
    return JSONResponse({
        "success": True,
        "client_id": client_id,
        "server_url": str(settings.SERVER_URL),
        "heartbeat_interval": 30
    })


@router.post("/client/heartbeat")
async def client_heartbeat(client_id: str):
    """
    客户端保活
    """
    from app.services.client_dispatcher import get_dispatcher
    
    dispatcher = get_dispatcher()
    alive = dispatcher.refresh_client(client_id)
    
    if not alive:
        return JSONResponse({"success": False, "error": "client not found"}, status_code=404)
    
    # 主动推送分配给该客户端的任务
    task = dispatcher.pop_task_for_client(client_id)
    
    return JSONResponse({
        "success": True,
        "task": task,
        "pending_count": dispatcher.get_pending_count()
    })


@router.post("/client/result")
async def client_submit_result(request: ClientTaskResultRequest):
    """
    客户端完成转换后，提交结果
    1. 上传 PDF 文件
    2. 更新任务状态
    """
    from app.services.client_dispatcher import get_dispatcher
    
    file_service = get_file_service()
    task_service = get_task_service()
    
    task = task_service.get_task(request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    dispatcher = get_dispatcher()
    dispatcher.mark_client_available(request.client_id)
    
    # 处理每个转换结果
    for res in request.results:
        file_id = res.get("file_id", "")
        success = res.get("success", False)
        pdf_path = res.get("pdf_path", "")
        error = res.get("error", "")
        processing_time = res.get("processing_time", 0.0)
        
        if success and pdf_path:
            # 上传 PDF 文件到服务器存储
            try:
                from app.models.schemas import ConversionResultData
                
                result_data = ConversionResultData(
                    success=True,
                    original_path=res.get("original_path", ""),
                    output_path=pdf_path,
                    file_size=Path(pdf_path).stat().st_size if Path(pdf_path).exists() else 0,
                    processing_time=processing_time
                )
                task_service.add_result(request.task_id, result_data)
            except Exception as e:
                logger.error(f"Failed to save client result: {e}")
        
        # 记录失败
        if not success:
            from app.models.schemas import ConversionResultData
            result_data = ConversionResultData(
                success=False,
                original_path=res.get("original_path", ""),
                output_path="",
                error=error,
                processing_time=processing_time
            )
            task_service.add_result(request.task_id, result_data)
    
    # 检查是否全部完成
    task = task_service.get_task(request.task_id)
    if task:
        if task.processed_files >= task.total_files:
            from app.models.schemas import TaskStatus
            task_service.update_task_status(
                request.task_id,
                TaskStatus.COMPLETED if task.failed < task.total_files else TaskStatus.FAILED
            )
    
    return JSONResponse({
        "success": True,
        "task_id": request.task_id,
        "processed": task.processed_files if task else 0
    })


@router.get("/client/list")
async def list_clients():
    """查看当前在线的客户端"""
    from app.services.client_dispatcher import get_dispatcher
    
    dispatcher = get_dispatcher()
    clients = dispatcher.list_clients()
    
    return JSONResponse({
        "success": True,
        "clients": [
            {
                "client_id": c.client_id,
                "hostname": c.hostname,
                "os_version": c.os_version,
                "last_seen": c.last_seen.isoformat(),
                "available": c.available,
                "pending_tasks": c.pending_tasks
            }
            for c in clients
        ]
    })


@router.post("/convert/client")
async def convert_via_client(request: ConvertRequest):
    """
    客户端模式：创建任务，分配给在线客户端执行
    流程：
    1. 创建任务
    2. 将任务分配给可用的客户端
    3. 返回 task_id（前端轮询 task 状态）
    """
    if not request.client_mode:
        raise HTTPException(status_code=400, detail="client_mode must be True")
    
    file_service = get_file_service()
    task_service = get_task_service()
    dispatcher = get_dispatcher()
    
    # 收集文件路径
    file_paths = []
    for file_id in request.file_ids:
        fp = file_service.get_file_path(file_id)
        if fp and fp.exists():
            file_paths.append(str(fp))
        else:
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_id}")
    
    for path in request.file_paths:
        if Path(path).exists():
            file_paths.append(path)
        else:
            raise HTTPException(status_code=404, detail=f"文件不存在: {path}")
    
    if not file_paths:
        raise HTTPException(status_code=400, detail="未选择文件")
    
    # 创建任务
    task = task_service.create_task(total_files=len(file_paths))
    from app.models.schemas import TaskStatus
    task_service.update_task_status(task.task_id, TaskStatus.PROCESSING)
    
    # 构建文件列表（带上 file_id，方便客户端识别）
    files_info = []
    for i, fp in enumerate(file_paths):
        file_id = request.file_ids[i] if i < len(request.file_ids) else f"_path_{i}"
        files_info.append({
            "id": file_id,
            "path": fp,
            "name": Path(fp).name
        })
    
    # 查找可用客户端
    available_client = dispatcher.find_available_client()
    if not available_client:
        # 没有客户端在线，创建空任务等待
        task_service.update_task_status(
            task.task_id,
            TaskStatus.FAILED,
            "没有在线的客户端，请确保 Doc2PDF 客户端已启动"
        )
        return JSONResponse({
            "success": False,
            "error": "没有在线的客户端，请确保 Doc2PDF 客户端已启动",
            "task_id": task.task_id
        }, status_code=503)
    
    # 分配任务给客户端
    dispatcher.assign_task(
        client_id=available_client.client_id,
        task_id=task.task_id,
        files=files_info,
        output_dir=request.output_dir or str(settings.paths.OUTPUT_DIR),
        source_root=request.source_root or ""
    )
    
    logger.info(f"Task {task.task_id} assigned to client {available_client.hostname}")
    
    return JSONResponse({
        "success": True,
        "task_id": task.task_id,
        "client_hostname": available_client.hostname,
        "client_id": available_client.client_id,
        "message": f"任务已分配给 {available_client.hostname}，正在转换..."
    })


@router.get("/download/{filename}")
    output_dir = settings.paths.OUTPUT_DIR
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/pdf'
    )


@router.post("/shutdown")
async def shutdown_server():
    def shutdown():
        import os
        time.sleep(0.5)
        os._exit(0)
    
    import threading
    threading.Thread(target=shutdown, daemon=True).start()
    return {"message": "正在关闭服务"}
