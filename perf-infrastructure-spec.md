# 性能优化设计文档

## 概述

本文档详细描述 AI Career Assistant 项目的性能优化方案，包括 Redis 会话存储、音频流式处理和 WebSocket 连接池三个核心改进。

---

## Redis 集成方案

### RedisClient 类设计

```python
# backend/app/core/redis_client.py
import json
import gzip
from typing import Optional, List, Dict, Any
import redis.asyncio as redis
from app.agents.interview_agent import InterviewState

class RedisClient:
    """Redis 客户端封装 - 用于面试会话持久化"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "interview:",
        default_ttl: int = 86400,  # 24 小时
    ):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self._redis: Optional[redis.Redis] = None
        self._fallback_to_memory = False
        self._memory_store: Dict[str, InterviewState] = {}
    
    async def connect(self) -> bool:
        try:
            self._redis = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=False)
            await self._redis.ping()
            return True
        except Exception as e:
            print(f"Redis 连接失败，启用内存降级：{e}")
            self._fallback_to_memory = True
            return False
    
    def _make_key(self, session_id: str) -> str:
        return f"{self.key_prefix}{session_id}:state"
    
    async def save_session(self, session_id: str, state: InterviewState, ttl: Optional[int] = None) -> bool:
        if self._fallback_to_memory:
            self._memory_store[session_id] = state
            return True
        try:
            json_str = json.dumps(state, ensure_ascii=False)
            compressed = gzip.compress(json_str.encode("utf-8"))
            key = self._make_key(session_id)
            await self._redis.set(key, compressed, ex=ttl or self.default_ttl)
            return True
        except Exception as e:
            print(f"保存会话失败：{e}")
            self._fallback_to_memory = True
            self._memory_store[session_id] = state
            return False
    
    async def get_session(self, session_id: str) -> Optional[InterviewState]:
        if self._fallback_to_memory:
            return self._memory_store.get(session_id)
        try:
            key = self._make_key(session_id)
            compressed = await self._redis.get(key)
            if not compressed:
                return None
            json_str = gzip.decompress(compressed).decode("utf-8")
            state: InterviewState = json.loads(json_str)
            return state
        except Exception as e:
            print(f"获取会话失败：{e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        if self._fallback_to_memory:
            self._memory_store.pop(session_id, None)
            return True
        try:
            key = self._make_key(session_id)
            await self._redis.delete(key)
            return True
        except Exception as e:
            print(f"删除会话失败：{e}")
            return False
    
    async def list_active_sessions(self) -> List[InterviewState]:
        if self._fallback_to_memory:
            return list(self._memory_store.values())
        try:
            pattern = f"{self.key_prefix}*state"
            sessions = []
            async for key in self._redis.scan_iter(match=pattern):
                compressed = await self._redis.get(key)
                if compressed:
                    json_str = gzip.decompress(compressed).decode("utf-8")
                    state = json.loads(json_str)
                    sessions.append(state)
            return sessions
        except Exception as e:
            print(f"列出会话失败：{e}")
            return []
    
    async def close(self):
        if self._redis:
            await self._redis.close()
```

### 配置更新

```python
# backend/app/core/config.py
REDIS_URL: str = "redis://localhost:6379/0"
REDIS_ENABLED: bool = True
REDIS_FALLBACK_TO_MEMORY: bool = True
```

---

## 迁移计划

### Phase 1: 双写模式 (Day 1-2)
1. 创建 RedisClient 类
2. 修改 start_interview 接口：同时写入内存和 Redis
3. 修改 submit_answer 接口：同时更新内存和 Redis

### Phase 2: 验证一致性 (Day 3)
- 编写测试用例对比内存和 Redis 中的数据
- 监控 Redis 操作延迟 (P95 < 50ms)

### Phase 3: 切换读操作 (Day 4)
- 优先从 Redis 读取
- Redis miss 时回退到内存并异步回填

### Phase 4: 移除内存存储 (Day 5)
- 完全移除 active_sessions 字典
- 所有读写都通过 Redis

---

## 音频流式架构

### 流式 STT 流程
```
前端录音 → WebSocket 分片 (5s/chunk) → Celery 任务 → Whisper API → 增量文本拼接
```

### 流式 TTS 流程
```
LLM 流式输出 → 文本分块器 → Celery 任务 → TTS API → WebSocket 推送
```

### Celery 任务定义

```python
# backend/app/tasks/audio_tasks.py
from celery import Celery

celery_app = Celery("audio_tasks", broker="redis://localhost:6379/1", backend="redis://localhost:6379/1")

@celery_app.task(bind=True, max_retries=3)
def transcribe_audio_chunk(self, audio_base64: str, chunk_index: int) -> dict:
    from app.services.audio_processor import AudioProcessor
    processor = AudioProcessor()
    transcript = processor.transcribe(audio_base64=audio_base64, language="zh")
    return {"chunk_index": chunk_index, "transcript": transcript, "status": "success"}

@celery_app.task(bind=True, max_retries=3)
def synthesize_text_chunk(self, text: str, voice: str = "alloy") -> dict:
    from app.services.audio_processor import AudioProcessor
    processor = AudioProcessor()
    audio_base64 = processor.synthesize_to_base64(text=text, voice=voice)
    return {"audio_base64": audio_base64, "text_length": len(text), "status": "success"}
```

---

## WebSocket 连接池设计

### 连接管理器

```python
# backend/app/core/websocket_manager.py
import asyncio
from typing import Dict, Set
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self, heartbeat_interval: float = 30.0):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._heartbeat_interval = heartbeat_interval
    
    async def connect(self, session_id: str, websocket: WebSocket) -> bool:
        await websocket.accept()
        if session_id not in self._connections:
            self._connections[session_id] = set()
        self._connections[session_id].add(websocket)
        return True
    
    async def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self._connections:
            self._connections[session_id].discard(websocket)
            if not self._connections[session_id]:
                del self._connections[session_id]
            try:
                await websocket.close()
            except:
                pass
    
    async def broadcast_to_session(self, session_id: str, message: dict) -> int:
        if session_id not in self._connections:
            return 0
        success_count = 0
        for websocket in self._connections[session_id]:
            try:
                await websocket.send_json(message)
                success_count += 1
            except:
                pass
        return success_count
    
    async def send_heartbeat(self):
        while True:
            await asyncio.sleep(self._heartbeat_interval)
            for session_id, connections in list(self._connections.items()):
                for ws in connections:
                    try:
                        await ws.send_json({"type": "ping"})
                        response = await asyncio.wait_for(ws.receive_json(), timeout=10.0)
                        if response.get("type") != "pong":
                            raise ValueError("Invalid pong")
                    except:
                        await self.disconnect(session_id, ws)
```

### 心跳协议
```json
// Server -> Client
{"type": "ping", "timestamp": 1711526400}

// Client -> Server
{"type": "pong", "timestamp": 1711526400}
```

---

## 监控指标

| 指标名称 | 当前值 | 目标值 |
|---------|--------|--------|
| Redis 命中率 | N/A | > 95% |
| 音频处理 P95 延迟 | 8.6s | < 2s |
| WebSocket 连接成功率 | ~95% | > 99% |
| 会话恢复成功率 | 0% | > 98% |

---

## 依赖更新

```txt
redis>=5.0.0
celery>=5.3.0
prometheus-client>=0.19.0
```

---

*文档生成时间：2026-03-27*
