---
name: git-modular-commits
description: >-
  Splits commits by functional area (backend, frontend, docs, etc.) and
  writes conventional commit messages. Use when the user invokes /git,
  asks to commit by module, wants GitLab-friendly atomic commits, or
  requests规范提交 / 按模块提交.
---

# Git: modular commits by conventional commits

## When to apply

- User says `/git`,「按模块提交」「规范提交」「拆 commit」，或准备提交涉及多目录的改动。
- Goal: **small, reviewable commits** aligned with **repo layout** (this project: `backend/`, `frontend/`, `docs/`, root config).

## Module map (this repository)

| Area | Path(s) | Typical scope |
|------|---------|----------------|
| backend | `backend/` | FastAPI, agents, services, models |
| frontend | `frontend/` | React, pages, API client |
| docs | `docs/`, `README.md`, `AGENTS.md` | Documentation only |
| root | `.cursorrules`, `.gitignore`, scripts at repo root | Tooling / meta |

If a change touches **two areas** (e.g. API + UI), prefer **two commits** unless the team explicitly wants one atomic feature commit.

## Commit message format

Follow **Conventional Commits** (English type + optional scope):

```text
<type>(<scope>): <short subject>

[optional body: why, not how]
```

- **type**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `perf`
- **scope**: `backend`, `frontend`, `docs`, or a concrete module name (e.g. `resume`, `jobs`)
- **Subject**: imperative mood, ~50 chars, no trailing period

Examples:

```text
feat(frontend): add study QA card on resume result step
fix(backend): validate study-qa payload when match_analysis missing
docs: add demo screenshots to README
chore: add git-modular-commits skill
```

## Workflow (agent executes)

1. **`git status`** and **`git diff`** (staged + unstaged) to see all touched paths.
2. **Classify** each file into `backend` / `frontend` / `docs` / `root` (or mixed).
3. **Split**:
   - Stage only files for **one** module: `git add path1 path2`
   - If dependencies force order (e.g. API before UI), commit **backend first**, then **frontend**.
4. **Commit** with one message per logical step.
5. **Push** when user asks; remind that **GitLab CI** (if `.gitlab-ci.yml` exists) runs on push/MR — atomic commits ease bisect and review.

## Rules

- Do **not** mix unrelated concerns in one commit (e.g. unrelated doc typo + API change).
- **Docs-only** changes: use `docs:` or `docs(scope):` without code changes in the same commit.
- **Secrets**: never commit `.env`; only `.env.example` with placeholders.
- If the user prefers **Chinese subjects**, keep **type** and **scope** in English for tooling compatibility, e.g. `feat(frontend): 简历结果页增加学习问答`.

## Anti-patterns

- One giant commit titled `update` spanning backend + frontend + docs.
- Committing generated artifacts or local-only paths unless the project already tracks them.

## Optional: GitLab MR

- Prefer **small MRs** or **clearly ordered commits** so MR diff matches a story.
- If CI is configured, note that failing jobs should be fixed before merge; avoid pushing broken `main`/`master`.
