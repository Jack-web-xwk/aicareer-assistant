# agents/

## 功能说明
LangGraph 智能体模块，实现简历优化智能体和面试模拟智能体的核心逻辑。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- LangGraph 0.2+
- LangChain 0.3+
- OpenAI GPT-4o-mini

## 文件说明
| 文件 | 说明 |
|------|------|
| __init__.py | 模块初始化 |
| resume_optimizer_agent.py | 简历优化智能体 |
| interview_agent.py | 面试模拟智能体 |

## 简历优化智能体流程
```
extract_resume_info → analyze_job_requirements → match_content → generate_optimized_resume
```

## 面试模拟智能体流程
```
init_interview → [transcribe_audio → generate_response → synthesize_speech → check_finish] (循环)
```

## 注意事项
- State 定义需使用 TypedDict
- 节点函数需返回状态更新字典
- 条件边需定义明确的判断逻辑
- 所有 LLM 调用需设置合理的 temperature
