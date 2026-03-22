"""
Learning Seed - 学无止境专栏初始数据

启动时若 learning_phases 表为空则自动写入。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import LearningArticle, LearningPhase

PLACEHOLDER_MD = "内容即将上线，敬请期待。"

PHASES_DATA = [
    {"title": "前置准备篇：Cursor + 大模型开发环境一站式搭建", "subtitle": "环境搭建", "articles": [
        "专栏前言：我的大模型学习之路，以及为什么用 Cursor 做开发",
        "学习路径规划：6 大阶段，30+ 篇内容，从入门到架构师的完整路线",
        "Cursor 保姆级教程：从安装到高级用法，大模型开发必备技巧全解",
        "环境搭建：Python+Git+Docker + 本地大模型，一站式部署，零踩坑",
    ]},
    {"title": "阶段一：大模型底层基础（筑基篇）", "subtitle": "筑基篇", "articles": [
        "一文搞懂 Transformer：从核心原理到对大模型发展的决定性影响",
        "大模型核心概念扫盲：Token、嵌入、上下文窗口、自回归生成全解",
        "第一课：用 Cursor 写第一行大模型调用代码，实现单轮问答",
        "开源模型 vs 闭源 API：选型对比、成本测算、适用场景全解",
    ]},
    {"title": "阶段二：对话系统开发（入门篇）", "subtitle": "入门篇", "articles": [
        "多轮对话核心逻辑：为什么不能纯文本拼接历史对话？",
        "无框架纯 Python 实现：结构化对话历史管理，角色隔离 + 滑动窗口",
        "本地大模型对话适配：开源模型 Chat Template 踩坑全解",
        "对话历史持久化：JSON+MySQL 双方案，支持跨会话恢复",
    ]},
    {"title": "阶段三：提示词工程与指令对齐（进阶篇）", "subtitle": "进阶篇", "articles": [
        "企业级提示词黄金公式：从只会提问到精准控制模型输出",
        "Cursor 专属提示词技巧：用 @文件、@库、@符号提升 10 倍效率",
        "核心技巧实战：少样本提示、思维链 CoT、幻觉抑制、格式约束",
        "提示词调优方法论：迭代优化、边界测试、场景化模板沉淀",
    ]},
    {"title": "阶段四：RAG 检索增强生成（核心篇）", "subtitle": "核心篇", "articles": [
        "RAG 全流程原理解析：解决大模型幻觉、知识滞后的核心方案",
        "从零搭建 RAG 系统：纯 Python 实现，无 LangChain 依赖",
        "向量数据库全解：Milvus 从部署到调优，检索策略全场景适配",
        "RAG 进阶优化：重排序、混合检索、多查询扩展、chunk 调优实战",
        "GraphRAG 升级：解决多跳问答、长文档推理的企业级方案",
    ]},
    {"title": "阶段五：大模型微调与私有化部署（深度篇）", "subtitle": "深度篇", "articles": [
        "微调核心认知：什么时候用 RAG？什么时候必须微调？",
        "轻量化微调实战：QLoRA 实现本地 7B 模型微调，消费级显卡可跑",
        "微调全流程：数据集准备→训练→模型合并→效果评估→落地部署",
        "本地大模型推理优化：量化、vLLM 加速、高并发服务部署",
    ]},
    {"title": "阶段六：Agent 智能体与企业级落地（终极篇）", "subtitle": "终极篇", "articles": [
        "Agent 核心原理：从「会聊天」到「会干活」的核心逻辑",
        "从零搭建 Agent 系统：工具调用、任务规划、多轮执行全实现",
        "多智能体协作：主从架构、团队模式、通信机制、任务调度实战",
        "企业级 Agent 落地：安全管控、人机交互、持久化、可观测性全方案",
        "毕业实战项目：用 Cursor 开发一套完整的企业级客服 Agent 系统",
    ]},
    {"title": "番外篇：行业落地案例", "subtitle": "番外", "articles": [
        "电商行业：大模型智能客服与用户运营系统落地",
        "金融行业：合规问答与投研分析系统落地",
        "制造业：生产文档问答与故障排查系统落地",
        "教育行业：个性化学习助手与题库解析系统落地",
    ]},
]


async def seed_learning_if_empty(session: AsyncSession) -> int:
    """若 learning_phases 表为空则写入数据，返回写入的文章数。"""
    result = await session.execute(select(LearningPhase).limit(1))
    if result.scalar_one_or_none():
        return 0
    total = 0
    for idx, phase_data in enumerate(PHASES_DATA):
        phase = LearningPhase(
            title=phase_data["title"],
            subtitle=phase_data.get("subtitle", ""),
            sort_order=idx,
        )
        session.add(phase)
        await session.flush()
        for art_idx, title in enumerate(phase_data["articles"]):
            session.add(LearningArticle(
                phase_id=phase.id,
                title=title,
                sort_order=art_idx,
                content_md=PLACEHOLDER_MD,
            ))
            total += 1
    await session.commit()
    return total
