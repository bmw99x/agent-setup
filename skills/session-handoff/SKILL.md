---
name: session-handoff
description: "Session handoff — preserve context across AI agent sessions. Use this skill when you need to save state, create a handoff, pause work, load a handoff, resume from a previous session, context is getting full (80%+), a major task milestone is completed, or you are switching tasks and need continuity. Proactively create handoffs after substantial work (5+ file edits, complex debugging, architecture decisions)."
---

# Session Handoff Skill

## Overview

Creates comprehensive handoff documents that enable fresh AI agents to seamlessly continue work with zero ambiguity. Solves the long-running agent context exhaustion problem by preserving complete context, decisions, and state across sessions.

## Purpose

- **Preserve context** - Capture all critical information before context window fills
- **Enable continuity** - Allow new agents to pick up exactly where you left off
- **Document decisions** - Record architectural choices and their rationale
- **Track progress** - Maintain clear status of completed and pending work
- **Chain sessions** - Link related handoffs for long-running projects

## When to Use

### User-Triggered

- User says "save state", "create handoff", "I need to pause"
- User requests "load handoff", "resume from", "continue where we left off"
- User mentions "context is getting full" or "save this for later"

### Agent-Triggered (Proactive)

- Context window approaching capacity (>80% full)
- Major task milestone completed
- Work session ending with significant progress
- After substantial work (5+ file edits, complex debugging, architecture decisions)
- Before switching to a different task

### Resumption Scenarios

- Starting a new session on an existing project
- Different agent needs to continue the work
- Need to recall decisions made in previous sessions
- Picking up after a long break

## How It Works

### CREATE Mode

Generates a comprehensive handoff document capturing current state:

1. **Generate Scaffold** - Pre-fill metadata (timestamp, git status, modified files)
2. **Complete Document** - Fill in critical sections (state, context, decisions, next steps)
3. **Validate** - Check for completeness, quality, and security
4. **Confirm** - Present location and summary to user

### RESUME Mode

Loads and validates existing handoff documents:

1. **Find Handoffs** - List available handoffs in project
2. **Check Staleness** - Assess if context is still current
3. **Load Document** - Read handoff (and chain if linked)
4. **Verify Context** - Validate assumptions and environment
5. **Begin Work** - Start from "Immediate Next Steps"

## Handoff Document Structure

A complete handoff includes:

1. **Metadata** - Timestamp, project path, git branch, commits
2. **Current State Summary** - What's happening right now
3. **Important Context** - Critical information for next agent
4. **Decisions Made** - Architectural choices with rationale
5. **Immediate Next Steps** - Clear, actionable first steps
6. **Pending Work** - Remaining tasks and priorities
7. **Critical Files** - Important locations and their purpose
8. **Key Patterns Discovered** - Conventions and approaches
9. **Potential Gotchas** - Known issues and workarounds
10. **Handoff Chain** - Links to previous/next handoffs

See [references/handoff-template.md](references/handoff-template.md) for the complete template.

## Storage Location

Handoffs are stored in: `.claude/handoffs/`

Naming convention: `YYYY-MM-DD-HHMMSS-[slug].md`

Example: `2024-01-15-143022-implementing-auth.md`

## Handoff Chaining

For long-running projects, chain handoffs together:

```
handoff-1.md (initial work)
    ↓
handoff-2.md --continues-from handoff-1.md
    ↓
handoff-3.md --continues-from handoff-2.md
```

Each handoff links to its predecessor, providing context breadcrumbs for new agents.

## Validation & Quality Assurance

When validating a handoff, check:

- No incomplete `[TODO: ...]` placeholders
- All required sections populated
- No potential secrets (API keys, passwords, tokens)
- Referenced files exist
- Quality score ≥ 70

## Staleness Detection

When resuming, assess:

- Time elapsed since handoff creation
- Git commits made since handoff
- Files changed since handoff
- Branch divergence
- Missing referenced files

## Quality Standards

Do not finalize a handoff if:

- Validation score is below 70
- Secrets are detected
- `[TODO: ...]` placeholders remain
- Required sections are empty

Best practices:

- Write clear, specific next steps (not vague goals)
- Document the "why" behind decisions, not just the "what"
- Include code snippets for critical patterns
- Reference specific file paths and line numbers
- Update handoffs as work progresses

## References

- [handoff-template.md](references/handoff-template.md) - Complete template structure with guidance
- [resume-checklist.md](references/resume-checklist.md) - Verification checklist for resuming agents

## Benefits

- Zero ambiguity — new agents know exactly what to do
- Context preservation — no loss of critical information
- Decision history — understand why choices were made
- Reduced onboarding — faster agent startup on existing work
- Quality assurance — automated validation prevents incomplete handoffs
- Security — secret detection prevents credential leaks
- Long-term memory — handoff chains maintain project history
