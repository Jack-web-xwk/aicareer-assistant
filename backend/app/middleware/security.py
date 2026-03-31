"""
安全中间件

提供以下安全功能：
1. 请求体大小限制（限制 10MB）
2. 全局异常处理（不暴露内部错误栈信息）
"""

import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.utils.logger import get_logger

logger = get_logger(__name__)

# 请求体大小限制：10MB
MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    请求体大小限制中间件

    拒绝超过限制大小的请求，防止大文件上传导致内存耗尽。
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # 检查 Content-Length 头
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
                if size > MAX_REQUEST_BODY_SIZE:
                    logger.warning(
                        "请求体过大，已拒绝: %s bytes (限制: %s bytes), 路径: %s",
                        size,
                        MAX_REQUEST_BODY_SIZE,
                        request.url.path,
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "success": False,
                            "message": f"请求体过大，最大允许 {MAX_REQUEST_BODY_SIZE // (1024 * 1024)}MB",
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """
    全局异常处理中间件

    捕获所有未处理的异常，返回统一格式的错误响应，
    不暴露内部错误栈信息，避免信息泄露。
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            # 记录完整的错误信息到服务端日志
            logger.error(
                "未处理的异常: %s, 路径: %s, 方法: %s",
                str(e),
                request.url.path,
                request.method,
                exc_info=True,
            )

            # 对客户端只返回通用错误信息，不暴露内部细节
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "服务器内部错误，请稍后重试",
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "服务器内部错误，请稍后重试",
                    },
                },
            )
