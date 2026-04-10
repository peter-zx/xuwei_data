import asyncio
import time
from typing import Dict, Optional, Callable, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from config.settings import get_settings
from app.core.logging import get_logger
from app.models.schemas import TaskInfo, TaskStatus, ConversionResultData


class TaskService:
    _tasks: Dict[str, TaskInfo] = {}
    _executor: Optional[ThreadPoolExecutor] = None
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("task_service")
    
    @property
    def executor(self) -> ThreadPoolExecutor:
        if TaskService._executor is None:
            max_workers = self.settings.conversion.MAX_CONCURRENT_TASKS
            TaskService._executor = ThreadPoolExecutor(max_workers=max_workers)
        return TaskService._executor
    
    def create_task(self, total_files: int = 0) -> TaskInfo:
        task = TaskInfo(total_files=total_files)
        TaskService._tasks[task.task_id] = task
        self.logger.info(f"Task created: {task.task_id} | Total files: {total_files}")
        return task
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        return TaskService._tasks.get(task_id)
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error_message: str = ""
    ) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        
        task.status = status
        if error_message:
            task.error_message = error_message
        if status == TaskStatus.COMPLETED or status == TaskStatus.FAILED:
            task.completed_at = datetime.now()
        
        self.logger.info(f"Task {task_id} status: {status.value}")
        return True
    
    def add_result(
        self,
        task_id: str,
        result: ConversionResultData
    ) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        
        task.results.append(result)
        task.processed_files += 1
        if result.success:
            task.successful += 1
        else:
            task.failed += 1
        
        return True
    
    def update_progress(
        self,
        task_id: str,
        processed: int,
        successful: int,
        failed: int
    ) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        
        task.processed_files = processed
        task.successful = successful
        task.failed = failed
        return True
    
    async def run_conversion(
        self,
        task_id: str,
        convert_func: Callable,
        *args,
        **kwargs
    ) -> TaskInfo:
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        self.update_task_status(task_id, TaskStatus.PROCESSING)
        
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                lambda: convert_func(*args, **kwargs)
            )
            
            for result in results:
                self.add_result(task_id, result)
            
            failed_count = sum(1 for r in results if not r.success)
            final_status = TaskStatus.FAILED if failed_count == len(results) else TaskStatus.COMPLETED
            
            self.update_task_status(task_id, final_status)
            
        except Exception as e:
            self.logger.exception(f"Task {task_id} failed with exception")
            self.update_task_status(task_id, TaskStatus.FAILED, str(e))
        
        return self.get_task(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        
        if task.status == TaskStatus.PROCESSING:
            self.logger.warning(f"Cannot cancel task {task_id}: already processing")
            return False
        
        self.update_task_status(task_id, TaskStatus.FAILED, "Cancelled by user")
        return True
    
    def list_tasks(self) -> list[TaskInfo]:
        return list(TaskService._tasks.values())
    
    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        count = 0
        now = datetime.now()
        for task_id in list(TaskService._tasks.keys()):
            task = TaskService._tasks[task_id]
            if task.completed_at:
                age = (now - task.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    del TaskService._tasks[task_id]
                    count += 1
        return count


_task_service: Optional[TaskService] = None


def get_task_service() -> TaskService:
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service
