"""
全局异常处理：保证任意未处理异常与 HTTP 错误均写入应用日志（文件 + 控制台）。

说明：Starlette 按异常类型匹配处理器；须先注册 HTTPException / RequestValidationError，
再注册通用 Exception，避免 4xx/422 被误记为 500。
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse

from app.utils.logger import get_logger

_log = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        _log.warning(
            "422 请求体验证失败 | %s %s | errors=%s",
            request.method,
            request.url.path,
            exc.errors(),
        )
        return await request_validation_exception_handler(request, exc)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        if exc.status_code >= 500:
            _log.error(
                "HTTP %s | %s %s | detail=%s",
                exc.status_code,
                request.method,
                request.url.path,
                exc.detail,
            )
        else:
            _log.warning(
                "HTTP %s | %s %s | detail=%s",
                exc.status_code,
                request.method,
                request.url.path,
                exc.detail,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        _log.exception(
            "未捕获异常（返回 500）| %s %s | %s",
            request.method,
            request.url.path,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
