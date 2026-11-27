# Records and operations

Map these logical records to the control store rather than expecting every system to have the same schema. A board may put task state in project fields and keep source and output records in a linked store. Assign one owner for each piece of state and document where it is stored.

| Record | Minimum fields | Stable identity |
|---|---|---|
| Intake event | Source type, account or tenant, container or conversation, source item ID, source URL if available, author/submitter, capture time, permitted excerpt, reply route if known, linked task ID or triage decision | Source type + installation scope + provider item coordinates |
| Control task | Title, scope and criteria, owner, stage, next action, last verified stage, evidence, decision history | Controller-assigned task ID |
| Output | Task ID, operation, route, target record or conversation, required flag, intended revision, status, authorization reference, attempt information, remote ID/link or verification evidence | Task ID + operation + destination + intended revision |

Use native provider IDs as strings. Encode key components unambiguously. For a proposed creation, use the configured project or destination and a stable creation revision before the remote item ID exists. Keep that creation key when the remote ID is saved. Timeout recovery uses the original operation key. A deliberate new update or reply uses a new revision and, for a reply, authorization for its changed content and target. A routed ledger task may be one of several outputs. Keep all of their IDs when that happens.

## Control and delivery states

| Control stage | What is established |
|---|---|
| `new` / `needs_decision` | At least one source has been captured and is waiting for triage. |
| `ready` / `in_progress` | Scope, owner, criteria, and the next action are recorded. |
| `paused` / `blocked` / `skipped` | The reason is recorded. Keep the last verified stage and the owner of the next action when relevant. |
| `work_verified` | Work meets the recorded criteria. Required delivery may still be pending. |
| `closed` | Work is verified, and every required output has been verified or waived by an authorized owner. |

An output starts at `pending`. Before a write, save the intended payload or its immutable reference, any required authorization, and a `claimed` attempt. Record `accepted` if transport succeeds without readback. Record `verified` after confirming the result at the intended destination. Use `failed` only when no write occurred, `uncertain` when it might have occurred, and `waived` when the authorized owner removes the requirement. A task may remain `work_verified` while one delivery is uncertain.

For concurrent writers, enforce unique event and output keys and use atomic claims or conditional writes. A single-writer profile instead routes all state changes through one serialized writer, including changes initiated by people or flows. Reading an empty row and appending immediately afterward is insufficient when two writers can race.

## Reconcile before retrying

- **Duplicate delivery of an input event:** return the stored decision or task ID. An event from a different source may still link to the same task after triage.
- **A task create or reply times out:** look up the existing target, operation correlation marker, or provider run and thread. If the result is found, record its receipt. Retry only when the result is confirmed absent or the provider supports a true idempotent retry with the same key. An unconfirmed lookup stays `uncertain`.
- **A write partially succeeds:** record the remote objects already created. For example, if a GitHub issue exists but adding it to Projects failed, resume from that issue ID.
- **A route or body changes:** invalidate the previous approval for that operation. Keep the old attempt history.
- **A source or output becomes inaccessible:** preserve links and IDs, report the gap, and leave the affected stage open.

For a mixed-source example, a Slack thread and an email can link to one task after triage. Asana writeback and a Slack reply then have separate output keys. If Asana is verified and the Slack send is uncertain, reconcile the Slack thread and leave the Asana output alone.

A run is reviewable when a new operator can trace an input to its task, read the criteria and evidence, and tell which output needs action without replaying successful writes.
