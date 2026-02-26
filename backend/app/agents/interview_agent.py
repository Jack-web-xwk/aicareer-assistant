"""
Interview Agent - 面试模拟智能体

使用 LangGraph 实现语音技术面试模拟：
1. 初始化面试
2. 语音转文字
3. 生成回复
4. 文字转语音
5. 检查是否结束
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.services.audio_processor import AudioProcessor


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
    
    # 状态控制
    is_finished: bool                          # 是否结束
    current_step: str                          # 当前步骤
    error: Optional[str]                       # 错误信息
    
    # 最终报告
    report: Optional[Dict[str, Any]]           # 面试评估报告


class InterviewAgent:
    """
    面试模拟智能体
    
    使用 LangGraph 构建的面试模拟流程：
    init_interview → [transcribe_audio → generate_response → synthesize_speech → check_finish] (循环)
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化智能体
        
        Args:
            api_key: OpenAI API Key
            model: 使用的模型名称
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model=self.model,
            temperature=0.7,
        )
        
        self.audio_processor = AudioProcessor(api_key=self.api_key)
        
        # 构建图
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 状态图"""
        workflow = StateGraph(InterviewState)
        
        # 添加节点
        workflow.add_node("init_interview", self._init_interview)
        workflow.add_node("transcribe_audio", self._transcribe_audio)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("synthesize_speech", self._synthesize_speech)
        workflow.add_node("check_finish", self._check_finish)
        workflow.add_node("generate_report", self._generate_report)
        
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
                "continue": END,  # 返回等待下一轮输入
                "finish": "generate_report",
            }
        )
        
        workflow.add_edge("generate_report", END)
        
        # 编译图
        return workflow.compile()
    
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
        job_role = state["job_role"]
        tech_stack = state["tech_stack"]
        difficulty = state.get("difficulty_level", "medium")
        
        difficulty_desc = {
            "easy": "基础级别，考察基本概念和常见用法",
            "medium": "中等难度，考察原理理解和实际应用",
            "hard": "高难度，考察深入原理、性能优化和架构设计",
        }
        
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
                    "timestamp": datetime.utcnow().isoformat(),
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
            return {
                "error": f"面试初始化失败: {str(e)}",
                "current_step": "init_interview",
            }
    
    async def _transcribe_audio(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点2: 语音转文字
        
        使用 Whisper 将用户语音转换为文字。
        """
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
                "timestamp": datetime.utcnow().isoformat(),
                "score": None,
            })
            
            return {
                "current_answer": transcript,
                "conversation_history": conversation_history,
                "current_step": "transcribe_audio",
            }
        
        except Exception as e:
            return {
                "error": f"语音转文字失败: {str(e)}",
                "current_step": "transcribe_audio",
            }
    
    async def _generate_response(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点3: 生成回复
        
        基于对话历史生成面试官的回复（反馈 + 下一个问题）。
        """
        job_role = state["job_role"]
        tech_stack = state["tech_stack"]
        conversation_history = state.get("conversation_history", [])
        current_answer = state.get("current_answer", "")
        question_count = state.get("question_count", 1)
        max_questions = state.get("max_questions", 5)
        
        # 判断是否是最后一个问题
        is_last_question = question_count >= max_questions
        
        system_prompt = f"""你是一位经验丰富的技术面试官，正在面试一位应聘「{job_role}」岗位的候选人。
技术栈范围：{', '.join(tech_stack)}

当前是第 {question_count}/{max_questions} 个问题。

请基于候选人的回答：
1. 首先对回答进行简短的反馈（指出亮点或需要补充的地方）
2. 给出这个回答的评分（0-100）
3. {"然后宣布面试结束，感谢候选人" if is_last_question else "然后提出下一个技术问题"}

请用 JSON 格式回复：
{{
    "feedback": "对回答的反馈",
    "score": 85,
    "next_content": "{"感谢参与面试的结束语" if is_last_question else "下一个技术问题"}",
    "is_last": {str(is_last_question).lower()}
}}"""

        # 构建对话上下文
        messages = [SystemMessage(content=system_prompt)]
        
        for msg in conversation_history:
            if msg["role"] == "assistant":
                messages.append(SystemMessage(content=f"面试官: {msg['content']}"))
            else:
                messages.append(HumanMessage(content=f"候选人: {msg['content']}"))
        
        try:
            response = await self.llm.ainvoke(messages)
            
            import json
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            result = json.loads(json_str)
            
            feedback = result.get("feedback", "")
            score = result.get("score", 0)
            next_content = result.get("next_content", "")
            is_last = result.get("is_last", is_last_question)
            
            # 组合完整回复
            full_response = f"{feedback}\n\n{next_content}"
            
            # 更新对话历史
            conversation_history = list(state.get("conversation_history", []))
            conversation_history.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.utcnow().isoformat(),
                "score": None,
            })
            
            # 记录评分
            scores = list(state.get("scores", []))
            scores.append({
                "question_number": question_count,
                "question": state.get("current_question", ""),
                "answer": current_answer,
                "score": score,
                "feedback": feedback,
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
    
    async def _generate_report(self, state: InterviewState) -> Dict[str, Any]:
        """
        节点6: 生成面试评估报告
        
        综合评估面试表现，生成详细报告。
        """
        job_role = state["job_role"]
        tech_stack = state["tech_stack"]
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
        
        # 运行初始化
        result = await self.graph.ainvoke(initial_state)
        return result
    
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
        # 更新状态
        state = dict(state)
        state["audio_input"] = audio_input
        state["current_step"] = "process_answer"
        
        # 如果提供了文本输入，直接使用（跳过转录）
        if text_input:
            state["current_answer"] = text_input
            conversation_history = list(state.get("conversation_history", []))
            conversation_history.append({
                "role": "user",
                "content": text_input,
                "timestamp": datetime.utcnow().isoformat(),
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
        
        return state


# 便捷函数
def create_interview_graph(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> InterviewAgent:
    """
    创建面试模拟智能体实例
    
    Args:
        api_key: OpenAI API Key
        model: 使用的模型
    
    Returns:
        InterviewAgent 实例
    """
    return InterviewAgent(api_key=api_key, model=model)
