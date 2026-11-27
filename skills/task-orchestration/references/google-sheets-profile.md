# Google Sheets control store profile

Use this pilot layout when one person or one runner can serialize all writes. Keep spreadsheet access scoped to authorized operators. A board can use the same contract if its fields and related records can represent the same state.

Create three tabs with these header rows. Format IDs as plain text and use one consistent UTC timestamp format.

```text
Intake: source_key, source_type, source_scope, source_item_id, source_url, author_or_submitter, captured_at, excerpt, reply_route, task_id, triage_decision
Tasks: task_id, title, scope, acceptance_criteria, owner, due_at, stage, last_verified_stage, next_action, evidence_links, decision_history
Outputs: output_key, task_id, operation, destination, intended_revision, required, status, payload_ref, approval_ref, attempt_ref, remote_id, remote_url, verified_at, last_error
```

Example routing profile for a pilot, with destinations supplied in the new environment:

| Binding | Example |
|---|---|
| Input | One allowlisted Teams channel through Power Automate. Use a permitted staging inbox if the intake flow cannot share the serialized writer. |
| Status owner | `Tasks` tab. The controller updates it and links intake and outputs by `task_id`. |
| Business ledger | One Asana project. Save the task GID and URL. Reopen the same task to verify completion or updates. |
| Required reply | Original Teams channel thread. Save the verified reply ID and link, or the approved verification reference. |
| Authorization | The operator decides create/link/skip during triage and approves the exact reply before sending. |

The writer looks up `source_key`, `task_id`, and `output_key` before creating or updating rows. Keep lookup and write in the same serialized operation. Have flows and collaborators submit inputs to that writer or a staging inbox. Do not also allow them to write directly to the control tabs. If a flow cannot persist through the writer, have the writer reserve the approved output, invoke the flow once, reconcile its run, and persist the receipt. Use manual reply with receipt capture if the flow cannot be restricted to that invocation path.

For GitHub Projects as the business ledger, save the issue ID and Projects item ID separately. Handle a successful issue creation before retrying board placement. [Asana task API](https://developers.asana.com/reference/tasks), [GitHub Projects API](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects).
