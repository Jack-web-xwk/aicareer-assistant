"""
LLM Prompts - 多维度面试评估提示词模板

提供面试评估各个环节的 prompt 模板。
"""

from typing import List, Dict, Any


# ==================== Multi-Dimensional Assessment Prompts ====================

MULTI_DIMENSION_ASSESSMENT_PROMPT = """你是一位专业的多维度面试评估专家。请基于候选人的面试表现，从以下 5 个维度进行全面评估：

评估维度及权重：
1. 技术深度 (technical_depth) - 25%: 对核心技术概念的深入理解程度
2. 技术广度 (technical_breadth) - 20%: 知识面的宽度和跨领域理解
3. 沟通表达 (communication) - 20%: 表达的清晰度、逻辑性和专业性
4. 逻辑思维 (logic) - 20%: 分析问题、推理和论证的能力
5. 问题解决 (problem_solving) - 15%: 面对问题的分析能力和解决方案质量

面试信息：
- 岗位：{job_role}
- 技术栈：{tech_stack}
- 面试记录：
{interview_record}

请以 JSON 格式输出评估结果：
{{
    "dimension_scores": [
        {{
            "dimension_id": "technical_depth",
            "score": 85,
            "feedback": "详细反馈...",
            "key_points": ["要点 1", "要点 2"],
            "weight": 0.25
        }},
        // ... 其他 4 个维度
    ],
    "total_score": 87.5,
    "overall_feedback": "整体评价...",
    "strengths": ["优势 1", "优势 2"],
    "weaknesses": ["不足 1", "不足 2"]
}}

要求：
- 每个维度的评分必须有具体依据
- feedback 要具体、可操作，避免空泛
- key_points 列出 3-5 个关键观察点
- 总分使用加权平均计算"""


REALTIME_FEEDBACK_PROMPT = """你是一位实时面试反馈助手。请基于候选人当前的回答，提供简洁、即时的反馈。

当前面试信息：
- 岗位：{job_role}
- 当前问题：{current_question}
- 候选人回答：{current_answer}
- 已回答问题数：{question_count}/{max_questions}

请用 JSON 格式输出即时反馈（需要在 200ms 内完成）：
{{
    "overall_feedback": "一句话点评（20 字以内）",
    "suggestions": ["建议 1", "建议 2"],
    "encouragement": "鼓励性话语"
}}

要求：
- 反馈必须简洁、 actionable
- suggestions 最多 2 条
- 语气友好、专业"""


LEARNING_SUGGESTION_PROMPT = """你是一位个性化学习规划师。请基于面试评估结果，为候选人制定学习计划。

候选人信息：
- 目标岗位：{job_role}
- 经验水平：{experience_level}
- 薄弱维度：{weakness_dimension}
- 具体问题：{weakness_description}
- 其他维度得分：{other_dimensions}

请生成 JSON 格式的学习建议：
{{
    "dimension": "{weakness_dimension}",
    "weakness": "具体薄弱点描述",
    "learning_resources": [
        {{
            "title": "资源标题",
            "type": "book|course|video|article|practice",
            "url": "https://...",
            "platform": "平台名称",
            "estimated_hours": 10,
            "difficulty": "beginner|intermediate|advanced"
        }}
    ],
    "action_items": [
        "第 1 周：学习内容...",
        "第 2 周：实践练习...",
        "第 3 周：项目实战..."
    ],
    "priority": "high|medium|low",
    "estimated_hours": 40
}}

要求：
- 推荐真实有效的学习资源（Coursera/Udemy/官方文档等）
- action_items 要具体、可执行、有时间规划
- 优先级根据岗位匹配度确定"""


# ==================== Dimension-Specific Analysis Prompts ====================

TECHNICAL_DEPTH_ANALYSIS_PROMPT = """请评估候选人在以下回答中展现的技术深度。

考察重点：
- 核心概念的理解是否深入
- 是否了解底层原理和实现机制
- 能否解释"为什么"而不仅是"是什么"
- 是否有性能优化和最佳实践的考虑

面试记录：
{interview_record}

技术栈范围：{tech_stack}

请从以下角度评分（0-100）：
1. 概念理解的准确性
2. 原理掌握的深入程度
3. 实际应用的熟练度
4. 性能优化的考虑

输出 JSON：
{{
    "score": 85,
    "feedback": "详细反馈",
    "key_points": ["观察点 1", "观察点 2", "观察点 3"],
    "evidence": ["具体回答证据 1", "具体回答证据 2"]
}}"""


COMMUNICATION_EVAL_PROMPT = """请评估候选人在面试中的沟通表达能力。

考察重点：
- 表达是否清晰、准确
- 逻辑是否连贯
- 是否能用恰当的方式解释复杂概念
- 倾听和理解问题的能力
- 专业术语的使用是否准确

面试对话记录：
{conversation_history}

请从以下角度评分（0-100）：
1. 表达清晰度
2. 逻辑连贯性
3. 概念解释能力
4. 专业术语使用
5. 倾听理解能力

输出 JSON：
{{
    "score": 80,
    "feedback": "详细反馈",
    "key_points": ["观察点 1", "观察点 2", "观察点 3"],
    "examples": ["具体例子 1", "具体例子 2"]
}}"""


PROBLEM_SOLVING_EVAL_PROMPT = """请评估候选人的问题解决能力。

考察重点：
- 面对问题的第一反应和分析思路
- 是否能拆解复杂问题
- 考虑问题的全面性（边界条件、异常处理等）
- 解决方案的可行性和优化意识
- 在引导下的学习和调整能力

面试中的问题与回答：
{problem_solving_records}

请从以下角度评分（0-100）：
1. 问题分析能力
2. 方案设计的合理性
3. 边界条件的考虑
4. 优化意识
5. 学习调整能力

输出 JSON：
{{
    "score": 78,
    "feedback": "详细反馈",
    "key_points": ["观察点 1", "观察点 2", "观察点 3"],
    "solution_approach": "候选人的解题思路",
    "areas_to_improve": ["改进建议 1", "改进建议 2"]
}}"""


# ==================== Helper Functions ====================

def format_interview_record(scores: List[Dict[str, Any]]) -> str:
    """格式化面试记录用于 prompt"""
    records = []
    for s in scores:
        record = f"Q{s.get('question_number', '?')}: {s.get('question', '')}\n"
        record += f"A: {s.get('answer', '')}\n"
        record += f"评分：{s.get('score', 0)}\n"
        record += f"反馈：{s.get('feedback', '')}"
        records.append(record)
    return "\n\n".join(records)


def format_conversation_history(messages: List[Dict[str, Any]]) -> str:
    """格式化对话历史用于 prompt"""
    lines = []
    for msg in messages:
        role = "面试官" if msg.get("role") == "assistant" else "候选人"
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)
