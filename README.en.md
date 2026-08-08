# VibeCodingTemplate

> An AI coding governance template for multi-language projects.
> Provides project constitution (AGENTS.md), domain-specific skills, automated verification scripts, and CI/CD scaffolding.
> Designed for use with Claude Code, Codex, Copilot, Windsurf, and other AI coding assistants.

[中文文档](README.md) | **English**

---

## What This Project Is

VibeCodingTemplate is a **meta-project template** — not a specific application, but a governance framework you clone to start a new project. It encodes senior-engineer project governance knowledge into machine-readable, auto-verifiable rules.

**Core problems it solves:**

1. **AI hallucination governance** — AI assistants invent APIs, cross architectural boundaries, ignore constraints. This template provides AGENTS.md (project constitution) + anti-hallucination rules + closed-loop verification scripts.
2. **Documentation drift** — Function counts, signatures, and structure info get hardcoded in multiple places. This template enforces SSOT (Single Source of Truth) with automated consistency checking.
3. **Engineering knowledge transfer** — Each new project starts from zero. This template distills anti-pattern case libraries from 5 real projects' commit histories into executable rules.

## Quick Start

### Option A: Full initialization (interactive)

```powershell
# Windows (PowerShell)
.\scripts\init-project.ps1 -Target C:\Projects\MyNewProject -GitInit
```

```bash
# Linux / macOS (Python 3.10+)
python scripts/init-project.py /path/to/MyNewProject --git-init
```

### Option B: Parameterized initialization

```bash
python scripts/init-project.py /path/to/MyNewProject \
    --values '{"PROJECT_NAME": "MyApp", "VERSION": "1.0.0", "AUTHOR": "Your Name"}' \
    --git-init --create-compatibility-links
```

### Verify

```bash
# Cross-platform (Python)
python scripts/verify-all.py

# Windows only (PowerShell)
.\scripts\verify-all.ps1
```

## Key Concepts

| Concept | File | Purpose |
|---------|------|---------|
| Project constitution | `AGENTS.md` | Global architecture, red lines, core workflows |
| SSOT | `rules/api-reference.md` | Single source for function signatures |
| Domain terms | `rules/context.md` | Single source for terminology |
| Project structure | `rules/project-structure.md` | Single source for file layout |
| Code review | `rules/code-review-prompt.md` | Tiered review templates (Min/Standard/Max) |
| Cross-project lessons | `rules/cross-project-synthesis.md` | Anti-pattern library from 5 real projects |

## Supported Languages

| Language | Skill file | NewModule templates |
|----------|-----------|---------------------|
| C# / Excel-DNA | `skills/csharp-SKILL.md` | Core.cs + Udf.cs + Foundation.cs + Tests.cs |
| Python | `skills/python-SKILL.md` | Core.py + test + CrossVal.py |
| VBA | `skills/vba-SKILL.md` | Udf.bas + VariantKit.bas |
| TypeScript | `skills/typescript-SKILL.md` | Core.ts + test |
| Go | `skills/go-SKILL.md` | Core.go + Core_test.go |

## Three Expert Skills (Refactoring Lifecycle)

```
Architecture Reviewer (pre-decision) → Should we do this?
        ↓
Refactoring Guardian (during execution) → Did we introduce regressions?
        ↓
Project Plan Reviewer (post-execution) → Did the plan work?
```

## CI/CD Pipeline

| Workflow | Purpose |
|----------|---------|
| `ci.yml` | Layered quality gate (quick / full / quality / template-self-test) |
| `security.yml` | CodeQL scanning (PR + scheduled) |
| `release.yml` | release-please auto-release (Conventional Commits driven) |
| `stale.yml` | Auto-close stale Issues/PRs |
| `dependabot.yml` | Dependency auto-update |

## License

MIT — see [LICENSE](LICENSE)
