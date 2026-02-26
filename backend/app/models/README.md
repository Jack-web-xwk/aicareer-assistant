# models/

## 功能说明
数据模型层，包含 SQLAlchemy ORM 模型定义和 Pydantic Schema 定义。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- SQLAlchemy 2.0+
- Pydantic

## 文件说明
| 文件 | 说明 |
|------|------|
| __init__.py | 模型导出 |
| base.py | SQLAlchemy Base 类 |
| user.py | 用户模型 |
| resume.py | 简历模型 |
| interview.py | 面试记录模型 |
| schemas.py | Pydantic Schema 定义 |

## 模型关系
```
User (1) -----> (*) Resume
User (1) -----> (*) InterviewRecord
```

## 注意事项
- ORM 模型与 Schema 分离，遵循清晰的职责划分
- 所有模型需定义 `created_at` 和 `updated_at` 字段
- 使用 SQLAlchemy 2.0 风格的类型注解
