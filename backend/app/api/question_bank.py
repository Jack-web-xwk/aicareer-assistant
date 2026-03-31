"""
Question Bank API - 题库管理接口

提供题库的 CRUD 操作、搜索、统计等功能。
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import (
    SuccessResponse,
    QuestionBankCreate,
    QuestionBankUpdate,
    QuestionBankResponse,
    QuestionBankSearchRequest,
    QuestionBankStatistics,
    QuestionBankBatchImportRequest,
    QuestionBankBatchImportResponse,
)
from app.services.question_service import QuestionService

router = APIRouter()


@router.get("/categories", response_model=SuccessResponse)
async def get_categories(db: AsyncSession = Depends(get_db)):
    """
    获取所有分类及题目数量
    
    返回题库中所有的分类及其对应的题目数量统计。
    """
    service = QuestionService(db)
    stats = await service.get_statistics()
    
    # 提取分类统计
    categories = [
        {"category": cat, "count": count}
        for cat, count in stats["category_stats"].items()
    ]
    
    return SuccessResponse(
        success=True,
        message="获取分类成功",
        data={"categories": categories, "total": stats["total_count"]}
    )


@router.get("/questions", response_model=SuccessResponse)
async def search_questions(
    keyword: Optional[str] = Query(None, description="关键词"),
    category: Optional[str] = Query(None, description="分类"),
    difficulty: Optional[str] = Query(None, description="难度级别", pattern="^(easy|medium|hard)$"),
    tech_stack: Optional[str] = Query(None, description="技术栈（逗号分隔）"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    limit: int = Query(default=20, ge=1, le=100, description="数量限制"),
    db: AsyncSession = Depends(get_db),
):
    """
    搜索题目
    
    支持多种过滤条件：
    - keyword: 关键词搜索（匹配问题描述）
    - category: 分类过滤
    - difficulty: 难度级别 (easy/medium/hard)
    - tech_stack: 技术栈（逗号分隔的字符串）
    
    返回分页结果。
    """
    # 解析技术栈参数
    tech_stack_list = None
    if tech_stack:
        tech_stack_list = [t.strip() for t in tech_stack.split(",") if t.strip()]
    
    service = QuestionService(db)
    questions, total = await service.search_questions(
        keyword=keyword,
        category=category,
        difficulty=difficulty,
        tech_stack=tech_stack_list,
        offset=offset,
        limit=limit,
    )
    
    # 转换为响应格式
    questions_data = [q.to_dict() for q in questions]
    
    return SuccessResponse(
        success=True,
        message="搜索成功",
        data={
            "questions": questions_data,
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    )


@router.post("/questions", response_model=SuccessResponse)
async def create_question(
    question_data: QuestionBankCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新题目
    
    需要提供：
    - category: 分类名称
    - question: 问题描述
    - difficulty: 难度级别（可选，默认 medium）
    - tech_stack: 技术栈列表（可选）
    - expected_points: 期望回答要点（可选）
    - follow_up_questions: 追问问题列表（可选）
    """
    service = QuestionService(db)
    
    # 验证分类
    if not question_data.category or not question_data.category.strip():
        raise HTTPException(status_code=400, detail="分类名称不能为空")
    
    # 验证难度级别
    if question_data.difficulty not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail="难度级别必须是 easy/medium/hard")
    
    try:
        question = await service.create_question(question_data.model_dump())
        return SuccessResponse(
            success=True,
            message="题目创建成功",
            data=QuestionBankResponse.model_validate(question).model_dump()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败：{str(e)}")


@router.get("/questions/{question_id}", response_model=SuccessResponse)
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取题目详情
    
    根据 ID 获取单个题目的完整信息。
    """
    service = QuestionService(db)
    question = await service.get_question_by_id(question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    return SuccessResponse(
        success=True,
        message="获取成功",
        data=QuestionBankResponse.model_validate(question).model_dump()
    )


@router.put("/questions/{question_id}", response_model=SuccessResponse)
async def update_question(
    question_id: int,
    update_data: QuestionBankUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    更新题目
    
    可以更新题目的任意字段（部分更新）。
    """
    service = QuestionService(db)
    
    # 过滤掉 None 值
    data = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if not data:
        raise HTTPException(status_code=400, detail="没有提供更新数据")
    
    question = await service.update_question(question_id, data)
    
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    return SuccessResponse(
        success=True,
        message="题目更新成功",
        data=QuestionBankResponse.model_validate(question).model_dump()
    )


@router.delete("/questions/{question_id}", response_model=SuccessResponse)
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    删除题目（软删除）
    
    将题目标记为非活动状态，而非物理删除。
    """
    service = QuestionService(db)
    success = await service.delete_question(question_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    return SuccessResponse(
        success=True,
        message="题目已删除",
        data={"id": question_id}
    )


@router.get("/statistics", response_model=SuccessResponse)
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """
    获取题库统计数据
    
    返回：
    - 总题目数
    - 按分类统计
    - 按难度统计
    - 平均使用次数
    - 平均得分
    - 热门题目 TOP5
    """
    service = QuestionService(db)
    stats = await service.get_statistics()
    
    return SuccessResponse(
        success=True,
        message="获取统计成功",
        data=stats
    )


@router.post("/questions/batch-import", response_model=SuccessResponse)
async def batch_import_questions(
    import_request: QuestionBankBatchImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    批量导入题目
    
    支持一次性导入多个题目，自动跳过重复题目（根据分类 + 问题描述判断）。
    
    请求格式：
    ```json
    {
        "questions": [
            {
                "category": "后端开发",
                "tech_stack": ["Python", "FastAPI"],
                "difficulty": "medium",
                "question": "请解释 FastAPI 的工作原理",
                "expected_points": ["异步处理", "类型提示", "性能优势"],
                "follow_up_questions": ["与 Flask 有什么区别？"]
            }
        ],
        "skip_duplicates": true
    }
    ```
    """
    service = QuestionService(db)
    
    if not import_request.questions:
        raise HTTPException(status_code=400, detail="题目列表不能为空")
    
    result = await service.batch_import(
        questions=import_request.questions,
        skip_duplicates=import_request.skip_duplicates,
    )
    
    return SuccessResponse(
        success=True,
        message=f"导入完成：成功{result['imported']}个，跳过{result['skipped']}个，失败{result['failed']}个",
        data=QuestionBankBatchImportResponse(**result).model_dump()
    )


# ==================== 便捷函数 ====================

def get_random_question_for_interview(
    category: str,
    tech_stack: List[str],
    difficulty: str,
    service: QuestionService,
) -> Optional[Dict[str, Any]]:
    """
    为面试随机抽取一道题目
    
    Args:
        category: 分类
        tech_stack: 技术栈
        difficulty: 难度
        service: 题库服务实例
    
    Returns:
        题目字典，如果题库为空则返回 None
    """
    import asyncio
    
    async def _fetch():
        questions = await service.get_by_category(
            category=category,
            tech_stack=tech_stack,
            difficulty=difficulty,
            limit=10,
        )
        
        if not questions:
            # 尝试放宽条件：只按分类和难度
            questions = await service.get_by_category(
                category=category,
                difficulty=difficulty,
                limit=10,
            )
        
        if not questions:
            # 再放宽：只按分类
            questions = await service.get_by_category(
                category=category,
                limit=10,
            )
        
        if questions:
            import random
            selected = random.choice(questions)
            return selected.to_dict()
        
        return None
    
    # 在异步环境中使用
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_fetch())


__all__ = ["router"]
