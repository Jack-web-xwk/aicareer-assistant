# tests/

## 功能说明
测试代码目录，包含单元测试、集成测试和端到端测试。

## 开发状态
- [x] 待开发
- [ ] 开发中
- [ ] 已完成

## 依赖关系
- pytest
- pytest-asyncio
- httpx（API 测试）

## 文件说明
| 文件 | 说明 |
|------|------|
| conftest.py | pytest 配置和 fixtures |
| test_resume_parser.py | 简历解析测试 |
| test_job_scraper.py | 爬虫测试 |
| test_agents.py | 智能体测试 |
| test_api.py | API 接口测试 |

## 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_resume_parser.py

# 生成覆盖率报告
pytest --cov=app
```

## 注意事项
- 测试需使用 mock 避免真实 API 调用
- 数据库测试使用内存 SQLite
- 异步测试需使用 pytest-asyncio
