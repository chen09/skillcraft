---
name: "agent-continuity"
description: "Use when a long-running agent task needs continuity across context resets, agent restarts, or takeover by another agent. Supports proactive checkpointing during healthy execution and emergency rescue handoff when an agent is stalled, drifting, looping, over-context, or timing out. Produces or updates handoff.md so a new agent can continue without relying on hidden conversation context."
---

# Agent Continuity

This skill externalizes task state into `handoff.md`. It is not multi-agent orchestration and not background-agent management. It is for preserving continuity when one agent may need to stop and another agent must resume safely.

Objective: produce a validator-ready continuity entrypoint that lets a new agent continue from concrete evidence instead of hidden conversation context.

## Modes

### 1. Checkpoint Mode

Use when the current agent is still healthy, but the task is long, context is growing, or the user wants restartability.

Goal: update `handoff.md` after meaningful progress, usually every 1-2 steps.

Rules:

- Record confirmed state, not vague memory.
- Keep the next step minimal and executable.
- Include evidence: file paths, commands, outputs, decisions.
- Do not expand scope while checkpointing.
- Preserve important history; do not overwrite blockers or do-not-retry notes.
- Before appending, check the handoff size. Above 150,000 bytes, report the size and propose a
  split before the next checkpoint; do not split automatically.
- For an approved split, preserve the existing handoff verbatim in the first unused history path:
  use sibling `<name>-history.md` initially, then collision-safe
  `<name>-<UTC timestamp>-history.md` paths (plus a numeric suffix if needed). Verify each copy
  with a byte-for-byte comparison or cryptographic hash before replacing the current handoff,
  and keep the new `handoff.md` as the small current-truth layer. Never summarize, normalize, or
  overwrite preserved history.

### 2. Rescue Mode

Use when the current agent is stalled, drifting, looping, over-context, timing out, or no longer safe to continue.

Goal: within 90 seconds, recover enough state for a fresh agent to continue.

Rules:

- Read `handoff.md` first. If missing, create a minimal one.
- Read only directly relevant files and files referenced by `handoff.md`.
- Pick exactly one safe highest-priority action that can be done within 90 seconds.
- Execute that action, or record the blocker once.
- Do not run long commands, broad searches, or retry loops.
- Do not perform destructive operations.
- Update `handoff.md` before stopping.

## Required Handoff File

Default path: `handoff.md` at the task root unless the user specifies another path.

For self-distillation, continuity audits, or large generated artifact packages, the task root may be the output directory rather than a source repository. In that case, create or update `<output-root>/handoff.md` and record the generated reports, inventories, validator outputs, and the next safe action there. Do not skip the handoff just because no source project files were edited.

Use the structure in `references/handoff-template.md`.

Required properties:

- The `## Status` section starts exactly with one status label: `READY TO CONTINUE`, `NEEDS REVIEW`, or `BLOCKED ON <specific blocker>`.
- Every major claim includes evidence or is marked `Assumption`.
- Contains one highest-priority next step and three minimal next steps.
- Contains do-not-retry guidance for failed actions.
- Ends with a 15-second quick resume note.

## Operating Procedure

Inputs:

- User's original goal and current task root or output root.
- Existing `handoff.md`, if present.
- Directly relevant files, commands, validator output, and generated artifacts.
- Known blockers, failed retries, decisions, and assumptions.

Workflow:

1. Identify mode: Checkpoint or Rescue.
2. Locate or create `handoff.md`.
3. Read only enough context to update it accurately.
4. Update the handoff using the required structure.
5. If code or files changed, include exact paths and verification status.
6. If blocked, record the blocker, likely cause, and safest next action.
7. Validate the handoff with `scripts/validate_handoff.py` before claiming it is ready.

## Output Contract

- A `handoff.md` file at the task root or user-specified output root.
- `## Status` starts with `READY TO CONTINUE`, `NEEDS REVIEW`, or `BLOCKED ON <specific blocker>`.
- `## Next Minimal Step` gives one executable next action.
- `## Files And Artifacts` cites concrete paths and validation state.
- `## Quick Resume` gives a 15-second continuation note.

Completion criteria:

- The handoff exists at the selected continuity entrypoint.
- The next agent can execute `## Next Minimal Step` without hidden chat context.
- The handoff records validation status or explains why validation is blocked.

## Verification And Evidence Mode

Run the validator before claiming the handoff is ready:

```sh
python3 scripts/validate_handoff.py handoff.md
```

The validator exits successfully for a structurally valid handoff even when it prints a size
warning. A warning above 150,000 bytes is a prompt to propose a verified history split, not a
validation failure.

Use `real_execution` when the handoff describes real task state. Use `fixture`, `mock`, `dry_run`, or `candidate_only` labels in the handoff when it describes examples, tests, or proposed changes. For handoff-first audits that have no inventory yet, mark `evidence_missing` and record the next step to collect one.

## References

- `references/handoff-template.md`: canonical handoff structure.
- `references/checkpoint-mode.md`: prompt and rules for proactive checkpointing.
- `references/rescue-mode.md`: prompt and rules for emergency rescue.
- `references/comparison-notes.md`: why this differs from multi-agent handoff and background-agent management.

## Scripts

- `scripts/validate_handoff.py`: validates required sections and warns, without failing, when a
  handoff exceeds 150,000 bytes.
