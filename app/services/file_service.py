import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from fastapi import UploadFile

from config.settings import get_settings
from app.core.logging import get_logger
from app.core.exceptions import FileValidationError, FileStorageError, UnsupportedFormatError, FileTooLargeError
from app.models.schemas import FileInfo, FileNode


class FileService:
    _file_registry: Dict[str, FileInfo] = {}
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("file_service")
        self.upload_dir = self.settings.paths.UPLOAD_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        ext = Path(original_filename).suffix.lower()
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime("%m%d_%H%M%S")
        return f"{timestamp}_{unique_id}{ext}"
    
    def _get_mime_type(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        mime_types = {
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    async def save_upload(self, file: UploadFile) -> FileInfo:
        try:
            original_name = file.filename or "unknown"
            ext = Path(original_name).suffix.lower()
            
            if ext not in self.settings.conversion.SUPPORTED_EXTENSIONS:
                raise UnsupportedFormatError(ext)
            
            unique_filename = self._generate_unique_filename(original_name)
            file_path = self.upload_dir / unique_filename
            
            file_content = await file.read()
            file_size = len(file_content)
            
            max_size = self.settings.security.MAX_UPLOAD_SIZE
            if file_size > max_size:
                raise FileTooLargeError(file_size, max_size)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            file_info = FileInfo(
                filename=unique_filename,
                original_name=original_name,
                file_path=str(file_path),
                file_size=file_size,
                mime_type=self._get_mime_type(original_name),
                extension=ext
            )
            
            FileService._file_registry[file_info.id] = file_info
            
            self.logger.info(f"File uploaded: {file_info.id} | {original_name} | {file_size} bytes")
            
            return file_info
            
        except FileValidationError:
            raise
        except Exception as e:
            self.logger.exception(f"Failed to save upload: {original_name}")
            raise FileStorageError(f"Failed to save file: {str(e)}")
    
    async def save_batch(self, files: List[UploadFile]) -> List[FileInfo]:
        results = []
        for file in files:
            try:
                file_info = await self.save_upload(file)
                results.append(file_info)
            except Exception as e:
                self.logger.error(f"Failed to upload {file.filename}: {str(e)}")
        return results
    
    def get_file(self, file_id: str) -> Optional[FileInfo]:
        return FileService._file_registry.get(file_id)
    
    def get_file_path(self, file_id: str) -> Optional[Path]:
        file_info = self.get_file(file_id)
        if file_info:
            return Path(file_info.file_path)
        return None
    
    def delete_file(self, file_id: str) -> bool:
        file_info = FileService._file_registry.get(file_id)
        if not file_info:
            return False
        
        try:
            file_path = Path(file_info.file_path)
            if file_path.exists():
                file_path.unlink()
            del FileService._file_registry[file_id]
            self.logger.info(f"File deleted: {file_id}")
            return True
        except Exception as e:
            self.logger.exception(f"Failed to delete file: {file_id}")
            return False
    
    def list_files(self) -> List[FileInfo]:
        return list(FileService._file_registry.values())
    
    def clear_temp_files(self) -> int:
        count = 0
        for file_id in list(FileService._file_registry.keys()):
            if self.delete_file(file_id):
                count += 1
        return count


def get_file_service() -> FileService:
    return FileService()
