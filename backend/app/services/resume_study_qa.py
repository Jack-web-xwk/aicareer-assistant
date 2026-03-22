"""
Resume study QA - 根据单次简历优化任务上下文生成面试准备 / 学习问答
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.llm_provider import LLMFactory
from app.models.schemas import StudyQaItem
from app.utils.logger import get_logger

logger = get_logger(__name__)

MAX_RESUME_CHARS = 14000
MAX_JOB_DESC_CHARS = 8000


def _truncate(text: str, max_len: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 20] + "\n…(已截断)"


def _parse_llm_json(text: str) -> List[Dict[str, Any]]:
    """Parse JSON object with \"items\" array or bare array from LLM output."""
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        raw = fence.group(1).strip()
    obj = json.loads(raw)
    if isinstance(obj, dict) and "items" in obj:
        items = obj["items"]
    elif isinstance(obj, list):
        items = obj
    else:
        raise ValueError("expected JSON object with 'items' or a JSON array")
    if not isinstance(items, list):
        raise ValueError("'items' must be a list")
    return items


async def generate_resume_study_qa(
    *,
    target_job_title: Optional[str],
    job_description: Optional[str],
    match_analysis: Optional[Dict[str, Any]],
    optimized_resume: str,
    max_items: int,
) -> List[StudyQaItem]:
    """
    Call LLM to produce study / interview-prep Q&A for this optimization task.
    """
    resume_excerpt = _truncate(optimized_resume, MAX_RESUME_CHARS)
    job_excerpt = _truncate(job_description or "", MAX_JOB_DESC_CHARS)
    ma_json = (
        json.dumps(match_analysis, ensure_ascii=False, indent=2)
        if match_analysis
        else "{}"
    )

    system = SystemMessage(
        content=(
            "You are a career coach helping candidates prepare for technical interviews. "
            "Output MUST be valid JSON only, no markdown outside JSON. "
            "Questions must be grounded in the job context and resume content provided; "
            "do not invent confidential employer information. "
            "Use Simplified Chinese for all user-facing strings."
        )
    )
    user = HumanMessage(
        content=f"""根据以下「目标岗位 + 匹配分析 + 优化后简历」生成 {max_items} 条学习/面试准备问答，帮助候选人巩固知识、准备可能面试问题。

要求：
1. 覆盖：岗位核心技能、匹配分析中的「需补充技能」、项目/经历深挖、常见行为/场景题（与岗位相关）。
2. 每条包含 topic（短标签）、question（清晰问题）、answer_hint（答题要点或思路，非背诵标准答案）。
3. 严格输出 JSON 对象，格式如下（不要其它文字）：
{{"items":[{{"topic":"...","question":"...","answer_hint":"..."}},...]}}

--- 目标岗位标题 ---
{target_job_title or "（未填）"}

--- 岗位描述（节选） ---
{job_excerpt or "（无）"}

--- 匹配分析（JSON） ---
{ma_json}

--- 优化后简历（Markdown，节选） ---
{resume_excerpt or "（无）"}
"""
    )

    model = settings.RESUME_STUDY_QA_MODEL.strip() or None
    qa_provider = settings.RESUME_STUDY_QA_PROVIDER.strip() or "bailian"
    llm = LLMFactory.create_for_resume(
        provider=qa_provider or None,
        model=model,
        temperature=0.4,
    )
    response = await llm.ainvoke([system, user])
    content = getattr(response, "content", None) or str(response)
    if not isinstance(content, str):
        content = str(content)

    try:
        raw_items = _parse_llm_json(content)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("study_qa JSON parse failed: %s; raw=%s", e, content[:800])
        raise ValueError("模型返回非合法 JSON") from e

    out: List[StudyQaItem] = []
    for i, row in enumerate(raw_items[:max_items]):
        if not isinstance(row, dict):
            continue
        try:
            out.append(
                StudyQaItem(
                    topic=str(row.get("topic") or "综合"),
                    question=str(row.get("question") or "").strip(),
                    answer_hint=str(row.get("answer_hint") or row.get("answerHint") or "").strip(),
                )
            )
        except Exception as e:
            logger.debug("skip invalid study_qa row %s: %s", i, e)
            continue

    valid = [x for x in out if x.question and x.answer_hint]
    if not valid:
        raise ValueError("未能从模型输出解析出有效问答条目")
    return valid
