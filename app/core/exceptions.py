from typing import Optional, Any, Dict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


class AppException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class FileValidationError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="FILE_VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class FileStorageError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="FILE_STORAGE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ConversionError(AppException):
    def __init__(self, message: str, file_path: str = "", details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if file_path:
            details["file_path"] = file_path
        super().__init__(
            message=message,
            code="CONVERSION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class UnsupportedFormatError(FileValidationError):
    def __init__(self, file_extension: str):
        super().__init__(
            message=f"不支持的文件格式: {file_extension}",
            details={"extension": file_extension}
        )


class FileTooLargeError(FileValidationError):
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f"文件大小 {file_size} 超过最大限制 {max_size}",
            details={"file_size": file_size, "max_size": max_size}
        )


class TaskNotFoundError(AppException):
    def __init__(self, task_id: str):
        super().__init__(
            message=f"任务不存在: {task_id}",
            code="TASK_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": task_id}
        )


class async_context:
    def __init__(self, logger=None):
        self.logger = logger
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and self.logger:
            self.logger.exception(f"Exception in async context: {exc_val}")
        return False


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    from .logging import get_logger
    logger = get_logger("exceptions")
    logger.error(
        f"AppException: {exc.message} | Code: {exc.code} | Path: {request.url.path}",
        **exc.details
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    from .logging import get_logger
    logger = get_logger("exceptions")
    logger.error(f"验证错误: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求验证失败",
                "details": {"errors": exc.errors()}
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from .logging import get_logger
    logger = get_logger("exceptions")
    logger.exception(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "发生内部错误",
                "details": {}
            }
        }
    )


def register_exception_handlers(app):
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
