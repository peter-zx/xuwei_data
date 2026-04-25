import os
import json
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
from dataclasses import dataclass, field


PROJECT_ROOT = Path(__file__).parent.parent.resolve()


@dataclass
class PathConfig:
    STORAGE_ROOT: Path = field(default_factory=lambda: PROJECT_ROOT / "storage")
    UPLOAD_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "storage" / "uploads")
    OUTPUT_DIR: Path = field(
        default_factory=lambda: PROJECT_ROOT / "storage" / "outputs"
    )
    LOG_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")
    TEMPLATES_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "app" / "templates")
    STATIC_DIR: Path = field(default_factory=lambda: PROJECT_ROOT / "app" / "static")
    ALLOWED_SCAN_ROOTS: List[str] = field(
        default_factory=lambda: [str(PROJECT_ROOT / "storage")]
    )


@dataclass
class ServerConfig:
    HOST: str = "0.0.0.0"
    PORT: int = 8503
    WORKERS: int = 1
    RELOAD: bool = False
    # 客户端连接地址（填写服务器实际 IP/域名，客户端用此地址连接）
    BASE_URL: str = "http://localhost:8503"


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
    APP_NAME: str = "文档转PDF工具"
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
        self.server.BASE_URL = os.getenv("BASE_URL", self.server.BASE_URL)
        
        # 全局便捷访问
        self._server_url = self.server.BASE_URL
        
        # 应用额外环境变量覆盖
        self._apply_env_overrides()
    
    @property
    def SERVER_URL(self) -> str:
        return self.server.BASE_URL

    def _apply_env_overrides(self):
        # 输出目录支持环境变量覆盖（云端必须配置）
        output_dir_env = os.getenv("OUTPUT_DIR")
        if output_dir_env:
            self.paths.OUTPUT_DIR = Path(output_dir_env)
        
        # 允许扫描的目录列表（安全隔离）
        scan_roots_env = os.getenv("ALLOWED_SCAN_ROOTS")
        if scan_roots_env:
            self.paths.ALLOWED_SCAN_ROOTS = [
                p.strip() for p in scan_roots_env.split(",") if p.strip()
            ]


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
