---
name: codex
description: "Delegate token-heavy or outsourceable tasks to OpenAI Codex CLI to reduce Claude token consumption. Use when the user asks to run, delegate, or outsource a task to Codex — or when the task is large, repetitive, or well-defined enough that Codex can handle it autonomously (e.g. writing tests, refactoring a file, running a code review, bulk edits). Triggers on: codex에게 맡겨줘, codex로 해줘, 외주화해줘, codex 실행해줘, 테스트 codex로 써줘, codex 리뷰 돌려줘."
---

# Codex Delegation Skill

Delegate tasks to Codex CLI to save Claude tokens.

## When to delegate to Codex

- Writing test files (one or more files)
- File-level refactoring
- Code review (`codex review`)
- Repetitive bulk edits (adding comments, type hints, formatting, etc.)
- User explicitly requests "delegate to codex" / "outsource this"

Skip delegation for simple 1–2 line edits or explanation requests — Claude is faster for those.

## Pre-flight check

```bash
codex login status   # expect "Logged in"
```

If it fails, instruct the user to run `codex login`.

## Default execution pattern

```bash
codex exec \
  --cd /path/to/repo \
  --sandbox workspace-write \
  --full-auto \
  --ephemeral \
  --json \
  -o /tmp/codex-result.txt \
  "task instruction"
```

**Fixed option rules:**
- `--cd` — always set to project root
- `--sandbox workspace-write` — default; allows writes while minimising system impact
- `--ephemeral` — prevents session state from leaking between runs
- `-o /tmp/codex-result.txt` — saves output for Claude to review

## Commands by task type

### Code tasks (tests, refactoring, bulk edits)

```bash
codex exec \
  --cd "$(pwd)" \
  --sandbox workspace-write \
  --full-auto \
  --ephemeral \
  -o /tmp/codex-result.txt \
  "task instruction here"
```

### Code review

```bash
codex review --base main "Review for security, performance, and regression risk. Cite file path and line number."
```

Or non-interactive:

```bash
codex exec review \
  --base main \
  --ephemeral \
  -o /tmp/codex-review.txt \
  "Review for security, performance, and regression risk."
```

### Long prompts (stdin)

```bash
cat prompt.txt | codex exec - \
  --cd "$(pwd)" \
  --sandbox workspace-write \
  --full-auto \
  --ephemeral \
  -o /tmp/codex-result.txt
```

## Workflow

1. Identify the task scope and target files from the user request.
2. Write a concrete prompt (more specific = better results).
3. Pick the matching pattern above and run it via Bash.
4. After completion, Read the `-o` file and summarise results for the user.
5. For any follow-up fixes, either handle them directly or re-run Codex.

## Prompt writing tips

A good Codex prompt:
- Names the target files/directories: `inside tests/mcp_server/`
- References existing patterns: `follow the style of test_apartment_trades.py`
- States the done condition: `all tests must pass`
- States constraints: `do not modify any other files`

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `codex: command not found` | Find the absolute path with `which codex` and use it |
| Git repo check fails | Set `--cd` to the repo root, or add `--skip-git-repo-check` |
| Output file missing | Verify the `-o` directory exists |
| Permissions concern | Use `--sandbox read-only` for a dry-run inspection step first |
