# SQLite 数据库快速启动指南

## 🎯 为什么选择 SQLite？

对于个人学习和开源项目，SQLite 是最佳选择：

### 优势
- ✅ **零配置**：无需安装数据库服务
- ✅ **单文件**：数据存储在单个文件中，便于备份
- ✅ **开箱即用**：clone 项目即可运行
- ✅ **无依赖**：不需要 Docker、PostgreSQL、Redis
- ✅ **适合演示**：便于分享和展示
- ✅ **足够性能**：个人使用完全足够

### 何时需要 PostgreSQL？
- 需要多用户并发写入
- 需要高可用性和集群
- 需要复杂的事务隔离
- 生产环境大规模使用

---

## 🚀 快速开始

### 步骤 1：安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 步骤 2：初始化数据库

```bash
cd backend
python -m scripts.init_db
```

### 步骤 3：启动后端服务

```bash
cd backend
python main.py
```

### 步骤 4：启动前端服务

```bash
cd frontend
npm run dev
```

### 步骤 5：访问应用

```
http://localhost:5173
```

---

## 📊 配置文件

### `backend/.env`

```bash
# 数据库配置（SQLite）
DATABASE_URL=sqlite+aiosqlite:///./data/career_assistant.db

# 其他配置...
```

---

## 📁 数据库文件位置

```
backend/
├── data/
│   └── career_assistant.db    # SQLite 数据库文件
└── uploads/                    # 上传的简历文件
```

---

## 🔧 常用操作

### 查看数据库

```bash
# 使用 SQLite 命令行工具
sqlite3 backend/data/career_assistant.db

# 查看所有表
sqlite3 backend/data/career_assistant.db ".tables"

# 查看简历数据
sqlite3 backend/data/career_assistant.db "SELECT * FROM resumes;"

# 查看用户数据
sqlite3 backend/data/career_assistant.db "SELECT * FROM users;"
```

### 备份数据库

```bash
# 复制数据库文件即可
cp backend/data/career_assistant.db backup.db

# 或者导出为 SQL
sqlite3 backend/data/career_assistant.db .dump > backup.sql
```

### 恢复数据库

```bash
# 从备份恢复
cp backup.db backend/data/career_assistant.db

# 或者从 SQL 导入
sqlite3 backend/data/career_assistant.db < backup.sql
```

### 清空数据库

```bash
# 删除数据库文件（重新初始化会重新创建）
rm backend/data/career_assistant.db

# 重新初始化
python -m scripts.init_db
```

---

## ️ 数据库管理工具

### 推荐工具

1. **DB Browser for SQLite**（图形化）
   - 官网：https://sqlitebrowser.org/
   - 跨平台、免费、开源
   - 可视化编辑数据

2. **SQLite Studio**（图形化）
   - 官网：https://sqlitestudio.pl/
   - 功能强大、免费

3. **命令行工具**
   ```bash
   sqlite3 backend/data/career_assistant.db
   ```

---

## 📝 数据迁移

### 从 PostgreSQL 迁移到 SQLite

如果之前使用 PostgreSQL，可以：

1. **从 PostgreSQL 导出数据**
   ```bash
   pg_dump -U username -d aicareer -f export.sql
   ```

2. **转换为 SQLite 格式**
   - 使用工具：https://github.com/dumblob/pg2sqlite
   - 或手动导入到 SQLite

3. **或者直接重新开始**
   - 删除 SQLite 数据库文件
   - 运行 `python -m scripts.init_db`
   - 重新创建用户和数据

---

## 🎯 开发建议

### 适合使用 SQLite 的场景
- ✅ 个人学习和演示
- ✅ 开源项目（降低使用门槛）
- ✅ 原型开发
- ✅ 小型应用
- ✅ 单用户应用

### 考虑使用 PostgreSQL 的场景
- 📊 多用户并发访问
- 📊 企业级应用
- 📊 需要高可用性
- 📊 复杂查询和事务

---

## 💡 性能优化

虽然使用 SQLite，但也可以优化：

### 1. 启用 WAL 模式（Write-Ahead Logging）

```sql
PRAGMA journal_mode=WAL;
```

### 2. 增加缓存

```sql
PRAGMA cache_size=-64000;  -- 64MB 缓存
```

### 3. 定期清理

```sql
VACUUM;  -- 整理数据库文件
```

---

## 🔍 故障排查

### 问题 1：数据库文件不存在

**症状**：
```
sqlite3.OperationalError: unable to open database file
```

**解决**：
```bash
# 确保 data 目录存在
mkdir -p backend/data

# 重新初始化
python -m scripts.init_db
```

### 问题 2：数据库被锁定

**症状**：
```
sqlite3.OperationalError: database is locked
```

**解决**：
```bash
# 1. 关闭所有访问数据库的程序
# 2. 删除可能存在的锁文件
rm backend/data/career_assistant.db-journal
rm backend/data/career_assistant.db-wal
rm backend/data/career_assistant.db-shm

# 3. 重启后端服务
```

### 问题 3：表不存在

**症状**：
```
sqlite3.OperationalError: no such table: xxx
```

**解决**：
```bash
# 重新初始化数据库
python -m scripts.init_db
```

---

## 📋 总结

### SQLite vs PostgreSQL

| 特性 | SQLite | PostgreSQL |
|------|--------|------------|
| **配置复杂度** | ⭐ 零配置 | ⭐⭐⭐⭐ 需要安装 |
| **使用门槛** | ⭐ 极低 | ⭐⭐⭐ 需要数据库知识 |
| **备份难度** | ⭐ 复制文件 | ⭐⭐⭐ 需要导出工具 |
| **并发性能** | ⭐⭐ 单线程写入 | ⭐⭐⭐⭐⭐ 高并发 |
| **适用场景** | 个人/学习/演示 | 企业/生产环境 |

### 推荐配置

**现阶段（学习 + 开源）**：
- ✅ SQLite + 本地文件存储
- ✅ 简单部署，开箱即用
- ✅ 专注功能开发

**未来（如果需要）**：
- 📊 PostgreSQL + Redis
- 📊 Docker 部署
- 📊 生产环境优化

---

**最后更新**：2026-04-01  
**数据库版本**：SQLite 3.x  
**推荐工具**：DB Browser for SQLite
