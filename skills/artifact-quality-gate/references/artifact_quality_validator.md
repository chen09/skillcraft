# Artifact Quality Validator

## Purpose

Prevent low-density agent outputs that look complete but do not answer the user's real goal.

## Scoring Table

| Dimension | Points | Checks |
|---|---:|---|
| User goal answered | 15 | Names task, goal, status, and concrete outcome. |
| Evidence bound | 20 | Uses concrete paths, repo-relative paths, commands, source dates, handoff inventory artifacts, or explicit `evidence_missing`. |
| Structure | 10 | Has skimmable sections and tables/lists where useful. |
| Input/process/output contract | 15 | States inputs, workflow, outputs, completion conditions. |
| Verification | 15 | Includes tests, smoke checks, validator, before/after comparison, score delta, or proof of execution. |
| Real/mock distinction | 10 | Distinguishes `real_execution`, `dry_run`, mock, fixture, semi-real, and `candidate_only`. |
| Repair/rollback | 10 | Includes failure repair, rollback, or next-step recovery. |
| Human entrypoint | 5 | Provides clickable receipt, index, handoff, or quick-open path. |

Thresholds:

- 90-100: ready for review, subject to the local evidence check.
- 75-89: usable, but requires targeted improvement.
- 60-74: draft only.
- below 60: not acceptable for final delivery.

## Local Evidence and Acceptance

`score_threshold` is the band implied by the heuristic score. `threshold` also reflects local path
availability. A `ready` score band becomes `usable` when a reference is missing or no referenced
local path exists. The score itself stays the same.

Use inline or reference-style Markdown links relative to the report, or inline code containing an
absolute path. Use angle brackets for link targets with spaces. The CLI skips fenced examples and
lists web URLs and paths in a foreign platform's format as unchecked. `review.local_evidence` lists
present, missing, and unchecked references.

The CLI reports independent verification as `not_performed` and acceptance as `pending`. Open the
relevant receipts, confirm the result against the task and its acceptance criteria, and record the
checks that still need to happen.

## Rework Task List When Below Threshold

1. Add a one-line TASK/STATUS/OUTPUT entry.
2. Add concrete evidence paths or mark `evidence_missing`.
3. Add verification result and whether it was real, mock, dry-run, or fixture.
4. Add input/output contract.
5. Add rollback or repair path.
6. Add a human-openable entrypoint.

## Handoff-First Artifact Checks

For self-distillation, continuity audit, or cross-agent continuation artifacts, look for:

- `Handoff_Inventory.md` or `handoff_inventory.json` when the artifact claims to summarize local handoff evidence.
- Explicit source roots or an `evidence_missing` explanation when roots were unavailable.
- A clear execution label: `real_execution`, `fixture`, `mock`, `dry_run`, `semi_real`, or `candidate_only`.
- Before/after scores or validator output when the artifact claims a repair or quality improvement.
- A repair path for failed live handoffs instead of silent edits.

## Non-Scoring Handoff Size Gap

For a `handoff.md` larger than 150,000 bytes, accept a non-empty sibling `handoff-history.md`
or an inline or reference-style Markdown link to a non-empty timestamped history file in the
same directory. For example, use `handoff-20261125T012345Z-history.md` or
`handoff-20261125T012345Z-2-history.md` if the first name is taken. The gap check verifies the
archive's location, file type, and size. Compare bytes separately to verify a verbatim split.
When neither form qualifies, add `oversized_handoff_without_history` to the output `gaps` array
and recommend a verified history split. The gap leaves the score and threshold unchanged.
