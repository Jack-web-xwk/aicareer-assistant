"""
ATS 兼容性评分服务

提供简历的 ATS（Applicant Tracking System，申请人跟踪系统）兼容性评分，
帮助用户优化简历以通过自动化筛选系统的审核。
"""

import re
from collections import Counter
from typing import List, Set


# 常见停用词列表（英文 + 部分中文高频词）
STOP_WORDS: Set[str] = {
    # 英文停用词
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must", "shall", "can",
    "that", "this", "these", "those", "it", "its", "he", "she", "they",
    "them", "their", "we", "our", "you", "your", "i", "my", "me",
    "not", "no", "nor", "if", "then", "than", "so", "very", "just",
    "about", "above", "after", "again", "all", "also", "am", "any",
    "because", "before", "between", "both", "each", "few", "get",
    "here", "how", "into", "more", "most", "new", "now", "only",
    "other", "out", "over", "own", "same", "some", "still", "such",
    "there", "through", "under", "up", "what", "when", "where",
    "which", "while", "who", "whom", "why", "work", "working",
    "ability", "including", "using", "including", "well", "experience",
    "etc", "like",
    # 中文停用词
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她",
}

# 标准简历章节关键词
SECTION_KEYWORDS = {
    "education": ["教育", "education", "学历", "学业", "学校", "university", "college", "degree", "学位"],
    "work_experience": [
        "工作经历", "工作经验", "work experience", "professional experience",
        "employment", "工作", "实习", "internship", "职业经历",
    ],
    "skills": [
        "技能", "skills", "技术栈", "tech stack", "专业技能",
        "核心技能", "能力", "competencies", "技术能力",
    ],
    "projects": [
        "项目", "projects", "项目经历", "project experience",
        "项目经验", "作品", "portfolio", "开源",
    ],
}


def _extract_keywords(text: str, min_length: int = 2) -> List[str]:
    """
    从文本中提取关键词

    参数:
        text: 输入文本
        min_length: 关键词最小长度

    返回:
        关键词列表（去除停用词和纯数字）
    """
    # 先将中文分词：在每个中文字符前后加空格，然后统一按空白分词
    text = re.sub(r"([\u4e00-\u9fff])", r" \1 ", text)
    # 提取所有字母和中文字符组成的 token
    tokens = re.findall(r"[a-zA-Z\u4e00-\u9fff][a-zA-Z0-9\u4e00-\u9fff\-\.+#]*", text.lower())
    # 过滤停用词和过短的词
    return [t for t in tokens if t not in STOP_WORDS and len(t) >= min_length]


def _calculate_keyword_match(resume_tokens: List[str], job_tokens: List[str]) -> tuple:
    """
    计算关键词匹配度

    参数:
        resume_tokens: 简历关键词列表
        job_tokens: 岗位描述关键词列表

    返回:
        (匹配度分数, 已匹配关键词列表, 缺失关键词列表)
    """
    if not job_tokens:
        return 100.0, [], []

    # 统计岗位关键词频率，取 Top N 作为目标关键词
    job_counter = Counter(job_tokens)
    # 取出现次数最多的关键词，最多 50 个
    top_keywords = [word for word, _ in job_counter.most_common(50)]

    resume_set = set(resume_tokens)

    matched = []
    missing = []

    for keyword in top_keywords:
        # 检查是否包含该关键词（支持子串匹配）
        if any(keyword in r_token or r_token in keyword for r_token in resume_set):
            matched.append(keyword)
        else:
            missing.append(keyword)

    if not top_keywords:
        return 100.0, [], []

    # 基于 Top 关键词的匹配比例计算分数
    match_ratio = len(matched) / len(top_keywords) if top_keywords else 1.0
    score = match_ratio * 100.0
    return round(score, 1), matched, missing


def _calculate_format_score(resume_text: str) -> tuple:
    """
    计算格式兼容性评分

    检查简历是否包含标准章节，ATS 系统通常偏好结构化的简历。

    参数:
        resume_text: 简历文本

    返回:
        (格式评分, 已存在的章节列表, 缺失的章节列表)
    """
    text_lower = resume_text.lower()
    found_sections = []
    missing_sections = []

    for section_name, keywords in SECTION_KEYWORDS.items():
        found = any(kw.lower() in text_lower for kw in keywords)
        if found:
            found_sections.append(section_name)
        else:
            missing_sections.append(section_name)

    total_sections = len(SECTION_KEYWORDS)
    if total_sections == 0:
        return 100.0, [], []

    # 基础分 = 已有章节的比例
    score = (len(found_sections) / total_sections) * 100.0

    # 额外检查：是否有明确的分节标记（冒号、标题行等）
    has_section_headers = bool(re.search(
        r"(?:^|\n)\s*(?:\d+[\.\)、\.])?\s*[\u4e00-\u9fffA-Z][\u4e00-\u9fffA-Za-z\s]{1,20}[：:]",
        resume_text,
    ))
    if has_section_headers:
        score = min(100.0, score + 10.0)

    return round(score, 1), found_sections, missing_sections


def _calculate_length_score(resume_text: str) -> tuple:
    """
    计算长度适当性评分

    一般建议简历 1-3 页（约 500-2000 个中文字或 300-1500 个英文单词）。

    参数:
        resume_text: 简历文本

    返回:
        (长度评分, 建议列表)
    """
    # 统计字符数（中英文混合）
    char_count = len(resume_text.strip())
    # 估算词数（中文按字计算，英文按空格分词）
    word_count = len(re.findall(r"[\u4e00-\u9fff]|[a-zA-Z]+", resume_text))
    suggestions = []

    if char_count < 200:
        # 太短
        score = max(0, 40.0 - (200 - char_count) * 0.2)
        suggestions.append("简历内容过短，建议补充更多详细信息，包括工作经历和项目经验。")
    elif word_count <= 1500:
        # 1-3 页的理想范围
        score = 100.0
    elif word_count <= 2500:
        # 稍微偏长
        score = 80.0
        suggestions.append("简历略长，建议精简至 1-3 页，突出核心经历。")
    elif word_count <= 4000:
        # 明显偏长
        score = 60.0
        suggestions.append("简历过长，建议大幅精简，删除不相关的经历描述。")
    else:
        # 非常长
        score = 40.0
        suggestions.append("简历严重超标，ATS 系统可能无法正确解析，建议压缩至 3 页以内。")

    return round(score, 1), suggestions


def calculate_ats_score(resume_text: str, job_description: str) -> dict:
    """
    ATS 兼容性评分

    从关键词匹配、格式兼容性、长度适当性三个维度评估简历的 ATS 兼容性。

    参数:
        resume_text: 简历文本内容
        job_description: 目标岗位描述

    返回:
        包含以下字段的字典:
        - overall_score: 总分 (0-100)
        - keyword_match: 关键词匹配度 (0-100)
        - format_score: 格式兼容性 (0-100)
        - length_score: 长度适当性 (0-100)
        - missing_keywords: 缺失的关键词列表
        - matched_keywords: 已匹配的关键词列表
        - suggestions: 改进建议列表
    """
    # 1. 提取关键词
    resume_tokens = _extract_keywords(resume_text)
    job_tokens = _extract_keywords(job_description)

    # 2. 关键词匹配评分
    keyword_score, matched, missing = _calculate_keyword_match(resume_tokens, job_tokens)

    # 3. 格式评分
    format_score, found_sections, missing_sections = _calculate_format_score(resume_text)

    # 4. 长度评分
    length_score, length_suggestions = _calculate_length_score(resume_text)

    # 5. 汇总建议
    suggestions = list(length_suggestions)

    # 关键词相关建议
    if missing:
        missing_str = ", ".join(missing[:10])
        if len(missing) > 10:
            missing_str += f" 等共 {len(missing)} 个"
        suggestions.append(f"建议在简历中补充以下关键词: {missing_str}")

    # 格式相关建议
    if missing_sections:
        section_names = {
            "education": "教育背景",
            "work_experience": "工作经历",
            "skills": "技能",
            "projects": "项目经历",
        }
        missing_names = [section_names.get(s, s) for s in missing_sections]
        suggestions.append(f"建议添加以下章节: {', '.join(missing_names)}")

    if not suggestions:
        suggestions.append("简历 ATS 兼容性良好！")

    # 6. 计算总分（加权平均：关键词 50%，格式 30%，长度 20%）
    overall_score = round(
        keyword_score * 0.5 + format_score * 0.3 + length_score * 0.2,
        1,
    )

    return {
        "overall_score": overall_score,
        "keyword_match": keyword_score,
        "format_score": format_score,
        "length_score": length_score,
        "missing_keywords": missing,
        "matched_keywords": matched,
        "suggestions": suggestions,
    }
