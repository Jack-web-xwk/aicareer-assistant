"""
Clone/pull ai-daily from Gitee, copy whitelisted Markdown into frontend/public/ai-daily,
and write catalog.json for the AI frontier learning UI.

Requires: git on PATH.
Run from repo root: python backend/scripts/sync_ai_daily.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import datetime as datetime_mod
from pathlib import Path
from typing import Any

GIT_URL = "https://gitee.com/xia-weikun/ai-daily.git"
BRANCH = "main"

# Only these path prefixes (relative to repo root) are published
WHITELIST_PREFIXES = ("daily/", "weekly/", "apps/")

DATE_IN_NAME = re.compile(r"(20\d{2}-\d{2}-\d{2})")
FIRST_HEADING = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _work_dir() -> Path:
    return _repo_root() / "backend" / "data" / "ai-daily-src"


def _out_dir() -> Path:
    return _repo_root() / "frontend" / "public" / "ai-daily"


def _ensure_git_clone(work: Path) -> None:
    work.parent.mkdir(parents=True, exist_ok=True)
    if (work / ".git").is_dir():
        subprocess.run(
            ["git", "-C", str(work), "fetch", "--depth", "1", "origin", BRANCH],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(work), "reset", "--hard", f"origin/{BRANCH}"],
            check=True,
            capture_output=True,
        )
    else:
        if work.exists():
            shutil.rmtree(work)
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                BRANCH,
                GIT_URL,
                str(work),
            ],
            check=True,
            capture_output=True,
        )


def _section_label(relpath: str) -> tuple[str, str]:
    """
    Returns (category_key, display_label) for UI grouping.
    category_key: daily | weekly | apps
    """
    parts = relpath.replace("\\", "/").split("/")
    if len(parts) < 2:
        return "apps", "应用实战"
    top = parts[0]
    if top == "apps":
        return "apps", "应用实战"
    sub = parts[1] if len(parts) > 1 else ""
    sub_map = {
        "models": "大模型",
        "finetune": "微调",
        "inference": "推理加速",
    }
    sub_zh = sub_map.get(sub, sub or "其他")
    if top == "daily":
        return "daily", f"日报 · {sub_zh}"
    if top == "weekly":
        return "weekly", f"周报 · {sub_zh}"
    return "apps", "应用实战"


def _title_from_file(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return path.stem
    m = FIRST_HEADING.search(text)
    if m:
        return m.group(1).strip()[:200] or path.stem
    return path.stem


def _sort_date(relpath: str, title: str) -> str | None:
    m = DATE_IN_NAME.search(relpath)
    if m:
        return m.group(1)
    m2 = DATE_IN_NAME.search(title)
    if m2:
        return m2.group(1)
    return None


def _collect_entries(work: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for p in sorted(work.rglob("*.md")):
        if p.name.startswith("."):
            continue
        try:
            rel = p.relative_to(work).as_posix()
        except ValueError:
            continue
        if rel.upper() == "README.MD":
            continue
        if not any(rel.startswith(pref) for pref in WHITELIST_PREFIXES):
            continue
        title = _title_from_file(p)
        cat_key, section_label = _section_label(rel)
        sort_date = _sort_date(rel, title)
        entries.append(
            {
                "relpath": rel,
                "title": title,
                "category": cat_key,
                "section": section_label,
                "sortDate": sort_date,
            }
        )
    dated = [e for e in entries if e.get("sortDate")]
    undated = [e for e in entries if not e.get("sortDate")]
    dated.sort(key=lambda e: e["sortDate"], reverse=True)
    undated.sort(key=lambda e: e["relpath"], reverse=True)
    return dated + undated


def _copy_markdown(work: Path, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in work.rglob("*.md"):
        if p.name.startswith("."):
            continue
        rel = p.relative_to(work).as_posix()
        if rel.upper() == "README.MD":
            continue
        if not any(rel.startswith(pref) for pref in WHITELIST_PREFIXES):
            continue
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        n += 1
    return n


def main() -> int:
    root = _repo_root()
    work = _work_dir()
    out = _out_dir()
    print(f"[sync_ai_daily] repo root: {root}")
    print(f"[sync_ai_daily] clone/pull -> {work}")
    try:
        _ensure_git_clone(work)
    except subprocess.CalledProcessError as e:
        print(f"[sync_ai_daily] git failed: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr.decode(errors="replace"), file=sys.stderr)
        return 1
    entries = _collect_entries(work)
    copied = _copy_markdown(work, out)
    catalog: dict[str, Any] = {
        "source": "https://gitee.com/xia-weikun/ai-daily",
        "generatedAt": datetime_mod.datetime.utcnow().isoformat() + "Z",
        "entries": entries,
    }
    out.mkdir(parents=True, exist_ok=True)
    catalog_path = out / "catalog.json"
    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[sync_ai_daily] copied {copied} markdown files -> {out}")
    print(f"[sync_ai_daily] catalog: {len(entries)} entries -> {catalog_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
