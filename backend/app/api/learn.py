"""
Learn API - 学无止境专栏

提供学习阶段与文章列表、详情接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.learning import LearningArticle, LearningPhase
from app.models.schemas import (
    LearningArticleDetail,
    LearningArticleListItem,
    LearningPhaseOut,
    SuccessResponse,
)

router = APIRouter()


@router.get("/phases", response_model=SuccessResponse)
async def list_phases(db: AsyncSession = Depends(get_db)):
    """
    返回全部学习阶段及所属文章（不含 content_md）。
    """
    result = await db.execute(
        select(LearningPhase)
        .options(selectinload(LearningPhase.articles))
        .order_by(LearningPhase.sort_order, LearningPhase.id)
    )
    phases = result.scalars().all()
    out = []
    for p in phases:
        articles = [
            LearningArticleListItem(
                id=a.id,
                phase_id=a.phase_id,
                title=a.title,
                sort_order=a.sort_order,
                external_url=a.external_url or None,
                created_at=a.created_at,
            )
            for a in sorted(p.articles, key=lambda x: (x.sort_order, x.id))
        ]
        out.append(
            LearningPhaseOut(
                id=p.id,
                title=p.title,
                subtitle=p.subtitle or "",
                sort_order=p.sort_order,
                articles=articles,
                created_at=p.created_at,
            )
        )
    return SuccessResponse(success=True, message="OK", data={"phases": out})


@router.get("/articles/{article_id}", response_model=SuccessResponse)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """
    返回单篇文章详情（含 content_md）。
    """
    result = await db.execute(
        select(LearningArticle).where(LearningArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    detail = LearningArticleDetail(
        id=article.id,
        phase_id=article.phase_id,
        title=article.title,
        sort_order=article.sort_order,
        content_md=article.content_md or "",
        external_url=article.external_url or None,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )
    return SuccessResponse(success=True, message="OK", data=detail)
