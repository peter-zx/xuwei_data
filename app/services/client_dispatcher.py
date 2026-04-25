"""
客户端调度器
负责：
1. 管理客户端注册/保活
2. 任务分配给空闲客户端
3. 查询可用客户端
"""
import uuid
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from app.core.logging import get_logger


@dataclass
class ClientNode:
    client_id: str
    hostname: str
    os_version: str
    last_seen: datetime = field(default_factory=datetime.now)
    available: bool = True
    pending_tasks: int = 0


@dataclass
class PendingTask:
    task_id: str
    client_id: str
    files: List[dict]  # [{id, path, name}]
    output_dir: str
    source_root: str
    created_at: datetime = field(default_factory=datetime.now)


class ClientDispatcher:
    """
    客户端注册表 + 任务队列
    所有操作线程安全（asyncio 环境下单例）
    """
    
    _instance: Optional['ClientDispatcher'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self._clients: Dict[str, ClientNode] = {}
        self._pending_tasks: Dict[str, PendingTask] = {}  # task_id -> PendingTask
        self._client_tasks: Dict[str, str] = {}  # client_id -> task_id (当前任务)
        self._lock = asyncio.Lock()
        self.logger = get_logger("client_dispatcher")
        self.logger.info("ClientDispatcher initialized")
    
    # ── 客户端管理 ───────────────────────────────────────────
    
    def register_client(self, hostname: str, os_version: str) -> str:
        """注册新客户端，返回 client_id"""
        client_id = str(uuid.uuid4())[:12]
        self._clients[client_id] = ClientNode(
            client_id=client_id,
            hostname=hostname or "未知主机",
            os_version=os_version or "",
            last_seen=datetime.now(),
            available=True
        )
        self.logger.info(f"Client registered: {client_id} ({hostname})")
        return client_id
    
    def refresh_client(self, client_id: str) -> bool:
        """保活，更新 last_seen"""
        client = self._clients.get(client_id)
        if not client:
            return False
        client.last_seen = datetime.now()
        return True
    
    def mark_client_available(self, client_id: str):
        """客户端完成任务，标记为空闲"""
        client = self._clients.get(client_id)
        if client:
            client.available = True
            client.pending_tasks = max(0, client.pending_tasks - 1)
        
        # 清理映射
        if self._client_tasks.get(client_id):
            del self._client_tasks[client_id]
    
    def mark_client_busy(self, client_id: str, task_id: str):
        """标记客户端正在执行任务"""
        client = self._clients.get(client_id)
        if client:
            client.available = False
            client.pending_tasks += 1
        self._client_tasks[client_id] = task_id
    
    def unregister_client(self, client_id: str):
        """客户端断开，清理"""
        if client_id in self._clients:
            del self._clients[client_id]
        if client_id in self._client_tasks:
            del self._client_tasks[client_id]
        self.logger.info(f"Client unregistered: {client_id}")
    
    def list_clients(self) -> List[ClientNode]:
        return list(self._clients.values())
    
    def find_available_client(self) -> Optional[ClientNode]:
        """找一台空闲的客户端"""
        for client in self._clients.values():
            if client.available:
                return client
        return None
    
    def get_pending_count(self) -> int:
        return len(self._pending_tasks)
    
    # ── 任务分配 ─────────────────────────────────────────────
    
    def assign_task(
        self,
        client_id: str,
        task_id: str,
        files: List[dict],
        output_dir: str,
        source_root: str
    ):
        """将任务分配给指定客户端"""
        self._pending_tasks[task_id] = PendingTask(
            task_id=task_id,
            client_id=client_id,
            files=files,
            output_dir=output_dir,
            source_root=source_root
        )
        self.mark_client_busy(client_id, task_id)
        self.logger.info(f"Task {task_id} assigned to client {client_id}")
    
    def pop_task_for_client(self, client_id: str) -> Optional[dict]:
        """客户端心跳时，主动查询自己是否有待处理任务"""
        for task_id, task in list(self._pending_tasks.items()):
            if task.client_id == client_id:
                # 返回任务详情后，从 pending 移除（客户端会自己处理）
                del self._pending_tasks[task_id]
                return {
                    "task_id": task.task_id,
                    "files": task.files,
                    "output_dir": task.output_dir,
                    "source_root": task.source_root
                }
        return None
    
    def get_task(self, task_id: str) -> Optional[PendingTask]:
        return self._pending_tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self._pending_tasks.pop(task_id, None)
        if task:
            self.mark_client_available(task.client_id)
            self.logger.info(f"Task {task_id} cancelled")
            return True
        return False


_dispatcher: Optional[ClientDispatcher] = None


def get_dispatcher() -> ClientDispatcher:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = ClientDispatcher()
    return _dispatcher
