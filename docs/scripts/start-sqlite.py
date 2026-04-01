#!/usr/bin/env python3
"""
SQLite 快速启动脚本

一键启动 SQLite 版本的 AI Career Assistant
适合个人学习和开源项目使用。
"""

import subprocess
import sys
from pathlib import Path


def print_banner(text: str):
    """打印标题"""
    print("=" * 60)
    print(text.center(60))
    print("=" * 60)
    print()


def check_dependencies():
    """检查依赖"""
    print_banner("检查依赖")
    
    try:
        import sqlalchemy
        import aiosqlite
        print("✅ SQLAlchemy 已安装")
        print("✅ aiosqlite 已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖：{e}")
        print("\n请运行：pip install -r requirements.txt")
        sys.exit(1)


def init_database():
    """初始化数据库"""
    print_banner("初始化 SQLite 数据库")
    
    backend_dir = Path(__file__).parent / "backend"
    script = backend_dir / "scripts" / "init_sqlite.py"
    
    if not script.exists():
        print(f"❌ 初始化脚本不存在：{script}")
        sys.exit(1)
    
    result = subprocess.run(
        [sys.executable, "-m", "scripts.init_sqlite"],
        cwd=backend_dir,
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print("\n❌ 数据库初始化失败")
        sys.exit(1)
    
    print("\n✅ 数据库初始化成功！")


def start_backend():
    """启动后端服务"""
    print_banner("启动后端服务")
    
    backend_dir = Path(__file__).parent / "backend"
    main_py = backend_dir / "main.py"
    
    if not main_py.exists():
        print(f"❌ main.py 不存在：{main_py}")
        sys.exit(1)
    
    print("后端服务启动命令：")
    print(f"  cd {backend_dir}")
    print(f"  python main.py")
    print()
    print("访问 API 文档：http://localhost:8000/docs")


def start_frontend():
    """启动前端服务"""
    print_banner("启动前端服务")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在：{frontend_dir}")
        sys.exit(1)
    
    print("前端服务启动命令：")
    print(f"  cd {frontend_dir}")
    print(f"  npm run dev")
    print()
    print("访问应用：http://localhost:5173")


def main():
    """主函数"""
    print_banner("AI Career Assistant - SQLite 快速启动")
    
    # 1. 检查依赖
    check_dependencies()
    
    # 2. 初始化数据库
    init_database()
    
    # 3. 启动后端
    start_backend()
    
    # 4. 启动前端
    start_frontend()
    
    # 5. 显示完成信息
    print_banner("启动完成")
    print("📋 下一步:")
    print()
    print("  1. 在新终端运行后端服务:")
    print(f"     cd {Path(__file__).parent / 'backend'}")
    print("     python main.py")
    print()
    print("  2. 在另一个终端运行前端服务:")
    print(f"     cd {Path(__file__).parent / 'frontend'}")
    print("     npm run dev")
    print()
    print("  3. 访问应用:")
    print("     http://localhost:5173")
    print()
    print("💡 提示:")
    print("  - 数据库文件：backend/data/career_assistant.db")
    print("  - 备份数据库：复制 data 目录即可")
    print("  - 查看数据：sqlite3 backend/data/career_assistant.db")
    print()
    print(" 祝您使用愉快！")
    print()


if __name__ == "__main__":
    main()
