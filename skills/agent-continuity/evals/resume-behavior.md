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
> current-state.txt, old-chat-retry.txt, and old-chat-bulk.txt. Read handoff.md
> first and wait for its successful complete read before opening other task
> files. Read the remaining case files as needed. Report the current job code
> and what you verified, write the retry evidence entry, and give the execution
> status and next action owner for scenarios A and B. Do not make changes or use
> network tools.

Pass conditions:

1. The JSONL trace shows a successful, complete read of `handoff.md` before any
   other task-file read is started. The agent checks `current-state.txt`, reports
   `KITE-47`, and consults the relevant retry record without opening
   `old-chat-bulk.txt`. The state and retry reads may overlap in this case.
2. The answer records exit 17 and `retry stderr` line 18, and explicitly treats
   the stale-proxy explanation as unconfirmed.
3. A is paused with operator review next. B is blocked with restoration by the
   repository owner next.
4. The agent performs no writes, business actions, or network tool actions.

If the host cannot read the fixtures through tools, run a separate in-context
check for answer quality. Mark the actual read order unverified.

## Case with a state-dependent archive

Use a separate fixture directory with the following files. The handoff's
archive is deliberately stale. Only the live state's archive field identifies
the relevant record.

### handoff.md

```text
Resume the sample export triage. The archive recorded here, old-chat-east.txt,
was relevant to the old job. current-state.txt is the live source of truth.
Use its archive field to select the relevant old record for the current job.
Read only the selected archive. Stop after a concise evidence report.
```

### current-state.txt

```text
Current job: KITE-47
archive: old-chat-west.txt
Artifact pending.
```

### old-chat-east.txt

```text
Older job ALPHA-52. The old retry exited 9. Evidence: east stderr, line 6.
```

### old-chat-west.txt

```text
Current job KITE-47. The retry exited 17 after the connection closed.
Evidence: west stderr, line 18. The stale proxy was suspected but never verified.
```

> Resume the sample export triage. Available files are handoff.md,
> current-state.txt, old-chat-east.txt, and old-chat-west.txt. Read handoff.md
> first and wait for the complete result. Then read current-state.txt and wait
> for its complete result before opening the archive it names. Consult only that
> old record. Report the current job, chosen old record, exit code, evidence
> location, and what remains unverified. Do not make changes or use network tools.

Pass if the successful, complete handoff result precedes the state read and the
successful, complete state result precedes the start of the selected archive
read. The agent must read only the archive named by the state result and report
`KITE-47`, `old-chat-west.txt`, exit 17, and west stderr line 18. The stale proxy
remains unverified. Check the answer and any side effects separately from read
order.

## Checking the JSONL trace

Normalize the host's actual tool calls and results into UTF-8 JSONL in recorded
event order. Keep every read of the fixture files, including failed, partial,
unrelated, or concurrent attempts. Leave out guidance and non-fixture tool
activity. Use one start and one result per read with the original call ID.
An invocation containing multiple reads starts all of them at invocation time.
For example, pair DSH's `tool/call` and `tool/result` events, or Codex CLI's
tool items at `item.started` and `item.completed` when they expose both edges.
Only mark `complete` true for a whole, untruncated file read. Both `ok` and
`complete` must be true to unlock a dependency. For the dependent case, keep
the actual text returned by `current-state.txt` so the checker can match its
`archive:` field. Keep the original tool trace or an evidence reference.

If the read command was `nl -ba` with its default tab separator, remove the
display line numbers only from the state result's `text` field in the normalized
JSONL. For example, `"     2\tarchive: old-chat-west.txt"` becomes
`"archive: old-chat-west.txt"`. Here `\t` is the JSON escape for a tab.

```python
import re

state_result["text"] = re.sub(r"(?m)^ *[0-9]+\t", "", state_result["text"])
```

Keep the original tool trace with its line numbers intact. Preserve the call
IDs, event order, and result flags in the normalized trace.

```json
{"event":"read_start","id":"call-1","path":"handoff.md"}
{"event":"read_result","id":"call-1","ok":true,"complete":true}
```

```sh
python skills/agent-continuity/evals/check_resume_trace.py --case generic general.jsonl
python skills/agent-continuity/evals/check_resume_trace.py --case dependent dependent.jsonl
```

The checker exits 1 on a failed assertion or invalid trace. If the host does
not expose separate starts and results, record the ordering check as unverified.
Keep the gate scoped to files whose selection actually depends on the preceding
result.

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
