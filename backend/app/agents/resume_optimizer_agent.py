"""
Resume Optimizer Agent - 简历优化智能体

使用 LangGraph 实现简历智能优化流程：
1. 提取简历信息
2. 分析岗位需求
3. 内容匹配
4. 生成优化简历

支持多种 LLM 提供商：OpenAI, DeepSeek, 智谱GLM, Ollama, Anthropic, Qwen
"""

from typing import Any, Dict, List, Optional, TypedDict, Union

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.core.llm_provider import LLMFactory, LLMProvider, create_llm


class ResumeOptimizerState(TypedDict):
    """
    简历优化智能体状态
    
    包含整个优化流程中需要传递的所有数据。
    """
    # 输入
    resume_text: str                          # 原始简历文本
    job_desc: str                             # 岗位描述文本
    job_url: Optional[str]                    # 岗位链接
    
    # 中间状态
    extracted_info: Optional[Dict[str, Any]]  # 提取的简历信息
    job_requirements: Optional[Dict[str, Any]] # 解析的岗位需求
    matched_content: Optional[Dict[str, Any]]  # 匹配分析结果
    
    # 输出
    optimized_resume: Optional[str]           # 优化后的简历（Markdown）
    
    # 元数据
    error: Optional[str]                      # 错误信息
    current_step: str                         # 当前步骤


class ResumeOptimizerAgent:
    """
    简历优化智能体
    
    使用 LangGraph 构建的简历优化流程：
    extract_resume_info → analyze_job_requirements → match_content → generate_optimized_resume
    
    支持多种 LLM 提供商：
    - OpenAI (默认)
    - DeepSeek (deepseek-chat, deepseek-reasoner)
    - 智谱 GLM (glm-4, glm-4-flash)
    - Ollama (本地模型)
    - Anthropic Claude
    - 通义千问 Qwen
    """
    
    def __init__(
        self,
        provider: Optional[Union[LLMProvider, str]] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **llm_kwargs: Any,
    ):
        """
        初始化智能体
        
        Args:
            provider: LLM 提供商 (openai/deepseek/zhipu/ollama/anthropic/qwen)
            model: 使用的模型名称
            api_key: API Key (可选，默认从环境变量读取)
            **llm_kwargs: 传递给 LLM 的其他参数
        """
        self.provider = provider
        self.model = model
        
        # 使用 LLM Factory 创建简历优化专用 LLM (较低温度，更精准)
        self.llm: BaseChatModel = LLMFactory.create_for_resume(
            provider=provider,
            model=model,
            api_key=api_key,
            **llm_kwargs,
        )
        
        # 构建图
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 状态图"""
        # 创建状态图
        workflow = StateGraph(ResumeOptimizerState)
        
        # 添加节点
        workflow.add_node("extract_resume_info", self._extract_resume_info)
        workflow.add_node("analyze_job_requirements", self._analyze_job_requirements)
        workflow.add_node("match_content", self._match_content)
        workflow.add_node("generate_optimized_resume", self._generate_optimized_resume)
        
        # 设置入口点
        workflow.set_entry_point("extract_resume_info")
        
        # 添加边（线性流程）
        workflow.add_edge("extract_resume_info", "analyze_job_requirements")
        workflow.add_edge("analyze_job_requirements", "match_content")
        workflow.add_edge("match_content", "generate_optimized_resume")
        workflow.add_edge("generate_optimized_resume", END)
        
        # 编译图
        return workflow.compile()
    
    async def _extract_resume_info(self, state: ResumeOptimizerState) -> Dict[str, Any]:
        """
        节点1: 提取简历信息
        
        使用 LLM 从简历文本中提取结构化信息：
        - 个人信息
        - 教育背景
        - 工作经历
        - 项目经验
        - 技术栈
        """
        system_prompt = """你是一个专业的简历分析师。请从简历文本中提取以下结构化信息，以 JSON 格式返回：

{
    "name": "姓名",
    "contact": {
        "email": "邮箱",
        "phone": "电话",
        "location": "所在地"
    },
    "summary": "个人简介/求职意向",
    "education": [
        {
            "school": "学校名称",
            "degree": "学位",
            "major": "专业",
            "start_date": "开始时间",
            "end_date": "结束时间",
            "gpa": "GPA（如有）",
            "highlights": ["亮点1", "亮点2"]
        }
    ],
    "work_experience": [
        {
            "company": "公司名称",
            "title": "职位",
            "start_date": "开始时间",
            "end_date": "结束时间",
            "responsibilities": ["职责1", "职责2"],
            "achievements": ["成就1", "成就2"]
        }
    ],
    "projects": [
        {
            "name": "项目名称",
            "role": "担任角色",
            "description": "项目描述",
            "technologies": ["技术1", "技术2"],
            "achievements": ["成果1", "成果2"]
        }
    ],
    "skills": {
        "programming_languages": ["语言1", "语言2"],
        "frameworks": ["框架1", "框架2"],
        "tools": ["工具1", "工具2"],
        "soft_skills": ["软技能1", "软技能2"]
    },
    "certifications": ["证书1", "证书2"],
    "languages": ["语言1", "语言2"]
}

请仔细分析简历内容，提取所有可用信息。如果某项信息不存在，使用 null。"""

        human_prompt = f"请分析以下简历并提取信息：\n\n{state['resume_text']}"
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析 JSON 响应
            import json
            content = response.content
            # 尝试从响应中提取 JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            extracted_info = json.loads(json_str)
            
            return {
                "extracted_info": extracted_info,
                "current_step": "extract_resume_info",
            }
        
        except Exception as e:
            return {
                "error": f"简历信息提取失败: {str(e)}",
                "current_step": "extract_resume_info",
            }
    
    async def _analyze_job_requirements(self, state: ResumeOptimizerState) -> Dict[str, Any]:
        """
        节点2: 分析岗位需求
        
        使用 LLM 解析岗位描述，提取：
        - 核心职责
        - 必备技能
        - 优先技能
        """
        system_prompt = """你是一个专业的招聘分析师。请从岗位描述中提取以下结构化信息，以 JSON 格式返回：

{
    "title": "岗位名称",
    "core_responsibilities": ["核心职责1", "核心职责2"],
    "required_skills": {
        "technical": ["必备技术技能1", "必备技术技能2"],
        "soft": ["必备软技能1", "必备软技能2"]
    },
    "preferred_skills": {
        "technical": ["加分技术技能1", "加分技术技能2"],
        "soft": ["加分软技能1", "加分软技能2"]
    },
    "experience_requirement": "经验要求描述",
    "education_requirement": "学历要求",
    "key_keywords": ["关键词1", "关键词2"],
    "team_culture": "团队文化/工作环境描述（如有）"
}

请仔细分析岗位描述，准确区分必备和加分条件。"""

        human_prompt = f"请分析以下岗位描述并提取需求：\n\n{state['job_desc']}"
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]
            
            response = await self.llm.ainvoke(messages)
            
            import json
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            job_requirements = json.loads(json_str)
            
            return {
                "job_requirements": job_requirements,
                "current_step": "analyze_job_requirements",
            }
        
        except Exception as e:
            return {
                "error": f"岗位需求分析失败: {str(e)}",
                "current_step": "analyze_job_requirements",
            }
    
    async def _match_content(self, state: ResumeOptimizerState) -> Dict[str, Any]:
        """
        节点3: 内容匹配
        
        将简历内容与岗位需求进行匹配分析，标记需要强化的部分。
        """
        system_prompt = """你是一个专业的简历优化顾问。请分析候选人简历与目标岗位的匹配程度，以 JSON 格式返回：

{
    "match_score": 75,  // 0-100 的匹配度评分
    "matched_skills": ["匹配的技能1", "匹配的技能2"],
    "missing_skills": ["缺失的技能1", "缺失的技能2"],
    "experience_match": {
        "score": 80,
        "analysis": "经验匹配分析"
    },
    "education_match": {
        "score": 90,
        "analysis": "学历匹配分析"
    },
    "strengths": ["优势1", "优势2"],
    "areas_to_improve": ["需要改进的方面1", "需要改进的方面2"],
    "content_to_highlight": ["应该突出的经历1", "应该突出的项目2"],
    "keywords_to_add": ["应该添加的关键词1", "关键词2"],
    "suggestions": ["优化建议1", "优化建议2"]
}"""

        extracted_info = state.get("extracted_info", {})
        job_requirements = state.get("job_requirements", {})
        
        human_prompt = f"""请分析以下简历与岗位的匹配情况：

## 简历信息
{extracted_info}

## 岗位需求
{job_requirements}

请进行详细的匹配分析。"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]
            
            response = await self.llm.ainvoke(messages)
            
            import json
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            matched_content = json.loads(json_str)
            
            return {
                "matched_content": matched_content,
                "current_step": "match_content",
            }
        
        except Exception as e:
            return {
                "error": f"内容匹配分析失败: {str(e)}",
                "current_step": "match_content",
            }
    
    async def _generate_optimized_resume(self, state: ResumeOptimizerState) -> Dict[str, Any]:
        """
        节点4: 生成优化简历
        
        基于匹配分析结果，使用 STAR 法则生成优化后的简历。
        """
        system_prompt = """你是一个专业的简历优化专家。请基于提供的分析结果，生成一份优化后的简历。

要求：
1. 使用 Markdown 格式
2. 使用 STAR 法则（Situation-Task-Action-Result）描述工作经历和项目
3. 突出与目标岗位相关的技能和经验
4. 添加匹配分析中建议的关键词
5. 量化成果（使用数字和百分比）
6. 简历结构清晰，重点突出

输出格式：
```markdown
# 姓名

## 联系方式
- 邮箱: xxx
- 电话: xxx
- 所在地: xxx

## 个人简介
[针对目标岗位优化的简介]

## 专业技能
- **编程语言**: xxx
- **框架**: xxx
- **工具**: xxx

## 工作经历

### 公司名称 | 职位 | 时间
- **[Situation]** 背景描述
- **[Task]** 任务目标
- **[Action]** 采取的行动
- **[Result]** 取得的成果（量化）

## 项目经验

### 项目名称
- **项目背景**: xxx
- **技术栈**: xxx
- **我的职责**: xxx
- **项目成果**: xxx

## 教育背景

### 学校 | 学位 | 专业 | 时间
- GPA: xxx
- 相关课程/荣誉

## 证书/其他
```"""

        extracted_info = state.get("extracted_info", {})
        job_requirements = state.get("job_requirements", {})
        matched_content = state.get("matched_content", {})
        
        human_prompt = f"""请基于以下信息生成优化后的简历：

## 原始简历信息
{extracted_info}

## 目标岗位需求
{job_requirements}

## 匹配分析结果
{matched_content}

请生成一份针对该岗位优化的专业简历。"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]
            
            response = await self.llm.ainvoke(messages)
            
            optimized_resume = response.content
            
            # 提取 markdown 内容
            if "```markdown" in optimized_resume:
                optimized_resume = optimized_resume.split("```markdown")[1].split("```")[0].strip()
            elif optimized_resume.startswith("```") and optimized_resume.endswith("```"):
                optimized_resume = optimized_resume[3:-3].strip()
            
            return {
                "optimized_resume": optimized_resume,
                "current_step": "generate_optimized_resume",
            }
        
        except Exception as e:
            return {
                "error": f"优化简历生成失败: {str(e)}",
                "current_step": "generate_optimized_resume",
            }
    
    async def run(
        self,
        resume_text: str,
        job_desc: str,
        job_url: Optional[str] = None,
    ) -> ResumeOptimizerState:
        """
        运行简历优化流程
        
        Args:
            resume_text: 原始简历文本
            job_desc: 岗位描述
            job_url: 岗位链接（可选）
        
        Returns:
            优化后的状态（包含所有中间结果和最终简历）
        """
        initial_state: ResumeOptimizerState = {
            "resume_text": resume_text,
            "job_desc": job_desc,
            "job_url": job_url,
            "extracted_info": None,
            "job_requirements": None,
            "matched_content": None,
            "optimized_resume": None,
            "error": None,
            "current_step": "start",
        }
        
        # 运行图
        final_state = await self.graph.ainvoke(initial_state)
        
        return final_state


# 便捷函数
def create_resume_optimizer_graph(
    provider: Optional[Union[LLMProvider, str]] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **llm_kwargs: Any,
) -> ResumeOptimizerAgent:
    """
    创建简历优化智能体实例
    
    Args:
        provider: LLM 提供商 (openai/deepseek/zhipu/ollama/anthropic/qwen)
        model: 使用的模型名称
        api_key: API Key (可选)
        **llm_kwargs: 传递给 LLM 的其他参数
    
    Returns:
        ResumeOptimizerAgent 实例
    
    Examples:
        # 使用默认配置 (从环境变量读取)
        agent = create_resume_optimizer_graph()
        
        # 使用 DeepSeek
        agent = create_resume_optimizer_graph(provider="deepseek")
        
        # 使用智谱 GLM-4
        agent = create_resume_optimizer_graph(provider="zhipu", model="glm-4")
        
        # 使用本地 Ollama
        agent = create_resume_optimizer_graph(provider="ollama", model="qwen2.5")
    """
    return ResumeOptimizerAgent(
        provider=provider,
        model=model,
        api_key=api_key,
        **llm_kwargs,
    )
