"""
Learning Suggestion Service - 个性化学习建议服务

基于面试评估结果，为候选人提供个性化的学习计划和建议。
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.models.schemas import AssessmentDimension, DimensionScore, LearningSuggestion
from app.utils.logger import get_logger


class LearningSuggestionService:
    """
    学习建议服务
    
    提供以下功能：
    1. 分析薄弱环节
    2. 生成个性化学习计划
    3. 推荐学习资源
    4. 追踪进步情况
    """
    
    # 学习资源库（按维度分类）
    LEARNING_RESOURCES = {
        AssessmentDimension.TECHNICAL_DEPTH: [
            {
                "title": "深入理解计算机系统 (CSAPP)",
                "type": "book",
                "url": "https://csapp.cs.cmu.edu/",
                "platform": "CMU",
                "estimated_hours": 60,
                "difficulty": "intermediate",
                "description": "计算机系统的全面深入讲解"
            },
            {
                "title": "Coursera - 算法专项课程",
                "type": "course",
                "url": "https://www.coursera.org/specializations/algorithms",
                "platform": "Coursera",
                "estimated_hours": 40,
                "difficulty": "intermediate",
                "description": "斯坦福大学算法课程"
            },
            {
                "title": "极客时间 - 技术专栏",
                "type": "article",
                "url": "https://time.geekbang.org/",
                "platform": "极客时间",
                "estimated_hours": 20,
                "difficulty": "intermediate",
                "description": "国内技术专家深度技术文章"
            },
            {
                "title": "LeetCode 高频题深度练习",
                "type": "practice",
                "url": "https://leetcode.com/problemset/top-100-liked/",
                "platform": "LeetCode",
                "estimated_hours": 30,
                "difficulty": "advanced",
                "description": "Top 100 Liked Questions 深度练习"
            },
        ],
        AssessmentDimension.TECHNICAL_BREADTH: [
            {
                "title": "系统设计入门",
                "type": "course",
                "url": "https://github.com/donnemartin/system-design-primer",
                "platform": "GitHub",
                "estimated_hours": 25,
                "difficulty": "intermediate",
                "description": "全面的系统设计知识体系"
            },
            {
                "title": " Udemy - Complete Web Developer Course",
                "type": "course",
                "url": "https://www.udemy.com/course/the-complete-web-developer-zero-to-mastery/",
                "platform": "Udemy",
                "estimated_hours": 35,
                "difficulty": "beginner",
                "description": "全栈开发通识课程"
            },
            {
                "title": "Tech Weekly Newsletter",
                "type": "article",
                "url": "https://techweekly.com/",
                "platform": "TechWeekly",
                "estimated_hours": 5,
                "difficulty": "beginner",
                "description": "每周技术趋势和广度知识"
            },
            {
                "title": "AWS/Azure/GCP 云认证基础",
                "type": "course",
                "url": "https://aws.amazon.com/training/",
                "platform": "AWS",
                "estimated_hours": 40,
                "difficulty": "intermediate",
                "description": "云计算平台基础知识"
            },
        ],
        AssessmentDimension.COMMUNICATION: [
            {
                "title": "TED - 演讲技巧课程",
                "type": "video",
                "url": "https://www.ted.com/playlists/53/ted_talks_on_public_speaking",
                "platform": "TED",
                "estimated_hours": 8,
                "difficulty": "beginner",
                "description": "学习优秀演讲者的表达技巧"
            },
            {
                "title": "Coursera - 沟通技巧专项",
                "type": "course",
                "url": "https://www.coursera.org/specializations/communication",
                "platform": "Coursera",
                "estimated_hours": 20,
                "difficulty": "beginner",
                "description": "职场沟通技巧系统学习"
            },
            {
                "title": "《金字塔原理》",
                "type": "book",
                "url": "https://www.amazon.com/Pyramid-Principle-Thinking-Writing-Logic-ebook/dp/B07CQXJZ3T",
                "platform": "Amazon",
                "estimated_hours": 15,
                "difficulty": "intermediate",
                "description": "逻辑思考和表达的经典方法"
            },
            {
                "title": "技术写作指南",
                "type": "article",
                "url": "https://documentation.divio.com/",
                "platform": "Divio",
                "estimated_hours": 10,
                "difficulty": "intermediate",
                "description": "技术文档写作最佳实践"
            },
        ],
        AssessmentDimension.LOGIC: [
            {
                "title": "Coursera - 逻辑与数学推理",
                "type": "course",
                "url": "https://www.coursera.org/learn/logic-mathematical-reasoning",
                "platform": "Coursera",
                "estimated_hours": 30,
                "difficulty": "intermediate",
                "description": "系统性逻辑思维训练"
            },
            {
                "title": "LeetCode 算法题分类练习",
                "type": "practice",
                "url": "https://leetcode.com/explore/",
                "platform": "LeetCode",
                "estimated_hours": 40,
                "difficulty": "intermediate",
                "description": "按算法分类系统练习"
            },
            {
                "title": "《思考，快与慢》",
                "type": "book",
                "url": "https://www.amazon.com/Thinking-Fast-Slow-Daniel-Kahneman-ebook/dp/B00555X8OA",
                "platform": "Amazon",
                "estimated_hours": 20,
                "difficulty": "intermediate",
                "description": "理解决策和思维模式"
            },
            {
                "title": "批判性思维导论",
                "type": "course",
                "url": "https://www.edx.org/learn/critical-thinking",
                "platform": "edX",
                "estimated_hours": 25,
                "difficulty": "beginner",
                "description": "培养批判性思维能力"
            },
        ],
        AssessmentDimension.PROBLEM_SOLVING: [
            {
                "title": "Google - 问题解决能力课程",
                "type": "course",
                "url": "https://grow.google/certificates/data-analytics/",
                "platform": "Google",
                "estimated_hours": 35,
                "difficulty": "intermediate",
                "description": "数据驱动的问题解决方法"
            },
            {
                "title": "HackerRank 编程挑战",
                "type": "practice",
                "url": "https://www.hackerrank.com/domains",
                "platform": "HackerRank",
                "estimated_hours": 45,
                "difficulty": "intermediate",
                "description": "多领域编程问题实战"
            },
            {
                "title": "《如何解题》",
                "type": "book",
                "url": "https://www.amazon.com/How-Solve-It-Mathematics-Heuristics-ebook/dp/B00FYOIIG6",
                "platform": "Amazon",
                "estimated_hours": 15,
                "difficulty": "beginner",
                "description": "波利亚经典解题方法论"
            },
            {
                "title": "Project Euler 数学编程题",
                "type": "practice",
                "url": "https://projecteuler.net/",
                "platform": "Project Euler",
                "estimated_hours": 50,
                "difficulty": "advanced",
                "description": "数学与编程结合的挑战题"
            },
        ],
    }
    
    # 优先级映射
    PRIORITY_MAP = {
        "high": {"min_score": 0, "max_score": 60},
        "medium": {"min_score": 60, "max_score": 75},
        "low": {"min_score": 75, "max_score": 100},
    }
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def analyze_weaknesses(
        self, 
        dimension_scores: List[DimensionScore],
        threshold: float = 70.0
    ) -> List[Dict[str, Any]]:
        """
        分析薄弱环节
        
        Args:
            dimension_scores: 多维度评分列表
            threshold: 薄弱阈值，低于此分数视为薄弱
        
        Returns:
            薄弱环节列表，包含维度、分数、描述等
        """
        weaknesses = []
        
        for dim_score in dimension_scores:
            score = dim_score.score
            if score < threshold:
                weakness = {
                    "dimension": dim_score.dimension_id.value,
                    "dimension_name": dim_score.dimension_id.display_name,
                    "score": score,
                    "weight": dim_score.weight,
                    "feedback": dim_score.feedback,
                    "key_points": dim_score.key_points,
                    "priority": self._calculate_priority(score),
                }
                weaknesses.append(weakness)
        
        # 按分数升序排序（最薄弱的在前）
        weaknesses.sort(key=lambda x: x["score"])
        
        return weaknesses
    
    def generate_learning_plan(
        self,
        weaknesses: List[Dict[str, Any]],
        job_role: str = "",
        experience_level: str = "mid",
        max_items: int = 3
    ) -> List[LearningSuggestion]:
        """
        生成个性化学习计划
        
        Args:
            weaknesses: 薄弱环节列表
            job_role: 目标岗位
            experience_level: 经验水平 (junior/mid/senior)
            max_items: 最多生成的建议数量
        
        Returns:
            学习建议列表
        """
        suggestions = []
        
        for i, weakness in enumerate(weaknesses[:max_items]):
            try:
                dimension = AssessmentDimension(weakness["dimension"])
            except ValueError:
                continue
            
            # 获取该维度的推荐资源
            resources = self.recommend_resources(dimension, experience_level)
            
            # 生成行动计划
            action_items = self._generate_action_items(
                dimension,
                weakness,
                experience_level,
            )
            
            # 估算学习时间
            total_hours = sum(
                r.get("estimated_hours", 10) for r in resources[:3]
            )
            
            suggestion = LearningSuggestion(
                dimension=dimension,
                weakness=weakness["feedback"][:200],
                learning_resources=resources[:5],  # 最多 5 个资源
                action_items=action_items,
                priority=weakness["priority"],
                estimated_hours=total_hours,
            )
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def recommend_resources(
        self,
        dimension: AssessmentDimension,
        experience_level: str = "mid",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        推荐学习资源
        
        Args:
            dimension: 评估维度
            experience_level: 经验水平
            limit: 最多返回的资源数量
        
        Returns:
            学习资源列表
        """
        resources = self.LEARNING_RESOURCES.get(dimension, [])
        
        # 根据经验水平过滤和排序
        difficulty_order = {
            "junior": ["beginner", "intermediate", "advanced"],
            "mid": ["intermediate", "advanced", "beginner"],
            "senior": ["advanced", "intermediate", "beginner"],
        }
        
        preferred_difficulties = difficulty_order.get(experience_level, ["intermediate"])
        
        # 按优先级排序
        sorted_resources = sorted(
            resources,
            key=lambda r: (
                0 if r.get("difficulty") in preferred_difficulties[:2] else 1,
                r.get("estimated_hours", 999),
            )
        )
        
        return sorted_resources[:limit]
    
    def track_progress(
        self,
        session_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        追踪进步情况
        
        Args:
            session_history: 历史面试记录列表，每条记录包含 dimension_scores
        
        Returns:
            进度分析报告
        """
        if not session_history:
            return {
                "total_sessions": 0,
                "message": "暂无面试记录",
            }
        
        # 按维度统计分数趋势
        dimension_trends = {}
        
        for session in session_history:
            dimension_scores = session.get("dimension_scores", [])
            for dim_data in dimension_scores:
                dim_id = dim_data.get("dimension_id")
                score = dim_data.get("score", 0)
                
                if dim_id not in dimension_trends:
                    dimension_trends[dim_id] = []
                
                dimension_trends[dim_id].append(score)
        
        # 计算每个维度的趋势
        progress_report = {
            "total_sessions": len(session_history),
            "dimensions": {},
            "overall_improvement": 0,
        }
        
        all_improvements = []
        
        for dim_id, scores in dimension_trends.items():
            if len(scores) >= 2:
                first_score = scores[0]
                last_score = scores[-1]
                improvement = last_score - first_score
                improvement_rate = (improvement / first_score * 100) if first_score > 0 else 0
                
                dimension_name = AssessmentDimension(dim_id).display_name if dim_id in [d.value for d in AssessmentDimension] else dim_id
                
                progress_report["dimensions"][dim_id] = {
                    "name": dimension_name,
                    "first_score": first_score,
                    "latest_score": last_score,
                    "average_score": sum(scores) / len(scores),
                    "improvement": round(improvement, 2),
                    "improvement_rate": round(improvement_rate, 2),
                    "trend": "up" if improvement > 0 else ("down" if improvement < 0 else "stable"),
                }
                
                all_improvements.append(improvement_rate)
        
        # 计算整体进步率
        if all_improvements:
            progress_report["overall_improvement"] = round(sum(all_improvements) / len(all_improvements), 2)
        
        return progress_report
    
    def _calculate_priority(self, score: float) -> str:
        """根据分数计算优先级"""
        if score <= self.PRIORITY_MAP["high"]["max_score"]:
            return "high"
        elif score <= self.PRIORITY_MAP["medium"]["max_score"]:
            return "medium"
        else:
            return "low"
    
    def _generate_action_items(
        self,
        dimension: AssessmentDimension,
        weakness: Dict[str, Any],
        experience_level: str
    ) -> List[str]:
        """生成具体的行动计划"""
        
        # 根据不同维度生成不同的行动计划模板
        action_templates = {
            AssessmentDimension.TECHNICAL_DEPTH: [
                f"第 1-2 周：深入学习{weakness.get('dimension_name', '技术深度')}核心概念，阅读相关技术书籍章节",
                "第 3-4 周：完成在线课程的实践项目，加深理解",
                "第 5-6 周：在实际项目中应用所学知识，解决具体问题",
                "第 7-8 周：总结学习成果，尝试向他人讲解或写技术博客",
            ],
            AssessmentDimension.TECHNICAL_BREADTH: [
                "第 1-2 周：系统学习技术领域概览，建立知识框架",
                "第 3-4 周：了解主流技术栈的特点和适用场景",
                "第 5-6 周：动手实践 2-3 种不同的技术方案",
                "第 7-8 周：参与开源项目或技术社区，拓展视野",
            ],
            AssessmentDimension.COMMUNICATION: [
                "第 1-2 周：学习结构化表达方法（如金字塔原理）",
                "第 3-4 周：每天练习 5 分钟技术话题的清晰表达并录音回听",
                "第 5-6 周：参加技术分享或线上讨论，实践表达技巧",
                "第 7-8 周：寻求反馈并持续改进表达方式",
            ],
            AssessmentDimension.LOGIC: [
                "第 1-2 周：学习逻辑推理基础知识和常见谬误",
                "第 3-4 周：每日练习算法题，注重解题思路的严谨性",
                "第 5-6 周：在技术讨论中刻意练习结构化论证",
                "第 7-8 周：复盘自己的决策过程，找出逻辑漏洞",
            ],
            AssessmentDimension.PROBLEM_SOLVING: [
                "第 1-2 周：学习系统化的问题分析框架（如 5W1H）",
                "第 3-4 周：大量练习编程题目，积累解题模式",
                "第 5-6 周：参与实际项目的问题排查和优化工作",
                "第 7-8 周：总结解题方法论，形成自己的思维模型",
            ],
        }
        
        return action_templates.get(dimension, [
            "第 1-2 周：基础知识学习和理解",
            "第 3-4 周：实践练习巩固知识",
            "第 5-6 周：项目实战应用",
            "第 7-8 周：总结复盘提升",
        ])


# 便捷函数
def create_learning_suggestion_service() -> LearningSuggestionService:
    """创建学习建议服务实例"""
    return LearningSuggestionService()
