# Handoff Template

Use this structure for `handoff.md`.

```markdown
# Handoff

## Status
READY TO CONTINUE / NEEDS REVIEW / BLOCKED ON <specific blocker>

## Original Goal
State the user's original task and preserve any binding constraints. Record what must be true
for the task to be complete. Mark any unresolved completion criterion as pending.

## Current State
- Last verified state, when it was checked, and its source (`<file path>`, command result, or output artifact).
- Workspace, branch, revision, or external target when the next step depends on it.
- Assumption: clearly mark unverified but currently useful assumptions.

## Recent Progress
- Verified result, decision, blocker, or next-action change that affects continuation.

## Next Minimal Step
Give one executable action. Point to the exact artifact, section, or command output needed to
start, and state the expected result or check. If the relevant output was truncated, give a
targeted way to retrieve it. Name the live fact to recheck before acting.

## Next 3 Steps
1. Minimal executable step.
2. Minimal executable step.
3. Minimal executable step.

## Unfinished Work
### High
- Item, dependency, and verification method.

### Medium
- Item, dependency, and verification method.

### Low
- Item, dependency, and verification method.

## Blockers
- Blocker:
  - Confirmed cause or labeled hypothesis:
  - Impact:
  - Confidence:
  - Possible workaround:

## Do Not Retry Without New Evidence
- Attempt, observed result, location of the original evidence, and the new evidence needed
  to justify a retry. Label an unconfirmed cause as a hypothesis.

## Files And Artifacts
- Path: purpose / status.
- Path: purpose / status.

## Decisions
- Decision:
  - Reason:
  - Evidence:

## Assumptions
- Assumption:
  - Why it is plausible:
  - How to verify:

## Quick Resume
One short paragraph that a new agent can read in 15 seconds to continue safely.
```

## Quality Bar

- A new agent should be able to act from `Next Minimal Step` without asking for clarification.
- Start the new session by reading the current `handoff.md` and checking the relevant live state.
  If key evidence is missing, read only the relevant excerpts from earlier records.
- The handoff should be useful even if the old conversation context is unavailable.
- For a handoff to another machine, use accessible sources or repository-relative paths with the
  relevant revision. Identify the host and worktree for changes that exist only locally.
- Uncertainty must be explicit.
