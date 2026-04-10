import time
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

from config.settings import get_settings
from app.core import get_logger, ConversionError
from app.core.converter import get_converter
from app.services import get_file_service, get_task_service
from app.models.schemas import (
    UploadResponse,
    ConversionRequest,
    TaskResponse,
    TaskStatusResponse,
    HealthResponse,
)


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


@router.post("/convert", response_model=TaskResponse)
async def convert_files(request: ConversionRequest, background_tasks: BackgroundTasks):
    if not request.file_ids:
        raise HTTPException(status_code=400, detail="未选择文件")
    
    file_service = get_file_service()
    task_service = get_task_service()
    
    file_paths = []
    for file_id in request.file_ids:
        file_path = file_service.get_file_path(file_id)
        if file_path and file_path.exists():
            file_paths.append(str(file_path))
        else:
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_id}")
    
    task = task_service.create_task(total_files=len(file_paths))
    
    async def run_conversion():
        converter = get_converter()
        results = converter.convert_batch(file_paths)
        
        for result in results:
            task_service.add_result(task.task_id, result.to_data())
        
        task_service.update_task_status(
            task.task_id,
            "completed" if any(r.success for r in results) else "failed"
        )
    
    background_tasks.add_task(run_conversion)
    
    return TaskResponse(
        success=True,
        task_id=task.task_id,
        status=task.status,
        message=f"转换任务已创建: {len(file_paths)} 个文件"
    )


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


@router.get("/download/{filename}")
async def download_file(filename: str):
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
