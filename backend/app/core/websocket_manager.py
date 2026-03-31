"""
WebSocket Manager - WebSocket 连接管理器

提供 WebSocket 连接池管理、心跳检测、自动重连和泄漏检测功能。
支持 Prometheus 指标导出和广播消息。
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.utils.logger import get_logger
from app.core.redis_client import get_redis_client

logger = get_logger(__name__)


# ========== 数据类 ==========

@dataclass
class ConnectionStats:
    """连接统计信息"""
    total_connections: int = 0
    active_connections: int = 0
    max_connections_per_user: int = 5
    total_messages_sent: int = 0
    total_messages_received: int = 0
    average_latency_ms: float = 0.0
    orphaned_connections_cleaned: int = 0
    reconnection_attempts: int = 0
    last_health_check: float = field(default_factory=time.time)


@dataclass
class WebSocketConnection:
    """WebSocket 连接包装器"""
    websocket: WebSocket
    session_id: str
    user_id: Optional[str] = None
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    message_count: int = 0
    is_alive: bool = True
    reconnect_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ========== WebSocket 管理器 ==========

class WebSocketManager:
    """
    WebSocket 连接管理器
    
    功能：
    - 连接池管理（max_connections_per_user=5）
    - 心跳检测（30s ping/pong）
    - 自动重连（max_retries=3）
    - 泄漏检测（orphaned connection cleanup）
    - 广播消息
    - Prometheus 指标导出
    """
    
    def __init__(
        self,
        max_connections_per_user: int = 5,
        heartbeat_interval: int = 30,
        max_reconnect_retries: int = 3,
        orphan_timeout: int = 300,  # 5 分钟无活动视为孤儿连接
    ):
        """
        初始化 WebSocket 管理器
        
        Args:
            max_connections_per_user: 每用户最大连接数
            heartbeat_interval: 心跳间隔（秒）
            max_reconnect_retries: 最大重连次数
            orphan_timeout: 孤儿连接超时时间（秒）
        """
        self.max_connections_per_user = max_connections_per_user or settings.WEBSOCKET_MAX_CONNECTIONS_PER_USER
        self.heartbeat_interval = heartbeat_interval or settings.WEBSOCKET_HEARTBEAT_INTERVAL
        self.max_reconnect_retries = max_reconnect_retries
        self.orphan_timeout = orphan_timeout
        
        # 连接存储
        self._connections: Dict[str, WebSocketConnection] = {}  # connection_id -> connection
        self._session_connections: Dict[str, Set[str]] = defaultdict(set)  # session_id -> connection_ids
        self._user_connections: Dict[str, Set[str]] = defaultdict(set)  # user_id -> connection_ids
        
        # 统计信息
        self._stats = ConnectionStats(
            max_connections_per_user=self.max_connections_per_user,
        )
        
        # 心跳任务
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # 回调函数
        self._on_connect_callbacks: List[Callable] = []
        self._on_disconnect_callbacks: List[Callable] = []
        self._on_message_callbacks: List[Callable] = []
        
        # 锁
        self._lock = asyncio.Lock()
        
        # Prometheus 指标
        self._websocket_connections_gauge = 0
        self._websocket_messages_counter = 0
        self._websocket_errors_counter = 0
    
    async def start_background_tasks(self):
        """启动后台任务（心跳检测和清理）"""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("WebSocket 后台任务已启动")
    
    async def stop_background_tasks(self):
        """停止后台任务"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        logger.info("WebSocket 后台任务已停止")
    
    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> str:
        """
        建立 WebSocket 连接
        
        Args:
            websocket: WebSocket 实例
            session_id: 会话 ID
            user_id: 用户 ID（可选）
        
        Returns:
            connection_id: 连接 ID
        
        Raises:
            RuntimeError: 超过最大连接数
        """
        # 检查连接数限制
        if user_id:
            user_conns = len(self._user_connections.get(user_id, set()))
            if user_conns >= self.max_connections_per_user:
                logger.warning(f"用户 {user_id} 连接数已达上限 ({user_conns}/{self.max_connections_per_user})")
                raise RuntimeError(
                    f"Maximum connections per user ({self.max_connections_per_user}) exceeded"
                )
        
        # 接受连接
        await websocket.accept()
        
        # 生成连接 ID
        connection_id = str(uuid.uuid4())
        
        # 创建连接对象
        connection = WebSocketConnection(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id,
        )
        
        # 存储连接
        async with self._lock:
            self._connections[connection_id] = connection
            self._session_connections[session_id].add(connection_id)
            if user_id:
                self._user_connections[user_id].add(connection_id)
            
            self._stats.total_connections += 1
            self._stats.active_connections = len(self._connections)
            self._websocket_connections_gauge = self._stats.active_connections
        
        # 触发回调
        for callback in self._on_connect_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(connection_id, session_id, user_id)
                else:
                    callback(connection_id, session_id, user_id)
            except Exception as e:
                logger.error(f"OnConnect 回调失败：{e}")
        
        logger.info(f"WebSocket 连接建立：{connection_id} (session={session_id}, user={user_id})")
        return connection_id
    
    async def disconnect(
        self,
        connection_id: str,
        reason: Optional[str] = None,
    ):
        """
        断开 WebSocket 连接
        
        Args:
            connection_id: 连接 ID
            reason: 断开原因
        """
        async with self._lock:
            connection = self._connections.pop(connection_id, None)
            
            if not connection:
                return
            
            # 清理索引
            self._session_connections[connection.session_id].discard(connection_id)
            if connection.user_id:
                self._user_connections[connection.user_id].discard(connection_id)
            
            self._stats.active_connections = len(self._connections)
            self._websocket_connections_gauge = self._stats.active_connections
        
        # 关闭 WebSocket
        try:
            await connection.websocket.close(code=1000, reason=reason or "Normal closure")
        except Exception as e:
            logger.debug(f"关闭 WebSocket 失败：{e}")
        
        # 触发回调
        for callback in self._on_disconnect_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(connection_id, connection.session_id, reason)
                else:
                    callback(connection_id, connection.session_id, reason)
            except Exception as e:
                logger.error(f"OnDisconnect 回调失败：{e}")
        
        logger.info(f"WebSocket 连接断开：{connection_id} (reason={reason})")
    
    async def send_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ) -> bool:
        """
        发送消息到指定连接
        
        Args:
            connection_id: 连接 ID
            message: 消息字典
        
        Returns:
            bool: 是否发送成功
        """
        connection = self._connections.get(connection_id)
        
        if not connection or not connection.is_alive:
            logger.warning(f"连接不存在或已失效：{connection_id}")
            return False
        
        try:
            await connection.websocket.send_json(message)
            
            connection.message_count += 1
            connection.last_activity = time.time()
            self._stats.total_messages_sent += 1
            self._websocket_messages_counter += 1
            
            return True
        
        except WebSocketDisconnect:
            logger.info(f"客户端断开连接：{connection_id}")
            connection.is_alive = False
            await self.disconnect(connection_id, "Client disconnected")
            return False
        
        except Exception as e:
            logger.error(f"发送消息失败 {connection_id}: {str(e)}")
            self._websocket_errors_counter += 1
            return False
    
    async def receive_message(
        self,
        connection_id: str,
        timeout: float = 5.0,
    ) -> Optional[Dict[str, Any]]:
        """
        从指定连接接收消息
        
        Args:
            connection_id: 连接 ID
            timeout: 超时时间（秒）
        
        Returns:
            消息字典或 None
        """
        connection = self._connections.get(connection_id)
        
        if not connection or not connection.is_alive:
            return None
        
        try:
            data = await asyncio.wait_for(
                connection.websocket.receive_json(),
                timeout=timeout,
            )
            
            connection.message_count += 1
            connection.last_activity = time.time()
            self._stats.total_messages_received += 1
            
            # 触发消息回调
            for callback in self._on_message_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(connection_id, data)
                    else:
                        callback(connection_id, data)
                except Exception as e:
                    logger.error(f"OnMessage 回调失败：{e}")
            
            return data
        
        except asyncio.TimeoutError:
            return None
        
        except WebSocketDisconnect:
            logger.info(f"客户端断开连接：{connection_id}")
            connection.is_alive = False
            await self.disconnect(connection_id, "Client disconnected")
            return None
        
        except Exception as e:
            logger.error(f"接收消息失败 {connection_id}: {str(e)}")
            self._websocket_errors_counter += 1
            return None
    
    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None,
        session_id: Optional[str] = None,
    ) -> int:
        """
        广播消息
        
        Args:
            message: 消息字典
            exclude: 排除的连接 ID 集合
            session_id: 如果指定，则只广播到该会话
        
        Returns:
            成功发送的数量
        """
        exclude = exclude or set()
        sent_count = 0
        
        if session_id:
            # 只广播到指定会话
            connection_ids = self._session_connections.get(session_id, set())
        else:
            # 广播到所有连接
            connection_ids = set(self._connections.keys())
        
        for conn_id in connection_ids:
            if conn_id in exclude:
                continue
            
            if await self.send_message(conn_id, message):
                sent_count += 1
        
        logger.debug(f"广播消息：发送到 {sent_count}/{len(connection_ids)} 个连接")
        return sent_count
    
    async def health_check(self) -> Dict[str, Any]:
        """
        心跳检测
        
        Returns:
            健康检查结果
        """
        healthy_connections = 0
        unhealthy_connections = []
        
        for conn_id, connection in list(self._connections.items()):
            try:
                # 发送 ping
                await asyncio.wait_for(
                    connection.websocket.send_text("ping"),
                    timeout=5.0,
                )
                healthy_connections += 1
                connection.last_activity = time.time()
            
            except Exception as e:
                logger.warning(f"心跳检测失败 {conn_id}: {e}")
                unhealthy_connections.append(conn_id)
                connection.is_alive = False
        
        self._stats.last_health_check = time.time()
        
        result = {
            "healthy": healthy_connections,
            "unhealthy": len(unhealthy_connections),
            "total": len(self._connections),
            "timestamp": self._stats.last_health_check,
        }
        
        if unhealthy_connections:
            logger.warning(f"发现 {len(unhealthy_connections)} 个不健康连接")
        
        return result
    
    async def _heartbeat_loop(self):
        """心跳检测循环"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self.health_check()
                logger.debug(f"WeekSocket 心跳检测完成")
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"心跳检测循环失败：{e}")
    
    async def _cleanup_loop(self):
        """孤儿连接清理循环"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                current_time = time.time()
                orphaned_ids = []
                
                for conn_id, connection in list(self._connections.items()):
                    # 检查是否超时
                    if current_time - connection.last_activity > self.orphan_timeout:
                        orphaned_ids.append(conn_id)
                
                # 清理孤儿连接
                for conn_id in orphaned_ids:
                    logger.info(f"清理孤儿连接：{conn_id}")
                    await self.disconnect(conn_id, "Orphaned connection")
                    self._stats.orphaned_connections_cleaned += 1
                
                if orphaned_ids:
                    logger.info(f"清理了 {len(orphaned_ids)} 个孤儿连接")
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"清理循环失败：{e}")
    
    async def attempt_reconnect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: Optional[str] = None,
        previous_connection_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        尝试重新连接
        
        Args:
            websocket: WebSocket 实例
            session_id: 会话 ID
            user_id: 用户 ID
            previous_connection_id: 之前的连接 ID
        
        Returns:
            新连接 ID 或 None
        """
        # 获取之前的重连次数
        reconnect_count = 0
        if previous_connection_id:
            old_connection = self._connections.get(previous_connection_id)
            if old_connection:
                reconnect_count = old_connection.reconnect_count
        
        if reconnect_count >= self.max_reconnect_retries:
            logger.warning(f"达到最大重连次数：{previous_connection_id}")
            return None
        
        try:
            # 建立新连接
            new_connection_id = await self.connect(websocket, session_id, user_id)
            
            # 更新重连计数
            new_connection = self._connections.get(new_connection_id)
            if new_connection:
                new_connection.reconnect_count = reconnect_count + 1
            
            self._stats.reconnection_attempts += 1
            logger.info(f"重连成功：{new_connection_id} (attempt={reconnect_count + 1})")
            
            return new_connection_id
        
        except Exception as e:
            logger.error(f"重连失败：{str(e)}")
            return None
    
    def on_connect(self, callback: Callable):
        """注册连接回调"""
        self._on_connect_callbacks.append(callback)
    
    def on_disconnect(self, callback: Callable):
        """注册断开回调"""
        self._on_disconnect_callbacks.append(callback)
    
    def on_message(self, callback: Callable):
        """注册消息回调"""
        self._on_message_callbacks.append(callback)
    
    async def get_connection_stats(self) -> ConnectionStats:
        """获取连接统计信息"""
        return self._stats
    
    def get_stats_dict(self) -> Dict[str, Any]:
        """获取统计信息字典"""
        return {
            "total_connections": self._stats.total_connections,
            "active_connections": self._stats.active_connections,
            "max_connections_per_user": self._stats.max_connections_per_user,
            "total_messages_sent": self._stats.total_messages_sent,
            "total_messages_received": self._stats.total_messages_received,
            "orphaned_connections_cleaned": self._stats.orphaned_connections_cleaned,
            "reconnection_attempts": self._stats.reconnection_attempts,
            "last_health_check": self._stats.last_health_check,
            "prometheus_websocket_connections": self._websocket_connections_gauge,
            "prometheus_websocket_messages": self._websocket_messages_counter,
            "prometheus_websocket_errors": self._websocket_errors_counter,
        }
    
    async def close_all(self):
        """关闭所有连接"""
        connection_ids = list(self._connections.keys())
        
        for conn_id in connection_ids:
            await self.disconnect(conn_id, "Server shutdown")
        
        await self.stop_background_tasks()
        logger.info(f"已关闭所有 {len(connection_ids)} 个 WebSocket 连接")


# 全局单例
websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """获取 WebSocket 管理器单例"""
    global websocket_manager
    if websocket_manager is None:
        websocket_manager = WebSocketManager()
    return websocket_manager


async def init_websocket_manager():
    """初始化 WebSocket 管理器"""
    manager = get_websocket_manager()
    await manager.start_background_tasks()
    return manager


async def close_websocket_manager():
    """关闭 WebSocket 管理器"""
    manager = get_websocket_manager()
    await manager.close_all()
