"""
从招聘详情截图调用多模态大模型，提取与 JobRequirements 一致的结构化岗位信息。
"""

from __future__ import annotations

import base64
import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.llm_provider import LLMFactory, LLMProvider
from app.models.schemas import JobRequirements
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM = """你是招聘网站详情页的 OCR + 信息抽取助手。用户会上传一张或多张截图（可能含职位名、公司、薪资、地点、JD、标签、招聘者等）。
请只根据图片中可见文字作答，不要编造。输出必须是**单个 JSON 对象**（不要 Markdown 围栏以外的文字），字段如下：
{
  "title": "职位名称，必填",
  "company": "公司名或 null",
  "salary": "薪资范围字符串或 null",
  "location": "工作地点城市/区域或 null",
  "industry": "行业或 null",
  "company_scale": "公司规模或 null",
  "financing_stage": "融资阶段或 null",
  "tech_stack_tags": ["页面上的技能/技术标签，如 Python、LangChain、Redis 等，没有则 []"],
  "benefits": ["福利标签，如五险一金、下午茶、带薪年假等，没有则 []"],
  "responsibilities": ["岗位职责要点，多条"],
  "qualifications": ["任职要求要点，与 responsibilities 区分；没有则 []"],
  "required_skills": ["从正文提炼的必备能力/经验，多条"],
  "preferred_skills": ["加分项，没有则 []"],
  "experience_years": "经验要求原文或 null",
  "education_requirement": "学历要求原文或 null",
  "work_address": "详细办公地址或 null",
  "work_schedule": "工作时间、是否双休等或 null",
  "recruiter_name": "招聘者姓名或 null",
  "recruiter_title": "招聘者职位/公司与身份，如「HR」「某某公司·人事」或 null"
}
若图中为 Boss 直聘：技能标签入 tech_stack_tags；「岗位职责」入 responsibilities；「任职要求」入 qualifications；侧栏公司信息入 company_scale / financing_stage / industry。"""


_VISION_DEFAULT_MODEL: dict[LLMProvider, str] = {
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.BAILIAN: "qwen-image-edit-plus",
    LLMProvider.QWEN: "qwen-image-edit-plus",
    LLMProvider.ZHIPU: "glm-4v",
    LLMProvider.DEEPSEEK: "deepseek-chat",  # 无官方视觉接口，仅作占位，自动逻辑会跳过
}


def _openai_models() -> list[str]:
    return ["gpt-4o-mini", "gpt-4o"]


def _zhipu_models() -> list[str]:
    return ["glm-4v", "glm-4v-plus"]


def _dashscope_models() -> list[str]:
    """DashScope 上按顺序尝试的视觉相关模型（可经 JOB_SCREENSHOT_VISION_MODEL_FALLBACKS 追加）。"""
    defaults = [
        "qwen-image-edit-plus",
        "qwen-image-edit-plus-2025-10-30",
        "qwen-vl-plus",
        "qwen-vl-max",
    ]
    extra = (getattr(settings, "JOB_SCREENSHOT_VISION_MODEL_FALLBACKS", None) or "").strip()
    extras = [x.strip() for x in extra.split(",") if x.strip()]
    seen: set[str] = set()
    out: list[str] = []
    for m in defaults + extras:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _models_for_provider(prov: LLMProvider, primary: str) -> list[str]:
    if prov in (LLMProvider.BAILIAN, LLMProvider.QWEN):
        ordered = _dashscope_models()
    elif prov == LLMProvider.OPENAI:
        ordered = _openai_models()
    elif prov == LLMProvider.ZHIPU:
        ordered = _zhipu_models()
    else:
        return [primary]
    out: list[str] = []
    seen: set[str] = set()
    for m in [primary] + [x for x in ordered if x != primary]:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _uniq_pairs(pairs: list[tuple[LLMProvider, str]]) -> list[tuple[LLMProvider, str]]:
    seen: set[tuple[LLMProvider, str]] = set()
    out: list[tuple[LLMProvider, str]] = []
    for p, m in pairs:
        if (p, m) in seen:
            continue
        seen.add((p, m))
        out.append((p, m))
    return out


def _build_vision_attempt_chain() -> list[tuple[LLMProvider, str]]:
    """按顺序尝试 (provider, model)；默认优先百炼（BAILIAN）→ 通义（QWEN）→ OpenAI → 智谱。"""
    override_p = (getattr(settings, "JOB_SCREENSHOT_VISION_PROVIDER", None) or "").strip().lower()
    override_m = (getattr(settings, "JOB_SCREENSHOT_VISION_MODEL", None) or "").strip()

    if override_p:
        prov = LLMProvider(override_p)
        primary = override_m or _VISION_DEFAULT_MODEL.get(prov) or LLMFactory.get_default_model(prov)
        if prov != LLMProvider.OLLAMA and not LLMFactory.get_api_key(prov):
            raise ValueError(
                f"已指定 JOB_SCREENSHOT_VISION_PROVIDER={override_p}，但未配置对应 API Key。"
            )
        return _uniq_pairs([(prov, m) for m in _models_for_provider(prov, primary)])

    attempts: list[tuple[LLMProvider, str]] = []

    ds: LLMProvider | None
    if LLMFactory.get_api_key(LLMProvider.BAILIAN):
        ds = LLMProvider.BAILIAN
    elif LLMFactory.get_api_key(LLMProvider.QWEN):
        ds = LLMProvider.QWEN
    else:
        ds = None
    if ds is not None:
        for m in _dashscope_models():
            attempts.append((ds, m))

    if LLMFactory.get_api_key(LLMProvider.OPENAI):
        for m in _openai_models():
            attempts.append((LLMProvider.OPENAI, m))

    if LLMFactory.get_api_key(LLMProvider.ZHIPU):
        for m in _zhipu_models():
            attempts.append((LLMProvider.ZHIPU, m))

    if not attempts:
        try:
            main = LLMProvider(settings.LLM_PROVIDER.lower())
        except ValueError:
            main = LLMProvider.OPENAI
        main_vision = {
            LLMProvider.BAILIAN: "qwen-image-edit-plus",
            LLMProvider.QWEN: "qwen-image-edit-plus",
            LLMProvider.OPENAI: "gpt-4o-mini",
            LLMProvider.ZHIPU: "glm-4v",
        }
        if main in main_vision and LLMFactory.get_api_key(main):
            for m in _models_for_provider(main, main_vision[main]):
                attempts.append((main, m))

    attempts = _uniq_pairs(attempts)
    if not attempts:
        raise ValueError(
            "未配置可用的多模态模型：请在 .env 设置 OPENAI_API_KEY、BAILIAN_API_KEY、QWEN_API_KEY 或 ZHIPU_API_KEY 之一，"
            "或使用 JOB_SCREENSHOT_VISION_PROVIDER + JOB_SCREENSHOT_VISION_MODEL 指定。"
        )
    return attempts


def _parse_llm_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()
    return json.loads(text)


def _coerce_job_requirements(data: dict[str, Any]) -> JobRequirements:
    def slist(key: str) -> list[str]:
        v = data.get(key)
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            out: list[str] = []
            for x in v:
                if isinstance(x, str) and x.strip():
                    out.append(x.strip())
            return out
        return []

    def sopt(key: str) -> str | None:
        v = data.get(key)
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            return s or None
        return str(v).strip() or None

    title = (data.get("title") or "").strip()
    if not title:
        title = "未知岗位"

    return JobRequirements(
        title=title,
        company=sopt("company"),
        salary=sopt("salary"),
        location=sopt("location"),
        industry=sopt("industry"),
        company_scale=sopt("company_scale"),
        financing_stage=sopt("financing_stage"),
        responsibilities=slist("responsibilities"),
        qualifications=slist("qualifications"),
        required_skills=slist("required_skills"),
        preferred_skills=slist("preferred_skills"),
        tech_stack_tags=slist("tech_stack_tags"),
        benefits=slist("benefits"),
        experience_years=sopt("experience_years"),
        education_requirement=sopt("education_requirement"),
        work_address=sopt("work_address"),
        work_schedule=sopt("work_schedule"),
        recruiter_name=sopt("recruiter_name"),
        recruiter_title=sopt("recruiter_title"),
    )


async def extract_job_requirements_from_image(image_bytes: bytes, mime_type: str) -> JobRequirements:
    """
    调用多模态模型从图片提取 JobRequirements。
    mime_type 如 image/png、image/jpeg、image/webp。
    """
    chain = _build_vision_attempt_chain()
    last_exc: Exception | None = None

    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    safe_mime = mime_type if "/" in mime_type else "image/png"
    data_url = f"data:{safe_mime};base64,{b64}"

    human = HumanMessage(
        content=[
            {
                "type": "text",
                "text": "请根据截图提取岗位信息，输出约定格式的 JSON。",
            },
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
    )

    for prov, model in chain:
        try:
            llm = LLMFactory.create(provider=prov, model=model, temperature=0.1, max_tokens=8192)
            resp = await llm.ainvoke([SystemMessage(content=_SYSTEM), human])
            raw = resp.content
            if not isinstance(raw, str):
                raw = str(raw)

            try:
                payload = _parse_llm_json(raw)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("截图岗位 JSON 解析失败，尝试宽松提取: %s", e)
                m = re.search(r"\{[\s\S]*\}", raw)
                if not m:
                    raise ValueError(f"模型未返回有效 JSON: {raw[:400]}") from e
                payload = json.loads(m.group(0))

            logger.info("截图岗位识别成功: provider=%s model=%s", prov.value, model)
            return _coerce_job_requirements(payload)
        except Exception as e:
            last_exc = e
            logger.warning(
                "截图岗位识别失败，将尝试下一配置: provider=%s model=%s err=%s",
                prov.value,
                model,
                e,
            )

    msg = "所有截图识别模型均失败。"
    if last_exc:
        raise ValueError(f"{msg} 最后错误: {last_exc!s}") from last_exc
    raise ValueError(msg)
