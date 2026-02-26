"""
Resume Parser Service - 简历解析服务

支持 PDF 和 Word 格式简历的文本提取。
"""

import io
from pathlib import Path
from typing import Optional, Union

import pdfplumber
from docx import Document

from app.core.exceptions import FileProcessingException


class ResumeParser:
    """
    简历解析器
    
    支持 PDF（使用 pdfplumber）和 Word（使用 python-docx）格式。
    """
    
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}
    
    def __init__(self):
        pass
    
    def parse(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_content: Optional[bytes] = None,
        file_type: Optional[str] = None,
    ) -> str:
        """
        解析简历文件，提取文本内容
        
        Args:
            file_path: 文件路径（与 file_content 二选一）
            file_content: 文件二进制内容（与 file_path 二选一）
            file_type: 文件类型（当使用 file_content 时必须提供）
        
        Returns:
            提取的文本内容
        
        Raises:
            FileProcessingException: 文件处理失败
        """
        try:
            if file_path:
                path = Path(file_path)
                ext = path.suffix.lower()
                
                if ext not in self.SUPPORTED_EXTENSIONS:
                    raise FileProcessingException(
                        f"Unsupported file type: {ext}",
                        filename=path.name,
                        file_type=ext,
                    )
                
                if ext == ".pdf":
                    return self._parse_pdf_file(path)
                else:
                    return self._parse_docx_file(path)
            
            elif file_content and file_type:
                if file_type.lower() in ("pdf", ".pdf", "application/pdf"):
                    return self._parse_pdf_bytes(file_content)
                elif file_type.lower() in ("docx", ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
                    return self._parse_docx_bytes(file_content)
                else:
                    raise FileProcessingException(
                        f"Unsupported file type: {file_type}",
                        file_type=file_type,
                    )
            else:
                raise FileProcessingException(
                    "Either file_path or (file_content, file_type) must be provided"
                )
        
        except FileProcessingException:
            raise
        except Exception as e:
            raise FileProcessingException(
                f"Failed to parse resume: {str(e)}",
                filename=str(file_path) if file_path else None,
            )
    
    def _parse_pdf_file(self, file_path: Path) -> str:
        """解析 PDF 文件"""
        text_parts = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    def _parse_pdf_bytes(self, content: bytes) -> str:
        """解析 PDF 字节内容"""
        text_parts = []
        
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    def _parse_docx_file(self, file_path: Path) -> str:
        """解析 Word 文件"""
        doc = Document(file_path)
        text_parts = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        # 提取表格内容
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_parts.append(" | ".join(row_text))
        
        return "\n".join(text_parts)
    
    def _parse_docx_bytes(self, content: bytes) -> str:
        """解析 Word 字节内容"""
        doc = Document(io.BytesIO(content))
        text_parts = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        # 提取表格内容
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_parts.append(" | ".join(row_text))
        
        return "\n".join(text_parts)


# 便捷函数
def parse_resume_file(
    file_path: Optional[Union[str, Path]] = None,
    file_content: Optional[bytes] = None,
    file_type: Optional[str] = None,
) -> str:
    """
    解析简历文件的便捷函数
    
    Args:
        file_path: 文件路径
        file_content: 文件二进制内容
        file_type: 文件类型
    
    Returns:
        提取的文本内容
    """
    parser = ResumeParser()
    return parser.parse(file_path=file_path, file_content=file_content, file_type=file_type)
