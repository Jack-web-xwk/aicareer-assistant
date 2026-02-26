# scripts/

## 功能说明
脚本目录，包含数据库初始化、数据迁移等运维脚本。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- SQLAlchemy
- app.models
- app.core.database

## 文件说明
| 文件 | 说明 |
|------|------|
| init_db.py | 数据库初始化脚本 |

## 使用方法
```bash
# 初始化数据库
python scripts/init_db.py
```

## 注意事项
- 脚本需在项目根目录运行
- 运行前确保 `.env` 已正确配置
