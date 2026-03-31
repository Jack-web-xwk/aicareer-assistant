"""
Interview Agent - 面试模拟智能体

使用 LangGraph 实现语音技术面试模拟：
1. 初始化面试
2. 语音转文字
3. 生成回复
4. 文字转语音
5. 检查是否结束

支持多种 LLM 提供商：OpenAI, DeepSeek, 智谱GLM, Ollama, Anthropic, Qwen, Bailian
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.core.llm_provider import LLMFactory, LLMProvider, create_llm
from app.core.prompts import (
    MULTI_DIMENSION_ASSESSMENT_PROMPT,
    REALTIME_FEEDBACK_PROMPT,
    LEARNING_SUGGESTION_PROMPT,
    TECHNICAL_DEPTH_ANALYSIS_PROMPT,
    COMMUNICATION_EVAL_PROMPT,
    PROBLEM_SOLVING_EVAL_PROMPT,
    format_interview_record,
    format_conversation_history,
)
from app.models.schemas import AssessmentDimension, DimensionScore, RealTimeFeedback, LearningSuggestion
from app.services.audio_processor import AudioProcessor
from app.utils.logger import get_logger


class QuestionServiceRef:
    """
    QuestionService 引用类
    
    用于避免循环导入，只在运行时动态导入 QuestionService。
    """
    
    @staticmethod
    def get_service(db_session):
        """动态获取 QuestionService 实例"""
        from app.services.question_service import QuestionService
        return QuestionService(db_session)


class InterviewMessage(TypedDict):
    """面试对话消息"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: str
    score: Optional[float]


class InterviewState(TypedDict):
    """
    面试模拟智能体状态
    
    包含整个面试流程中需要传递的所有数据。
    """
    # 配置
    job_role: str                              # 目标岗位
    tech_stack: List[str]                      # 技术栈
    difficulty_level: str                      # 难度级别 (easy/medium/hard)
    max_questions: int                         # 最大问题数
    
    # 对话状态
    conversation_history: List[InterviewMessage]  # 对话历史
    current_question: Optional[str]            # 当前问题
    current_answer: Optional[str]              # 当前回答（转录后）
    question_count: int                        # 已问问题数
    
    # 音频数据
    audio_input: Optional[str]                 # 输入音频（Base64）
    audio_output: Optional[str]                # 输出音频（Base64）
    
    # 评分
    scores: List[Dict[str, Any]]               # 每题评分
    total_score: Optional[float]               # 总分
    dimension_scores: Optional[List[Dict[str, Any]]]  # 多维度评分
    realtime_feedback_log: Optional[List[Dict[str, Any]]]  # 实时反馈历史
    
    # 状态控制
    is_finished: bool                          # 是否结束
    current_step: str                          # 当前步骤
    error: Optional[str]                       # 错误信息
    
    # 最终报告
    report: Optional[Dict[str, Any]]           # 面试评估报告
    learning_plan: Optional[Dict[str, Any]]    # 学习计划


class InterviewAgent:
    """
    面试模拟智能体
    
    使用 LangGraph 构建的面试模拟流程：
    init_interview → [transcribe_audio → generate_response → synthesize_speech → check_finish] (循环)
    
    支持多种 LLM 提供商：
    - OpenAI (默认)
    - DeepSeek (deepseek-chat, deepseek-reasoner)
    - 智谱 GLM (glm-4, glm-4-flash)
    - Ollama (本地模型)
    - Anthropic Claude
    - 通义千问 Qwen
    - 阿里百炼 Bailian
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
            provider: LLM 提供商 (openai/deepseek/zhipu/ollama/anthropic/qwen/bailian)
            model: 使用的模型名称
            api_key: API Key (可选，默认从环境变量读取)
            **llm_kwargs: 传递给 LLM 的其他参数
        """
        self.provider = provider
        self.model = model
        self.question_service = question_service
        self.use_hybrid_mode = use_hybrid_mode
        
        # 初始化日志记录器
        self.logger = get_logger(__name__)
        
        try:
            # 使用 LLM Factory 创建面试专用 LLM
            self.llm: BaseChatModel = LLMFactory.create_for_interview(
                provider=provider,
                model=model,
                api_key=api_key,
                **llm_kwargs,
            )
            
            # 音频处理器仍使用 OpenAI (Whisper/TTS)
            audio_api_key = api_key if provider in [None, LLMProvider.OPENAI, "openai"] else settings.OPENAI_API_KEY
            self.audio_processor = AudioProcessor(api_key=audio_api_key)
            
            # 构建图
            self.graph = self._build_graph()
        except Exception as e:
            self.logger.error(f"InterviewAgent初始化失败: {str(e)}", exc_info=True)
            raise
    
    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 状态图"""
        try:
            workflow = StateGraph(InterviewState)
            
            # 添加节点
            workflow.add_node("init_interview", self._init_interview)
            workflow.add_node("transcribe_audio", self._transcribe_audio)
            workflow.add_node("generate_response", self._generate_response)
            workflow.add_node("synthesize_speech", self._synthesize_speech)
            workflow.add_node("check_finish", self._check_finish)
            workflow.add_node("generate_report", self._generate_report)
            workflow.add_node("generate_realtime_feedback", self._generate_realtime_feedback)  # 新增：实时反馈
            workflow.add_node("generate_learning_plan", self._generate_learning_plan)  # 新增：学习计划
            
            # 设置入口点
            workflow.set_entry_point("init_interview")
            
            # 添加边
            workflow.add_edge("init_interview", "synthesize_speech")
            workflow.add_edge("transcribe_audio", "generate_response")
            workflow.add_edge("generate_response", "synthesize_speech")
            workflow.add_edge("synthesize_speech", "check_finish")
            
            # 条件边：检查是否结束
            workflow.add_conditional_edges(
                "check_finish",
                self._should_finish,
                {
                    "continue": "generate_realtime_feedback",  # 继续时先生成实时反馈
                    "finish": "generate_report",
                }
            )
            
            # 实时反馈后返回等待下一轮输入
            workflow.add_edge("generate_realtime_feedback", END)
            
            workflow.add_edge("generate_report", "generate_learning_plan")
            workflow.add_edge("generate_learning_plan", END)
            
            # 编译图
            return workflow.compile()
        except Exception as e:
            self.logger.error(f"构建状态图失败: {str(e)}", exc_info=True)
            raise
    
    def _should_finish(self, state: InterviewState) -> str:
        """判断是否结束面试"""
        if state.get("is_finished", False):
            return "finish"
        return "continue"
    
    async def _init_interview(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点1: 初始化面试
        
        设置面试官角色，生成第一个技术问题。
        """
        self.logger.debug(f"开始初始化面试，岗位: {state['job_role']}, 技术栈: {state['tech_stack']}")
        job_role = state["job_role"]
        tech_stack = state["tech_stack"]
        difficulty = state.get("difficulty_level", "medium")
        
        difficulty_desc = {
            "easy": "基础级别，考察基本概念和常见用法",
            "medium": "中等难度，考察原理理解和实际应用",
            "hard": "高难度，考察深入原理、性能优化和架构设计",
        }
        
        # ==================== Hybrid Mode: 题库集成 ====================
        question_from_bank = None
        
        if self.use_hybrid_mode and self.question_service:
            import random
            
            # 50% 概率尝试从题库抽取
            if random.random() < 0.5:
                try:
                    # 异步获取题库题目
                    questions = await self.question_service.get_by_category(
                        category=job_role,
                        tech_stack=tech_stack,
                        difficulty=difficulty,
                        limit=10,
                    )
                    
                    # Fallback 1: 如果技术栈过滤后没有题目，尝试只按分类 + 难度
                    if not questions:
                        questions = await self.question_service.get_by_category(
                            category=job_role,
                            difficulty=difficulty,
                            limit=10,
                        )
                    
                    # Fallback 2: 如果还是没有，尝试只按分类
                    if not questions:
                        questions = await self.question_service.get_by_category(
                            category=job_role,
                            limit=10,
                        )
                    
                    # 如果有题目，随机选择一个
                    if questions:
                        selected_question = random.choice(questions)
                        question_from_bank = selected_question.question
                        self.logger.info(
                            f"从题库抽取题目：id={selected_question.id}, "
                            f"category={selected_question.category}"
                        )
                except Exception as e:
                    self.logger.warning(f"题库抽取失败，切换到 LLM 模式：{str(e)}")
        
        # ==================== 生成面试开场 ====================
        if question_from_bank:
            # 使用题库题目
            system_prompt = f"""你是一位经验丰富的技术面试官，正在面试一位应聘「{job_role}」岗位的候选人。

面试配置：
- 目标岗位：{job_role}
- 技术栈范围：{', '.join(tech_stack)}
- 难度级别：{difficulty} - {difficulty_desc.get(difficulty, difficulty_desc['medium'])}

面试要求：
1. 先简单自我介绍（1-2 句话）
2. 然后提出以下技术问题（不要修改问题本身）：
   "{question_from_bank}"
3. 保持专业友好的态度"""
        else:
            # 使用 LLM 生成
            system_prompt = f"""你是一位经验丰富的技术面试官，正在面试一位应聘「{job_role}」岗位的候选人。

面试配置：
- 目标岗位：{job_role}
- 技术栈范围：{', '.join(tech_stack)}
- 难度级别：{difficulty} - {difficulty_desc.get(difficulty, difficulty_desc['medium'])}

面试要求：
1. 每次只问一个问题
2. 问题应该具体、明确，便于口头回答
3. 从基础概念开始，逐渐深入
4. 根据候选人回答情况调整后续问题
5. 保持专业友好的态度
6. 问题应覆盖技术栈的不同方面

请开始面试，先简单自我介绍，然后提出第一个技术问题。"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="请开始面试。"),
            ]
            
            response = await self.llm.ainvoke(messages)
            first_question = response.content
            
            # 初始化对话历史
            conversation_history = [
                {
                    "role": "assistant",
                    "content": first_question,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "score": None,
                }
            ]
            
            return {
                "current_question": first_question,
                "conversation_history": conversation_history,
                "question_count": 1,
                "current_step": "init_interview",
                "scores": [],
            }
        
        except Exception as e:
            self.logger.error(f"面试初始化失败: {str(e)}", exc_info=True)
            return {
                "error": f"面试初始化失败: {str(e)}",
                "current_step": "init_interview",
            }
    
    async def _transcribe_audio(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点2: 语音转文字
        
        使用 Whisper 将用户语音转换为文字。
        """
        self.logger.debug(f"开始语音转文字处理，音频输入长度: {len(state.get('audio_input', '')) if state.get('audio_input') else 0}")
        audio_input = state.get("audio_input")
        
        if not audio_input:
            return {
                "current_answer": "",
                "current_step": "transcribe_audio",
            }
        
        try:
            # 调用 Whisper 转录
            transcript = self.audio_processor.transcribe(
                audio_base64=audio_input,
                language="zh",
            )
            
            # 添加到对话历史
            conversation_history = list(state.get("conversation_history", []))
            conversation_history.append({
                "role": "user",
                "content": transcript,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "score": None,
            })
            
            return {
                "current_answer": transcript,
                "conversation_history": conversation_history,
                "current_step": "transcribe_audio",
            }
        
        except Exception as e:
            self.logger.error(f"语音转文字失败: {str(e)}", exc_info=True)
            return {
                "error": f"语音转文字失败: {str(e)}",
                "current_step": "transcribe_audio",
            }
    
    async def _generate_response(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点3: 生成回复
        
        基于对话历史生成面试官的回复（反馈 + 下一个问题）。
        """
        self.logger.debug(f"开始生成回复，当前问题数: {state.get('question_count', 1)}/{state.get('max_questions', 5)}, 回答长度: {len(state.get('current_answer', ''))}")
        job_role = state.get("job_role", "未知岗位")
        tech_stack = state.get("tech_stack", [])
        conversation_history = state.get("conversation_history", [])
        current_answer = state.get("current_answer", "")
        question_count = state.get("question_count", 1)
        max_questions = state.get("max_questions", 5)
        
        # 判断是否是最后一个问题
        is_last_question = question_count >= max_questions
        
        system_prompt = f"""你是一位经验丰富的技术面试官，正在面试一位应聘「{job_role}」岗位的候选人。
技术栈范围：{', '.join(tech_stack)}

当前是第 {question_count}/{max_questions} 个问题。

请基于候选人的回答，以自然、专业的面试官口吻进行回复：
1. 首先对回答进行简短的反馈（指出亮点或需要补充的地方）
2. 给出这个回答的评分（0-100分），请在回复中明确写出评分，例如"这个回答我可以给85分"
3. {"然后宣布面试结束，感谢候选人" if is_last_question else "然后自然地提出下一个技术问题"}

请用自然流畅的中文回复，保持专业友好的态度，就像真实的面试对话一样。
{"这是最后一个问题，请给出总结性反馈并结束面试。" if is_last_question else "请根据候选人的回答情况，提出一个相关的技术问题。"}"""

        # 构建对话上下文
        messages = [SystemMessage(content=system_prompt)]
        
        # 添加对话历史，保持自然的对话格式
        for msg in conversation_history:
            if msg["role"] == "assistant":
                messages.append(SystemMessage(content=f"面试官: {msg['content']}"))
            else:
                messages.append(HumanMessage(content=f"候选人: {msg['content']}"))
        
        try:
            response = await self.llm.ainvoke(messages)
            full_response = response.content.strip()
            
            # 从回复中提取评分（使用正则表达式查找0-100之间的数字）
            import re
            score_match = re.search(r'(\d{1,3})\s*分', full_response)
            if not score_match:
                # 尝试其他格式：如"给85分"、"评分85"、"85分"
                score_match = re.search(r'(\d{1,3})(?=\s*分)', full_response)
            if not score_match:
                score_match = re.search(r'评分\s*[:：]?\s*(\d{1,3})', full_response)
            if not score_match:
                score_match = re.search(r'(\d{1,3})\s*/\s*100', full_response)
            
            score = 0
            if score_match:
                try:
                    score = int(score_match.group(1))
                    # 确保分数在合理范围内
                    if score < 0:
                        score = 0
                    elif score > 100:
                        score = 100
                except ValueError:
                    score = 0
            else:
                # 如果没有找到明确评分，根据回复长度和质量估算一个分数
                if len(full_response) > 100 and "不错" in full_response or "很好" in full_response:
                    score = 80
                elif len(full_response) > 50:
                    score = 70
                else:
                    score = 60
            
            # 提取反馈部分（假设评分前的部分是反馈）
            feedback = full_response
            if score_match:
                # 将评分部分从反馈中移除，避免重复
                feedback = feedback.replace(score_match.group(0), '').strip()
            
            # 对于最后一个问题，next_content应该是结束语
            if is_last_question:
                next_content = "面试结束，感谢您的参与！"
                is_last = True
            else:
                # 下一个问题就是完整的回复（包含反馈和问题）
                next_content = full_response
                is_last = False
            
            # 更新对话历史
            conversation_history = list(state.get("conversation_history", []))
            conversation_history.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "score": None,
            })
            
            # 记录评分
            scores = list(state.get("scores", []))
            scores.append({
                "question_number": question_count,
                "question": state.get("current_question", ""),
                "answer": current_answer,
                "score": score,
                "feedback": feedback[:500] if len(feedback) > 500 else feedback,  # 截断过长的反馈
            })
            
            return {
                "current_question": next_content if not is_last else None,
                "conversation_history": conversation_history,
                "question_count": question_count + 1 if not is_last else question_count,
                "scores": scores,
                "is_finished": is_last,
                "current_step": "generate_response",
            }
        
        except Exception as e:
            self.logger.error(f"生成回复失败: {str(e)}", exc_info=True)
            return {
                "error": f"生成回复失败: {str(e)}",
                "current_step": "generate_response",
            }
    
    async def _synthesize_speech(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点4: 文字转语音
        
        使用 TTS 将面试官的回复转换为语音。
        """
        conversation_history = state.get("conversation_history", [])
        
        if not conversation_history:
            return {
                "audio_output": None,
                "current_step": "synthesize_speech",
            }
        
        # 获取最新的面试官消息
        last_assistant_msg = None
        for msg in reversed(conversation_history):
            if msg["role"] == "assistant":
                last_assistant_msg = msg["content"]
                break
        
        if not last_assistant_msg:
            return {
                "audio_output": None,
                "current_step": "synthesize_speech",
            }
        
        try:
            # 调用 TTS
            audio_base64 = self.audio_processor.synthesize_to_base64(
                text=last_assistant_msg,
                voice=settings.TTS_VOICE,
            )
            
            return {
                "audio_output": audio_base64,
                "current_step": "synthesize_speech",
            }
        
        except Exception as e:
            # TTS 失败不应该中断面试，返回空音频
            self.logger.warning(f"语音合成失败（非致命）: {str(e)}", exc_info=True)
            return {
                "audio_output": None,
                "current_step": "synthesize_speech",
                "error": f"语音合成失败（非致命）: {str(e)}",
            }
    
    async def _check_finish(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点5: 检查是否结束
        
        判断面试是否应该结束。
        """
        question_count = state.get("question_count", 0)
        max_questions = state.get("max_questions", 5)
        is_finished = state.get("is_finished", False)
        
        should_finish = is_finished or question_count > max_questions
        
        return {
            "is_finished": should_finish,
            "current_step": "check_finish",
        }
    
    async def _generate_realtime_feedback(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点 6: 生成实时反馈
        
        基于候选人当前回答，提供简洁、即时的反馈（目标延迟 <200ms）。
        """
        start_time = time.time()
        
        job_role = state.get("job_role", "未知岗位")
        current_question = state.get("current_question", "")
        current_answer = state.get("current_answer", "")
        question_count = state.get("question_count", 1)
        max_questions = state.get("max_questions", 5)
        session_id = state.get("session_id", "unknown")
        
        try:
            prompt = REALTIME_FEEDBACK_PROMPT.format(
                job_role=job_role,
                current_question=current_question[:200] if current_question else "",
                current_answer=current_answer[:300] if current_answer else "",
                question_count=question_count,
                max_questions=max_questions,
            )
            
            messages = [
                SystemMessage(content="你是专业的面试反馈助手，请生成简洁的 JSON 格式反馈。"),
                HumanMessage(content=prompt),
            ]
            
            response = await self.llm.ainvoke(messages, {"temperature": 0.2})
            
            import json
            content = response.content
            json_str = self._extract_json(content)
            feedback_data = json.loads(json_str)
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            realtime_feedback = RealTimeFeedback(
                session_id=session_id,
                dimension_scores=[],
                overall_feedback=feedback_data.get("overall_feedback", ""),
                suggestions=feedback_data.get("suggestions", []),
                response_time_ms=response_time_ms,
            )
            
            realtime_feedback_log = list(state.get("realtime_feedback_log", []))
            realtime_feedback_log.append(realtime_feedback.model_dump())
            
            self.logger.info(f"实时反馈已生成，响应时间：{response_time_ms}ms")
            
            return {
                "realtime_feedback_log": realtime_feedback_log,
                "current_step": "generate_realtime_feedback",
            }
        
        except Exception as e:
            self.logger.warning(f"实时反馈生成失败（非致命）: {str(e)}")
            return {
                "realtime_feedback_log": state.get("realtime_feedback_log", []),
                "current_step": "generate_realtime_feedback",
            }
    
    async def _generate_report(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点 7: 生成面试评估报告（多维度评分）
        
        综合评估面试表现，从 5 个维度生成详细报告。
        """
        job_role = state.get("job_role", "未知岗位")
        tech_stack = state.get("tech_stack", [])
        scores = state.get("scores", [])
        
        if scores:
            total_score = sum(s.get("score", 0) for s in scores) / len(scores)
        else:
            total_score = 0
        
        interview_record = format_interview_record(scores)
        
        try:
            prompt = MULTI_DIMENSION_ASSESSMENT_PROMPT.format(
                job_role=job_role,
                tech_stack=", ".join(tech_stack),
                interview_record=interview_record,
            )
            
            messages = [
                SystemMessage(content="你是专业的多维度面试评估专家。请严格按照 JSON 格式输出。"),
                HumanMessage(content=prompt),
            ]
            
            response = await self.llm.ainvoke(messages, {"temperature": 0.3})
            
            import json
            content = response.content
            json_str = self._extract_json(content)
            report_data = json.loads(json_str)
            
            dimension_scores = []
            for dim_data in report_data.get("dimension_scores", []):
                try:
                    dim_id = dim_data.get("dimension_id")
                    if isinstance(dim_id, str):
                        dimension = AssessmentDimension(dim_id)
                    else:
                        continue
                    
                    dim_score = DimensionScore(
                        dimension_id=dimension,
                        score=float(dim_data.get("score", 0)),
                        feedback=dim_data.get("feedback", ""),
                        key_points=dim_data.get("key_points", []),
                        weight=dimension.weight,
                    )
                    dimension_scores.append(dim_score.model_dump())
                except ValueError as e:
                    self.logger.warning(f"无效的维度 ID: {dim_data.get('dimension_id')}")
            
            if dimension_scores:
                weighted_total = sum(DimensionScore(**ds).weighted_score for ds in dimension_scores)
                report_data["total_score"] = round(weighted_total, 2)
            
            report_data["question_scores"] = scores
            
            return {
                "report": report_data,
                "dimension_scores": dimension_scores,
                "total_score": report_data.get("total_score", total_score),
                "current_step": "generate_report",
            }
        
        except Exception as e:
            self.logger.error(f"评估报告生成失败：{str(e)}", exc_info=True)
            return {
                "report": {
                    "total_score": total_score,
                    "grade": self._score_to_grade(total_score),
                    "strengths": [],
                    "weaknesses": [],
                    "suggestions": ["报告生成失败，请查看详细评分"],
                    "question_scores": scores,
                },
                "dimension_scores": [],
                "total_score": total_score,
                "current_step": "generate_report",
            }
    
    async def _generate_learning_plan(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点 8: 生成个性化学习计划
        
        基于面试评估结果，为候选人制定学习计划。
        """
        job_role = state.get("job_role", "未知岗位")
        dimension_scores = state.get("dimension_scores", [])
        
        if not dimension_scores:
            return {"learning_plan": None, "current_step": "generate_learning_plan"}
        
        try:
            min_score = 100
            weakest_dimension = None
            weakness_description = ""
            
            for dim_data in dimension_scores:
                score = dim_data.get("score", 0)
                if score < min_score:
                    min_score = score
                    weakest_dimension = dim_data.get("dimension_id")
                    weakness_description = dim_data.get("feedback", "")
            
            if not weakest_dimension:
                return {"learning_plan": None, "current_step": "generate_learning_plan"}
            
            other_dimensions = {
                dim.get("dimension_id"): dim.get("score")
                for dim in dimension_scores
                if dim.get("dimension_id") != weakest_dimension
            }
            
            prompt = LEARNING_SUGGESTION_PROMPT.format(
                job_role=job_role,
                experience_level="mid",
                weakness_dimension=weakest_dimension,
                weakness_description=weakness_description[:200],
                other_dimensions=str(other_dimensions),
            )
            
            messages = [
                SystemMessage(content="你是专业的学习规划师。请生成具体、可执行的学习计划。"),
                HumanMessage(content=prompt),
            ]
            
            response = await self.llm.ainvoke(messages, {"temperature": 0.4})
            
            import json
            content = response.content
            json_str = self._extract_json(content)
            learning_plan_data = json.loads(json_str)
            
            return {
                "learning_plan": learning_plan_data,
                "current_step": "generate_learning_plan",
            }
        
        except Exception as e:
            self.logger.error(f"学习计划生成失败：{str(e)}", exc_info=True)
            return {
                "learning_plan": None,
                "current_step": "generate_learning_plan",
            }
    
    def _extract_json(self, content: str) -> str:
        """从 LLM 响应中提取 JSON"""
        if "```json" in content:
            return content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            return content.split("```")[1].split("```")[0].strip()
        return content.strip()
    
    async def _generate_report(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点6: 生成面试评估报告
        
        综合评估面试表现，生成详细报告。
        """
        job_role = state.get("job_role", "未知岗位")
        tech_stack = state.get("tech_stack", [])
        scores = state.get("scores", [])
        conversation_history = state.get("conversation_history", [])
        
        # 计算总分
        if scores:
            total_score = sum(s.get("score", 0) for s in scores) / len(scores)
        else:
            total_score = 0
        
        system_prompt = f"""你是一位专业的面试评估专家。请基于以下面试记录生成一份详细的评估报告。

面试岗位：{job_role}
技术栈：{', '.join(tech_stack)}

请生成 JSON 格式的评估报告：
{{
    "total_score": 总分（0-100），
    "grade": "等级（A/B/C/D/F）",
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "suggestions": ["改进建议1", "改进建议2"],
    "technical_assessment": "技术能力评估",
    "communication_assessment": "沟通表达评估",
    "recommendation": "是否推荐（强烈推荐/推荐/待定/不推荐）",
    "detailed_report": "详细的 Markdown 格式评估报告"
}}"""

        # 构建面试记录
        interview_record = "\n".join([
            f"Q{i+1}: {s.get('question', '')}\nA: {s.get('answer', '')}\n评分: {s.get('score', 0)}\n反馈: {s.get('feedback', '')}"
            for i, s in enumerate(scores)
        ])
        
        human_prompt = f"请基于以下面试记录生成评估报告：\n\n{interview_record}"
        
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
            
            report = json.loads(json_str)
            report["question_scores"] = scores
            
            return {
                "report": report,
                "total_score": report.get("total_score", total_score),
                "current_step": "generate_report",
            }
        
        except Exception as e:
            # 如果报告生成失败，返回基本报告
            self.logger.error(f"评估报告生成失败: {str(e)}", exc_info=True)
            return {
                "report": {
                    "total_score": total_score,
                    "grade": self._score_to_grade(total_score),
                    "strengths": [],
                    "weaknesses": [],
                    "suggestions": ["报告生成失败，请查看详细评分"],
                    "question_scores": scores,
                },
                "total_score": total_score,
                "error": f"评估报告生成失败: {str(e)}",
                "current_step": "generate_report",
            }
    
    def _score_to_grade(self, score: float) -> str:
        """将分数转换为等级"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    async def start_interview(
        self,
        job_role: str,
        tech_stack: List[str],
        difficulty_level: str = "medium",
        max_questions: int = 5,
    ) -> InterviewState:
        """
        开始面试
        
        Args:
            job_role: 目标岗位
            tech_stack: 技术栈
            difficulty_level: 难度级别
            max_questions: 最大问题数
        
        Returns:
            初始化后的面试状态
        """
        initial_state: InterviewState = {
            "job_role": job_role,
            "tech_stack": tech_stack,
            "difficulty_level": difficulty_level,
            "max_questions": max_questions,
            "conversation_history": [],
            "current_question": None,
            "current_answer": None,
            "question_count": 0,
            "audio_input": None,
            "audio_output": None,
            "scores": [],
            "total_score": None,
            "is_finished": False,
            "current_step": "start",
            "error": None,
            "report": None,
        }
        
        try:
            # 运行初始化
            result = await self.graph.ainvoke(initial_state)
            self.logger.info(f"面试已成功启动: {job_role}, 技术栈: {tech_stack}")
            return result
        except Exception as e:
            self.logger.error(f"启动面试失败: {str(e)}", exc_info=True)
            raise
    
    async def process_answer(
        self,
        state: InterviewState,
        audio_input: Optional[str] = None,
        text_input: Optional[str] = None,
    ) -> InterviewState:
        """
        处理用户回答
        
        Args:
            state: 当前面试状态
            audio_input: 用户语音输入（Base64）
            text_input: 用户文本输入（可选，用于调试）
        
        Returns:
            更新后的面试状态
        """
        # 确保状态包含所有必需字段
        state = dict(state)
        
        # 设置默认值，防止字段丢失
        if "job_role" not in state:
            state["job_role"] = state.get("job_role", "未知岗位")
        if "tech_stack" not in state:
            state["tech_stack"] = state.get("tech_stack", [])
        if "difficulty_level" not in state:
            state["difficulty_level"] = state.get("difficulty_level", "medium")
        if "max_questions" not in state:
            state["max_questions"] = state.get("max_questions", 5)
        if "conversation_history" not in state:
            state["conversation_history"] = []
        if "scores" not in state:
            state["scores"] = []
        if "question_count" not in state:
            state["question_count"] = 0
        if "is_finished" not in state:
            state["is_finished"] = False
        
        state["audio_input"] = audio_input
        state["current_step"] = "process_answer"
        
        try:
            # 如果提供了文本输入，直接使用（跳过转录）
            if text_input:
                state["current_answer"] = text_input
                conversation_history = list(state.get("conversation_history", []))
                conversation_history.append({
                    "role": "user",
                    "content": text_input,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "score": None,
                })
                state["conversation_history"] = conversation_history
                
                # 从 generate_response 开始
                # 这里我们需要手动执行后续节点
                state = await self._generate_response(state)
                state = await self._synthesize_speech(state)
                state = await self._check_finish(state)
                
                if state.get("is_finished"):
                    state = await self._generate_report(state)
            else:
                # 从转录开始
                state = await self._transcribe_audio(state)
                state = await self._generate_response(state)
                state = await self._synthesize_speech(state)
                state = await self._check_finish(state)
                
                if state.get("is_finished"):
                    state = await self._generate_report(state)
            
            self.logger.info(f"成功处理用户回答，当前问题数: {state.get('question_count', 0)}")
            return state
        except Exception as e:
            self.logger.error(f"处理用户回答失败: {str(e)}", exc_info=True)
            state["error"] = f"处理用户回答失败: {str(e)}"
            return state


# 便捷函数
def create_interview_graph(
    provider: Optional[Union[LLMProvider, str]] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **llm_kwargs: Any,
) -> InterviewAgent:
    """
    创建面试模拟智能体实例
    
    Args:
        provider: LLM 提供商 (openai/deepseek/zhipu/ollama/anthropic/qwen/bailian)
        model: 使用的模型名称
        api_key: API Key (可选)
        **llm_kwargs: 传递给 LLM 的其他参数
    
    Returns:
        InterviewAgent 实例
    
    Examples:
        # 使用默认配置 (从环境变量读取)
        agent = create_interview_graph()
        
        # 使用 DeepSeek
        agent = create_interview_graph(provider="deepseek")
        
        # 使用 DeepSeek R1 推理模型
        agent = create_interview_graph(provider="deepseek", model="deepseek-reasoner")
        
        # 使用智谱 GLM
        agent = create_interview_graph(provider="zhipu", model="glm-4")
        
        # 使用本地 Ollama
        agent = create_interview_graph(provider="ollama", model="llama3.2")
    """
    return InterviewAgent(
        provider=provider,
        model=model,
        api_key=api_key,
        **llm_kwargs,
    )
