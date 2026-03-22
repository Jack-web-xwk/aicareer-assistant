"""
Project CLI entrypoint.

默认进入交互式菜单（PowerShell 循环选 1/2/3 启动服务）；
也可传入参数一次性启动 all / frontend / backend。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python cli.py",
        description="AI Career Assistant — 启动本地前后端服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py              进入交互菜单（推荐）
  python cli.py all          一次启动后端 + 前端（新窗口）
  python cli.py frontend     仅启动前端
  python cli.py backend      仅启动后端
        """.strip(),
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="interactive",
        choices=["interactive", "all", "frontend", "backend"],
        help="interactive=菜单循环；all/frontend/backend=单次启动后退出（默认: interactive）",
    )
    return parser


def run_ps1(mode: str) -> int:
    project_root = Path(__file__).resolve().parent
    ps1_path = project_root / "scripts" / "start-services.ps1"

    if not ps1_path.exists():
        print(f"错误: 未找到脚本 {ps1_path}", file=sys.stderr)
        return 1

    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ps1_path),
        "-Mode",
        mode,
    ]

    print("—" * 52)
    print("  AI Career Assistant · 正在调用启动脚本…")
    print("  脚本路径:", ps1_path)
    if mode == "interactive":
        print("  模式: 交互菜单（输入数字选择服务，0 退出）")
    else:
        print(f"  模式: 单次启动 → {mode}")
    print("—" * 52)
    print()

    completed = subprocess.run(command, cwd=project_root, check=False)
    return completed.returncode


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return run_ps1(args.target)


if __name__ == "__main__":
    raise SystemExit(main())
