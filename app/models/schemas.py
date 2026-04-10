from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConversionResultData(BaseModel):
    success: bool
    original_path: str
    output_path: str = ""
    error: str = ""
    file_size: int = 0
    processing_time: float = 0.0


class TaskInfo(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    total_files: int = 0
    processed_files: int = 0
    successful: int = 0
    failed: int = 0
    results: List[ConversionResultData] = []
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: str = ""


class FileInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    original_name: str
    file_path: str
    file_size: int
    mime_type: str
    extension: str
    upload_time: datetime = Field(default_factory=datetime.now)
    status: str = "uploaded"


class FileNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    path: str
    is_folder: bool
    size: int = 0
    extension: str = ""
    children: List['FileNode'] = []
    checked: bool = False


class ScanResponse(BaseModel):
    success: bool
    tree: Optional[FileNode] = None
    total_files: int = 0
    total_size: int = 0
    total_size_formatted: str = ""
    error: str = ""


class UploadResponse(BaseModel):
    success: bool
    file_id: str
    filename: str
    file_size: int
    message: str = ""


class TaskResponse(BaseModel):
    success: bool
    task_id: str
    status: TaskStatus
    message: str = ""


class TaskStatusResponse(BaseModel):
    success: bool
    task_id: str
    status: TaskStatus
    total_files: int = 0
    processed_files: int = 0
    successful: int = 0
    failed: int = 0
    results: List[Dict[str, Any]] = []
    error_message: str = ""


class ConversionRequest(BaseModel):
    file_ids: List[str]
    preserve_structure: bool = True


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    uptime: float
