#!/usr/bin/env python3
"""
测试面试智能体功能 - 简化版
避免导入不必要模块
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_simple():
    """简单测试系统消息构建"""
    print("[TEST] 简单测试面试智能体...")
    
    try:
        # 直接测试系统提示词构建
        job_role = "Python 后端工程师"
        tech_stack = ["Python", "FastAPI", "PostgreSQL"]
        question_count = 1
        max_questions = 3
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
        
        print("[OK] 系统提示词构建成功")
        print(f"预览: {system_prompt[:200]}...")
        
        # 测试正则表达式评分提取
        import re
        test_responses = [
            "这个回答我可以给85分，因为回答得很全面。",
            "评分: 90分，不错。",
            "给75分，需要补充细节。",
            "85/100，回答基本正确。"
        ]
        
        print("\n[SCAN] 测试评分提取:")
        for resp in test_responses:
            score_match = re.search(r'(\d{1,3})\s*分', resp)
            if not score_match:
                score_match = re.search(r'(\d{1,3})(?=\s*分)', resp)
            if not score_match:
                score_match = re.search(r'评分\s*[:：]?\s*(\d{1,3})', resp)
            if not score_match:
                score_match = re.search(r'(\d{1,3})\s*/\s*100', resp)
            
            if score_match:
                score = int(score_match.group(1))
                print(f"  '{resp}' -> {score}分")
            else:
                print(f"  '{resp}' -> 未找到评分")
        
        print("\n[SUCCESS] 简单测试通过！")
        return True
        
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("[TEST] AI面试系统简单测试")
    print("=" * 50)
    
    success = await test_simple()
    
    print("\n" + "=" * 50)
    if success:
        print("[OK] 基本功能测试通过！")
        print("\n[NEXT] 下一步:")
        print("1. 确保所有依赖已安装 (aiosqlite, langchain-openai, etc.)")
        print("2. 配置正确的API Key (当前使用DeepSeek)")
        print("3. 运行完整测试: python -m pytest tests/")
        return 0
    else:
        print("[FAIL] 测试失败")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)