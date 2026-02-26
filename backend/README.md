# backend/

## 功能说明
后端服务的根目录，包含 FastAPI 应用、业务逻辑、数据模型和 LangGraph 智能体等核心代码。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- FastAPI 0.115+
- LangGraph 0.2+
- LangChain 0.3+
- SQLAlchemy 2.0+
- pdfplumber
- python-docx
- OpenAI SDK

## 目录结构
```
backend/
├── app/                 # 核心应用代码
│   ├── api/             # API 路由
│   ├── core/            # 配置和工具
│   ├── models/          # 数据模型
│   ├── services/        # 业务服务
│   ├── agents/          # LangGraph 智能体
│   └── utils/           # 通用工具
├── tests/               # 测试代码
├── scripts/             # 脚本文件
├── .env.example         # 环境变量示例
├── requirements.txt     # Python 依赖
└── main.py              # 应用入口
```

## 注意事项
- 运行前需配置 `.env` 文件
- 首次运行需执行 `python scripts/init_db.py` 初始化数据库
- 所有 API 路由需添加适当的错误处理
