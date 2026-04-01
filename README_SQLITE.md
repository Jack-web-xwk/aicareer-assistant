# AI Career Assistant - SQLite 版本

## 🎯 项目定位

**个人学习 + 开源演示项目**

- 零配置，开箱即用
- 单文件数据库，便于备份
- 无需 Docker 依赖
- 专注功能开发和学习

---

## 🚀 快速开始

### 方式 1：使用启动脚本（推荐）

```bash
# 一键启动
python start-sqlite.py

# 然后按提示启动后端和前端
```

### 方式 2：手动启动

```bash
# 1. 初始化数据库
cd backend
python -m scripts.init_sqlite

# 2. 启动后端
python main.py

# 3. 启动前端（新终端）
cd frontend
npm run dev

# 4. 访问应用
# http://localhost:5173
```

---

## 📊 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy 2.0
- **异步**: asyncio + aiosqlite
- **认证**: JWT

### 前端
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design 5.x
- **构建工具**: Vite
- **状态管理**: React Hooks

---

## 📁 项目结构

```
aicareer-assistant/
├── backend/
│   ├── app/              # 应用代码
│   ├── data/             # SQLite 数据库文件
│   ├── scripts/          # 脚本工具
│   ├── uploads/          # 上传文件
│   ├── main.py           # 入口
│   └── .env              # 配置文件
├── frontend/
│   ├── src/              # 源代码
│   ├── public/           # 静态资源
│   └── package.json      # 依赖配置
├── start-sqlite.py       # 快速启动脚本
├── SQLITE_QUICKSTART.md  # SQLite 使用指南
└── README.md             # 本文档
```

---

## 🔧 常用命令

### 数据库管理

```bash
# 初始化数据库
python -m scripts.init_sqlite

# 查看数据库
sqlite3 backend/data/career_assistant.db

# 备份数据库
cp backend/data/career_assistant.db backup.db

# 清空数据库
rm backend/data/career_assistant.db
python -m scripts.init_sqlite
```

### 开发调试

```bash
# 启动后端
cd backend
python main.py

# 启动前端
cd frontend
npm run dev

# 查看 API 文档
# http://localhost:8000/docs
```

---

## 💡 数据库配置

### 当前配置（SQLite）

**文件**: `backend/.env`

```bash
DATABASE_URL=sqlite+aiosqlite:///./data/career_assistant.db
```

### 切换到 PostgreSQL（可选）

如果未来需要切换到 PostgreSQL：

```bash
# 修改 .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/aicareer
REDIS_URL=redis://localhost:6379/0

# 启动 Docker
docker-compose up -d db redis

# 初始化数据库
python -m scripts.init_postgres
```

---

## 📝 开发建议

### 适合使用 SQLite 的场景 ✅
- 个人学习和演示
- 开源项目（降低门槛）
- 原型开发
- 小型应用
- 单用户应用

### 考虑 PostgreSQL 的场景
- 多用户并发写入
- 需要高可用性
- 复杂事务隔离
- 生产环境大规模使用

---

## 🔍 故障排查

### 后端无法启动

```bash
# 检查依赖
pip install -r requirements.txt

# 重新初始化数据库
python -m scripts.init_sqlite

# 查看日志
tail -f backend/logs/ai_career_assistant.log
```

### 前端无法访问

```bash
# 清除缓存
npm run dev -- --force

# 重新安装依赖
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### 数据库问题

```bash
# 数据库被锁定
rm backend/data/career_assistant.db-journal
rm backend/data/career_assistant.db-wal
rm backend/data/career_assistant.db-shm

# 重新初始化
python -m scripts.init_sqlite
```

---

## 📚 文档

- [SQLite 快速启动指南](SQLITE_QUICKSTART.md)
- [回退总结](SQLITE_ROLLBACK_SUMMARY.md)
- [本地开发指南](LOCAL_DEV_SETUP_GUIDE.md)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/your-username/aicareer-assistant.git

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install

# 初始化数据库
python -m scripts.init_sqlite

# 启动服务
python main.py  # 后端
npm run dev     # 前端
```

---

## 📄 License

MIT License

---

## 🎉 致谢

感谢所有贡献者和使用者！

---

**最后更新**: 2026-04-01  
**数据库类型**: SQLite  
**启动脚本**: start-sqlite.py  
**推荐工具**: DB Browser for SQLite
