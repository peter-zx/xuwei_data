import os
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from dataclasses import dataclass, field


PROJECT_ROOT = Path(__file__).parent.parent.resolve()


@dataclass
class PathConfig:
    STORAGE_ROOT: Path = field(default_factory=lambda: PROJECT_ROOT / "storage")
    UPLOAD_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "storage" / "uploads")
    OUTPUT_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "storage" / "outputs")
    LOG_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")
    TEMPLATES_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "app" / "templates")
    STATIC_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "app" / "static")


@dataclass
class ServerConfig:
    HOST: str = "0.0.0.0"
    PORT: int = 8503
    WORKERS: int = 1
    RELOAD: bool = False


@dataclass
class ConversionConfig:
    MAX_FILE_SIZE_MB: int = 100
    MAX_CONCURRENT_TASKS: int = 4
    TASK_TIMEOUT_SECONDS: int = 300
    SUPPORTED_EXTENSIONS: list = field(default_factory=lambda: [
        '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.pdf'
    ])


@dataclass
class SecurityConfig:
    ALLOWED_ORIGINS: list = field(default_factory=lambda: ["*"])
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024


@dataclass
class Settings:
    ENV: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "Doc2PDF"
    VERSION: str = "3.0"
    
    paths: PathConfig = field(default_factory=PathConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    conversion: ConversionConfig = field(default_factory=ConversionConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    def __post_init__(self):
        self._ensure_directories()
        self._load_env_file()
    
    def _ensure_directories(self):
        for path in [self.paths.UPLOAD_DIR, self.paths.OUTPUT_DIR, self.paths.LOG_DIR]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _load_env_file(self):
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())
        
        self.ENV = os.getenv("APP_ENV", self.ENV)
        self.DEBUG = os.getenv("DEBUG", str(self.DEBUG)).lower() == "true"
        self.server.HOST = os.getenv("HOST", self.server.HOST)
        self.server.PORT = int(os.getenv("PORT", str(self.server.PORT)))
        self.server.RELOAD = os.getenv("RELOAD", str(self.server.RELOAD)).lower() == "true"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    global _settings
    _settings = Settings()
    return _settings
