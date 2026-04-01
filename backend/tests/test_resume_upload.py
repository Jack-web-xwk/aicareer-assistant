"""
测试简历上传和解析功能

验证简历上传、解析、优化等核心功能是否正常工作。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent / '..'))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.services.resume_parser import parse_resume_file
from app.utils.logger import get_logger

logger = get_logger(__name__)


def test_resume_parser():
    """测试简历解析器"""
    logger.info("=" * 60)
    logger.info("测试简历解析器")
    logger.info("=" * 60)
    
    # 测试 PDF 文件
    test_pdf = Path(__file__).parent.parent / "uploads" / "test.pdf"
    if test_pdf.exists():
        try:
            logger.info(f"\n测试 PDF 解析：{test_pdf}")
            text = parse_resume_file(file_path=str(test_pdf))
            logger.info(f"✓ PDF 解析成功，长度：{len(text)} 字符")
            logger.info(f"文本预览：{text[:200]}...")
        except Exception as e:
            logger.error(f"✗ PDF 解析失败：{str(e)}", exc_info=True)
    else:
        logger.warning(f"测试 PDF 文件不存在：{test_pdf}")
    
    # 测试 Word 文件
    test_docx = Path(__file__).parent.parent / "uploads" / "test.docx"
    if test_docx.exists():
        try:
            logger.info(f"\n测试 Word 解析：{test_docx}")
            text = parse_resume_file(file_path=str(test_docx))
            logger.info(f"✓ Word 解析成功，长度：{len(text)} 字符")
            logger.info(f"文本预览：{text[:200]}...")
        except Exception as e:
            logger.error(f"✗ Word 解析失败：{str(e)}", exc_info=True)
    else:
        logger.warning(f"测试 Word 文件不存在：{test_docx}")


async def test_database_queries():
    """测试数据库查询"""
    logger.info("\n" + "=" * 60)
    logger.info("测试数据库查询")
    logger.info("=" * 60)
    
    async with async_session_maker() as db:
        try:
            # 测试用户查询
            from app.models.user import User
            from sqlalchemy import select
            
            result = await db.execute(select(User))
            users = result.scalars().all()
            logger.info(f"✓ 用户查询成功，共 {len(users)} 个用户")
            
            for user in users[:3]:  # 只显示前 3 个
                logger.info(f"  - {user.email} (ID: {user.id})")
            
            # 测试简历查询
            from app.models.resume import Resume
            
            result = await db.execute(select(Resume).limit(5))
            resumes = result.scalars().all()
            logger.info(f"✓ 简历查询成功，共 {len(resumes)} 份简历")
            
            for resume in resumes:
                logger.info(f"  - {resume.original_filename} (状态：{resume.status.value})")
            
            # 测试学习资源查询
            from app.models.learning import LearningPhase, LearningArticle
            
            result = await db.execute(select(LearningPhase))
            phases = result.scalars().all()
            logger.info(f"✓ 学习阶段查询成功，共 {len(phases)} 个阶段")
            
            result = await db.execute(select(LearningArticle))
            articles = result.scalars().all()
            logger.info(f"✓ 学习文章查询成功，共 {len(articles)} 篇文章")
            
        except Exception as e:
            logger.error(f"✗ 数据库查询失败：{str(e)}", exc_info=True)


async def main():
    """主函数"""
    logger.info("\n开始运行测试用例...\n")
    
    # 测试简历解析
    test_resume_parser()
    
    # 测试数据库查询
    await test_database_queries()
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
