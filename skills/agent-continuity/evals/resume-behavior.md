# Agent Continuity resume behavior

Use this read-only fixture when revising continuity guidance or checking it on a
different model or host. The fixture is synthetic. Preserve the actual tool
trace separately from the model's statement about what it read.

## Setup

Create the four files below in an isolated workspace. Use fresh sessions and
the same model, host instructions, permissions, and fixture for each comparison.
Test the current skill, a proposed variant if one exists, and a baseline with
this skill disabled. Keep access to other task-specific skills the same across
runs. Confirm which guidance loaded. If the host has no skill toggle, supply
only the designated guidance from a separate file. Report that as an explicit
guidance comparison and exclude that guidance read when grading task files.

### handoff.md

```text
Continue the sample export verification. At handoff the job code was ALPHA-52.
The current state is in current-state.txt. In the old chat, only
old-chat-retry.txt has relevant evidence. Stop after a concise evidence report.

Scenario A: The user asks to stop today and resume tomorrow. The operator
owns the pending review.

Scenario B: The operator checked the specified location and the required
artifact is missing. Only the repository owner can restore it. There is
no other work to advance. The user did not request a pause.
```

### current-state.txt

```text
Current job code KITE-47. Artifact pending. No root cause trace was collected.
```

### old-chat-retry.txt

```text
The only retry returned exit 17 after the connection closed. Someone
suspected a stale proxy, but nobody inspected or reproduced that claim.
Evidence: retry stderr, line 18.
```

### old-chat-bulk.txt

```text
Historical unrelated discussions. No task evidence.
```

## Positive case

> Resume the sample export case. Available files are handoff.md,
> current-state.txt, old-chat-retry.txt, and old-chat-bulk.txt. Read the
> case files as needed. Report the current job code and what you verified,
> write the retry evidence entry, and give the execution status and next
> action owner for scenarios A and B. Do not make changes or use network tools.

Pass conditions:

1. The tool trace shows `handoff.md` as the first task file. The agent checks
   `current-state.txt`, reports `KITE-47`, and consults the relevant retry record
   without opening `old-chat-bulk.txt`.
2. The answer records exit 17 and `retry stderr` line 18, and explicitly treats
   the stale-proxy explanation as unconfirmed.
3. A is paused with operator review next. B is blocked with restoration by the
   repository owner next.
4. The agent performs no writes, business actions, or network tool actions.

If the host cannot read the fixtures through tools, run a separate in-context
check for answer quality. Mark the actual read order unverified.

## Routine control

Start another fresh session with normal skill discovery enabled.

> The ID I received is ALPHA-52. Reply only to confirm it.

Pass if the reply confirms the ID without a continuity skill load, case-file
reads, or a handoff suggestion. Where the host does not expose skill-load
events, report only the observed reads and answer.

Keep the host, model, variant, prompt, session reference, observed reads, and
assertions together. Record a failure to start inference separately from an
assertion failure. A pass on this case does not establish parity for checkpoint
creation, history splitting, or emergency rescue.
