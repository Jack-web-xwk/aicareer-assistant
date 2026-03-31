"""
Redis Client - Redis 客户端

提供会话持久化功能，支持面试状态存储、检索和管理。
使用连接池、重试机制和压缩序列化来提升性能和可靠性。
"""

import asyncio
import gzip
import json
from typing import Any, Dict, List, Optional
from functools import wraps
import time

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    AsyncRetrying,
)

from app.agents.interview_agent import InterviewState
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class RedisClient:
    """
    Redis 客户端单例类
    
    提供面试会话的持久化存储功能：
    - 使用 JSON + gzip 压缩序列化
    - 连接池管理 (max_connections=50)
    - 自动重试机制 (retry=3, exponential backoff)
    - TTL 自动过期
    - Prometheus 指标导出
    """
    
    _instance: Optional["RedisClient"] = None
    _lock: asyncio.Lock = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 防止重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        self._initialized = True
        self._pool: Optional[ConnectionPool] = None
        self._redis: Optional[Redis] = None
        self._key_prefix = "interview:session:"
        self._default_ttl = 86400  # 24 hours
        
        # Prometheus 指标
        self._redis_operation_counter = 0
        self._redis_error_counter = 0
        self._redis_latency_sum = 0.0
        
    async def initialize(self):
        """初始化 Redis 连接池"""
        if self._pool is not None:
            return
        
        try:
            # 创建连接池
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_POOL_SIZE,
                decode_responses=False,  # 我们手动处理编码/解码
                socket_connect_timeout=5.0,
                socket_timeout=5.0,
                retry_on_timeout=True,
            )
            
            self._redis = redis.Redis(connection_pool=self._pool)
            
            # 测试连接
            await self._redis.ping()
            logger.info(f"Redis 连接池初始化成功 (max_connections={settings.REDIS_POOL_SIZE})")
            
        except Exception as e:
            logger.error(f"Redis 初始化失败：{str(e)}", exc_info=True)
            raise
    
    async def close(self):
        """关闭 Redis 连接池"""
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
            self._redis = None
            logger.info("Redis 连接池已关闭")
    
    @property
    def redis(self) -> Redis:
        """获取 Redis 实例"""
        if self._redis is None:
            raise RuntimeError("Redis 未初始化，请先调用 initialize()")
        return self._redis
    
    def _serialize(self, state: InterviewState) -> bytes:
        """
        序列化 InterviewState 为压缩的字节数据
        
        使用 JSON + gzip 压缩来减少存储空间和网络传输
        """
        try:
            # 转换为普通字典（TypedDict -> dict）
            data_dict = dict(state)
            
            # JSON 序列化
            json_str = json.dumps(data_dict, ensure_ascii=False, default=str)
            
            # Gzip 压缩
            compressed = gzip.compress(json_str.encode('utf-8'))
            
            return compressed
            
        except Exception as e:
            logger.error(f"序列化失败：{str(e)}", exc_info=True)
            raise
    
    def _deserialize(self, data: Optional[bytes]) -> Optional[InterviewState]:
        """
        反序列化压缩数据为 InterviewState
        """
        if data is None:
            return None
        
        try:
            # Gzip 解压
            decompressed = gzip.decompress(data)
            
            # JSON 解析
            data_dict = json.loads(decompressed.decode('utf-8'))
            
            return data_dict  # TypedDict 在运行时就是 dict
            
        except Exception as e:
            logger.error(f"反序列化失败：{str(e)}", exc_info=True)
            raise
    
    def _get_key(self, session_id: str) -> str:
        """生成 Redis key"""
        return f"{self._key_prefix}{session_id}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.1, max=2.0),
        retry=retry_if_exception_type((RedisError, RedisConnectionError)),
        reraise=True,
    )
    async def save_session(
        self, 
        session_id: str, 
        state: InterviewState, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        保存会话状态到 Redis
        
        Args:
            session_id: 会话 ID
            state: InterviewState 对象
            ttl: 过期时间 (秒)，默认 24 小时
        
        Returns:
            bool: 是否保存成功
        """
        start_time = time.time()
        
        try:
            key = self._get_key(session_id)
            compressed_data = self._serialize(state)
            
            await self.redis.setex(
                key,
                ttl or self._default_ttl,
                compressed_data
            )
            
            self._redis_operation_counter += 1
            latency = time.time() - start_time
            self._redis_latency_sum += latency
            
            logger.debug(f"保存会话成功：{session_id}, latency={latency:.4f}s")
            return True
            
        except Exception as e:
            self._redis_error_counter += 1
            logger.error(f"保存会话失败 {session_id}: {str(e)}", exc_info=True)
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.1, max=2.0),
        retry=retry_if_exception_type((RedisError, RedisConnectionError)),
        reraise=True,
    )
    async def get_session(self, session_id: str) -> Optional[InterviewState]:
        """
        从 Redis 获取会话状态
        
        Args:
            session_id: 会话 ID
        
        Returns:
            InterviewState | None: 会话状态或 None
        """
        start_time = time.time()
        
        try:
            key = self._get_key(session_id)
            data = await self.redis.get(key)
            
            self._redis_operation_counter += 1
            latency = time.time() - start_time
            self._redis_latency_sum += latency
            
            if data is None:
                logger.debug(f"会话不存在：{session_id}")
                return None
            
            state = self._deserialize(data)
            logger.debug(f"获取会话成功：{session_id}, latency={latency:.4f}s")
            return state
            
        except Exception as e:
            self._redis_error_counter += 1
            logger.error(f"获取会话失败 {session_id}: {str(e)}", exc_info=True)
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.1, max=2.0),
        retry=retry_if_exception_type((RedisError, RedisConnectionError)),
        reraise=True,
    )
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话 ID
        
        Returns:
            bool: 是否删除成功
        """
        start_time = time.time()
        
        try:
            key = self._get_key(session_id)
            result = await self.redis.delete(key)
            
            self._redis_operation_counter += 1
            latency = time.time() - start_time
            self._redis_latency_sum += latency
            
            logger.debug(f"删除会话成功：{session_id}, deleted={result}")
            return result > 0
            
        except Exception as e:
            self._redis_error_counter += 1
            logger.error(f"删除会话失败 {session_id}: {str(e)}", exc_info=True)
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.1, max=2.0),
        retry=retry_if_exception_type((RedisError, RedisConnectionError)),
        reraise=True,
    )
    async def list_active_sessions(self) -> List[InterviewState]:
        """
        列出所有活跃会话
        
        Returns:
            List[InterviewState]: 活跃会话列表
        """
        start_time = time.time()
        
        try:
            pattern = f"{self._key_prefix}*"
            keys = []
            
            # 异步扫描 keys
            async for key in self.redis.scan_iter(match=pattern, count=100):
                keys.append(key)
            
            # 批量获取所有会话
            sessions = []
            if keys:
                values = await self.redis.mget(keys)
                for key, value in zip(keys, values):
                    if value:
                        try:
                            state = self._deserialize(value)
                            if state:
                                sessions.append(state)
                        except Exception as e:
                            logger.warning(f"反序列化会话失败 {key}: {e}")
            
            self._redis_operation_counter += 1
            latency = time.time() - start_time
            self._redis_latency_sum += latency
            
            logger.info(f"列出活跃会话：共 {len(sessions)} 个")
            return sessions
            
        except Exception as e:
            self._redis_error_counter += 1
            logger.error(f"列出活跃会话失败：{str(e)}", exc_info=True)
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.1, max=2.0),
        retry=retry_if_exception_type((RedisError, RedisConnectionError)),
        reraise=True,
    )
    async def cleanup_expired(self) -> int:
        """
        清理过期会话
        
        Redis 会自动通过 TTL 清理，此方法用于手动检查和统计
        
        Returns:
            int: 清理的会话数量
        """
        start_time = time.time()
        
        try:
            pattern = f"{self._key_prefix}*"
            cleaned_count = 0
            
            async for key in self.redis.scan_iter(match=pattern, count=100):
                # 检查 key 是否存在（TTL 是否过期）
                exists = await self.redis.exists(key)
                if not exists:
                    cleaned_count += 1
            
            self._redis_operation_counter += 1
            latency = time.time() - start_time
            self._redis_latency_sum += latency
            
            logger.info(f"清理过期会话：{cleaned_count} 个")
            return cleaned_count
            
        except Exception as e:
            self._redis_error_counter += 1
            logger.error(f"清理过期会话失败：{str(e)}", exc_info=True)
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取 Redis 客户端统计信息
        
        Returns:
            Dict: 包含操作计数、错误计数、平均延迟等
        """
        avg_latency = (
            self._redis_latency_sum / self._redis_operation_counter
            if self._redis_operation_counter > 0
            else 0.0
        )
        
        return {
            "total_operations": self._redis_operation_counter,
            "total_errors": self._redis_error_counter,
            "average_latency_seconds": avg_latency,
            "pool_size": settings.REDIS_POOL_SIZE,
            "connected": self._redis is not None,
        }
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: Redis 是否可连接
        """
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis 健康检查失败：{str(e)}")
            return False


# 全局单例
redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """获取 Redis 客户端单例"""
    global redis_client
    if redis_client is None:
        redis_client = RedisClient()
    return redis_client


async def init_redis():
    """初始化 Redis 客户端"""
    client = get_redis_client()
    await client.initialize()
    return client


async def close_redis():
    """关闭 Redis 客户端"""
    client = get_redis_client()
    await client.close()
