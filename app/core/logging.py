import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
from datetime import datetime


class Logger:
    _loggers = {}
    
    def __init__(self, name: str, log_dir: Path, level: int = logging.INFO):
        self.name = name
        self.log_dir = log_dir
        self.level = level
        self._logger = None
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        logger.handlers.clear()
        
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = self._setup_logger()
        return self._logger
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra=kwargs)
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra=kwargs)
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra=kwargs)
    
    def error(self, msg: str, **kwargs):
        self.logger.error(msg, extra=kwargs)
    
    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, extra=kwargs)
    
    def exception(self, msg: str, **kwargs):
        self.logger.exception(msg, extra=kwargs)


def get_logger(name: str, log_dir: Optional[Path] = None) -> Logger:
    if name not in Logger._loggers:
        if log_dir is None:
            from config.settings import get_settings
            log_dir = get_settings().paths.LOG_DIR
        Logger._loggers[name] = Logger(name, log_dir)
    return Logger._loggers[name]


def log_operation(operation: str, status: str, details: dict = None):
    logger = get_logger("operations")
    msg = f"[{operation}] Status: {status}"
    if details:
        msg += f" | Details: {details}"
    if status == "SUCCESS":
        logger.info(msg)
    else:
        logger.error(msg)
