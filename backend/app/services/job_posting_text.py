"""将爬取的岗位结构格式化为 LLM 输入文本与 JSON 快照（供 API 与后台任务共用）。"""

import json

from app.models.schemas import JobRequirements


def job_desc_text_from_requirements(job_info: JobRequirements, job_url: str) -> str:
    """将爬取结果格式化为给 LLM 的岗位说明文本。"""
    lines = [
        f"岗位名称：{job_info.title}",
        f"公司：{job_info.company or '未知'}",
        f"应聘岗位链接：{job_url}",
        f"薪资：{job_info.salary or '未标注'}",
        f"工作地点：{job_info.location or '未标注'}",
    ]
    if job_info.industry:
        lines.append(f"行业：{job_info.industry}")
    if job_info.company_scale:
        lines.append(f"公司规模：{job_info.company_scale}")
    if job_info.financing_stage:
        lines.append(f"融资阶段：{job_info.financing_stage}")
    if job_info.tech_stack_tags:
        lines.append("技能标签：" + "、".join(job_info.tech_stack_tags))
    if job_info.benefits:
        lines.append("福利：" + "、".join(job_info.benefits))
    lines.append("岗位职责：")
    lines.extend("- " + r for r in job_info.responsibilities)
    if job_info.qualifications:
        lines.append("任职要求：")
        lines.extend("- " + r for r in job_info.qualifications)
    lines.append("必备技能：")
    lines.extend("- " + s for s in job_info.required_skills)
    lines.append("加分技能：")
    lines.extend("- " + s for s in job_info.preferred_skills)
    if job_info.work_address:
        lines.append(f"办公地址：{job_info.work_address}")
    if job_info.work_schedule:
        lines.append(f"工作时间：{job_info.work_schedule}")
    if job_info.recruiter_name or job_info.recruiter_title:
        lines.append(
            "招聘方联系人："
            + " ".join(
                x
                for x in (job_info.recruiter_name or "", job_info.recruiter_title or "")
                if x
            )
        )
    lines.append(f"经验要求：{job_info.experience_years or '未指定'}")
    lines.append(f"学历要求：{job_info.education_requirement or '未指定'}")
    return "\n".join(lines)


def job_snapshot_json(job_info: JobRequirements, job_url: str) -> str:
    """结构化快照，供历史结果展示。"""
    d = job_info.model_dump()
    d["source_url"] = job_url
    return json.dumps(d, ensure_ascii=False)
