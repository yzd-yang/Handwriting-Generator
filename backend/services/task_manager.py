"""
任务状态管理与 WebSocket 推送。

从 app.py 中拆分出来（P1 2.4 重构）。
"""

import asyncio
from typing import Any, Optional

from fastapi import WebSocket

from task_store import get_task as get_generation_task
from task_store import get_queue_metrics as get_generation_queue_metrics
from task_types import GenerationTask

from utils.logging_setup import get_logger

logger = get_logger(__name__)

# WebSocket 推送（仍需内存存储，仅同进程有效）
task_websocket_connections: dict[str, set[WebSocket]] = {}
task_websocket_connections_lock = asyncio.Lock()


def build_task_status_payload(task_id: str, task: Optional[GenerationTask] = None) -> Optional[dict[str, Any]]:
    """构建任务状态响应体。"""
    if task is None:
        task = get_generation_task(task_id)
    if task is None:
        return None
    queue_metrics = get_generation_queue_metrics(task_id)
    return {
        "status": "success",
        "task_id": task_id,
        "task_status": task.get("status"),
        "task_stage": task.get("stage"),
        "task_message": task.get("message"),
        "task_progress": task.get("progress"),
        "created_at": task.get("created_at"),
        "updated_at": task.get("updated_at"),
        "error_message": task.get("error_message"),
        "queue_pending_count": queue_metrics.get("queue_pending_count"),
        "queue_ahead_count": queue_metrics.get("queue_ahead_count"),
        "processing_count": queue_metrics.get("processing_count"),
        "active_task_count": queue_metrics.get("active_task_count"),
    }


async def register_task_websocket(task_id, websocket):
    """注册 WebSocket 连接，用于推送任务状态更新。"""
    async with task_websocket_connections_lock:
        if task_id not in task_websocket_connections:
            task_websocket_connections[task_id] = set()
        task_websocket_connections[task_id].add(websocket)


async def unregister_task_websocket(task_id, websocket):
    """注销 WebSocket 连接。"""
    async with task_websocket_connections_lock:
        sockets = task_websocket_connections.get(task_id)
        if sockets is None:
            return
        sockets.discard(websocket)
        if len(sockets) == 0:
            task_websocket_connections.pop(task_id, None)


async def push_task_status_update(task_id):
    """向所有订阅了该任务的 WebSocket 连接推送状态更新。"""
    task = get_generation_task(task_id)
    if task is None:
        return
    payload = build_task_status_payload(task_id, task=task)
    if payload is None:
        return
    async with task_websocket_connections_lock:
        sockets = list(task_websocket_connections.get(task_id, set()))
    if len(sockets) == 0:
        return

    dead_sockets = []
    for socket in sockets:
        try:
            await socket.send_json(payload)
        except Exception:
            dead_sockets.append(socket)

    if dead_sockets:
        async with task_websocket_connections_lock:
            current_sockets = task_websocket_connections.get(task_id, set())
            for socket in dead_sockets:
                current_sockets.discard(socket)
            if len(current_sockets) == 0 and task_id in task_websocket_connections:
                task_websocket_connections.pop(task_id, None)


def model_to_dict(model):
    """将 Pydantic 模型转为 dict（兼容 v1/v2）。"""
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)
