"""
Custom Exceptions - 自定义异常

定义应用级别的自定义异常类，用于统一错误处理。
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """
    应用基础异常类
    
    所有自定义异常都应继承此类。
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为 JSON 响应格式"""
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            },
        }


class NotFoundException(AppException):
    """资源未找到异常"""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class ValidationException(AppException):
    """数据验证异常"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"validation_errors": errors or {}},
        )


class ExternalServiceException(AppException):
    """外部服务调用异常"""
    
    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        original_error: Optional[str] = None,
    ):
        details = {}
        if service_name:
            details["service"] = service_name
        if original_error:
            details["original_error"] = original_error
        
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
        )


class FileProcessingException(AppException):
    """文件处理异常"""
    
    def __init__(
        self,
        message: str = "File processing failed",
        filename: Optional[str] = None,
        file_type: Optional[str] = None,
    ):
        details = {}
        if filename:
            details["filename"] = filename
        if file_type:
            details["file_type"] = file_type
        
        super().__init__(
            message=message,
            status_code=400,
            error_code="FILE_PROCESSING_ERROR",
            details=details,
        )


class AIServiceException(AppException):
    """AI 服务异常"""
    
    def __init__(
        self,
        message: str = "AI service error",
        model: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        details = {}
        if model:
            details["model"] = model
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            status_code=503,
            error_code="AI_SERVICE_ERROR",
            details=details,
        )
