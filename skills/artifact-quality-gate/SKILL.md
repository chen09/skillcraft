---
name: artifact-quality-gate
description: For original-based self-distillation, require original preservation separately from heuristic scoring. Validate reports, receipts, skill candidates, handoffs, handoff-first inventories, research outputs, and implementation summaries for evidence, verification, real-vs-mock clarity, repair path, and human-openable entrypoints. Use when a non-trivial Codex artifact may be too thin, generic, unverified, hard for a human to accept, or claims self-distillation/continuity results that should be grounded in handoff evidence.
---

# Artifact Quality Gate

## Workflow

1. Identify artifact type: report, skill candidate, handoff, receipt, code summary, research output, visual report, or fixture.
2. Score the artifact with the quality table:
   - goal answered;
   - evidence bound;
   - structure;
   - input/process/output contract;
   - verification;
   - real/mock distinction;
   - repair/rollback;
   - human entrypoint.
   For handoff-first artifacts, specifically check whether the artifact cites `Handoff_Inventory.md` or `handoff_inventory.json`, labels execution mode (`real_execution`, `mock`, `fixture`, `dry_run`, or `candidate_only`), and includes before/after or validator results when it claims a repair or quality improvement.
3. If score is below 75, return a rework task list instead of accepting the artifact.
4. If score is 75-89, mark usable with targeted gaps.
5. For scores of 90 or higher, use the CLI's `threshold` to decide whether the artifact is
   ready for review. The CLI checks local references separately from the score. It reports
   `usable` if referenced local paths are missing or there are no checkable local paths.
6. For an input named `handoff.md` that exceeds 150,000 bytes, check for a non-empty sibling
   `handoff-history.md` or a Markdown link to a non-empty timestamped history file in the same
   directory. If neither is present, add the `oversized_handoff_without_history` gap and a rework
   task. The gap leaves the score and threshold unchanged.
7. Before reporting acceptance, open the evidence that supports each key claim, confirm the
   independent check and its result, and list any remaining acceptance items. Report an unavailable
   check as pending. A path check cannot establish the contents of a file or that a test ran.
8. When accepting a handoff for a context reset or transfer to another agent or machine, check
   resumability using only the handoff and its cited sources. Confirm the original constraints
   and completion conditions, locate the evidence needed for the first action, and verify that
   its expected result can be checked. Run a read-only probe in the receiving environment when
   available. If the first action changes state, check a prerequisite without performing the
   action. Record what was checked and the result, and mark any check you could not run pending.


### Blocking original-preservation contract

When the caller requires preservation of an authoritative original, record its source/version,
trusted SHA-256, scope and current artifact before scoring. A high material score cannot override
a failed preservation contract. Ordinary rewrites without this requirement use the existing workflow.

For this user's personal original V1 self-distillation, run `scripts/personal_preservation_contract.py`
with the target Markdown, `--source` and `--expected-source-sha256`. For a completed-cycle claim,
also provide `--require-package --package` with the actual run directory. The caller obtains paths
from the current node; never reuse another node's absolute project paths. Resolve bundled scripts
relative to this skill directory and discover the current Python executable locally.

The validator requires one intact original in a three-backtick text block and the original's phase,
output-name, periodic-cycle and P0 markers. Those markers prove retained requirements only.
Package checking proves nonempty paths only. Neither check proves stage execution, correct evidence
labels, installation, actual triggering or business acceptance. Review dated P0 inputs/results,
per-stage substantive evidence and claims independently, using the caller's claims validator where
available. A preserved handbook must never be reported as a completed new cycle.

Run scripts that write inputs/results only against an isolated copy. Preserve the first-round
receipts and sources. Record the preservation JSON, material-score JSON, source/hash conventions,
Page block ID/hash when applicable, execution modes, installed status, unmet domain checks and
rollback entry. Do not install from this workflow. Retain rejected artifacts; repair candidates in
isolation. Restore only the exact backed-up skill revision after a separately authorized install.

Hashes in this validator cover UTF-8 text with universal newlines normalized to LF. Record raw-byte
hashes separately for installation guards; do not compare the two conventions as content drift.

## Output

Return JSON plus a short Markdown summary. Report the heuristic `score` and `score_threshold`,
the evidence-aware `threshold`, missing or unchecked references from `review.local_evidence`,
and `gaps` such as an oversized handoff. The CLI leaves independent verification and acceptance
pending. Report the actual verification mode and result separately. Never claim real validation
when only mock, fixture, dry-run, or candidate-only validation was performed.

## Evidence Handling

Use concrete local paths, repo-relative paths, command outputs, source dates, handoff inventory artifacts, or `evidence_missing` markers when scoring an artifact. For local `skillcraft` artifacts, cite repo-relative paths such as `skills/artifact-quality-gate/SKILL.md` rather than generic descriptions.

When the artifact is a self-distillation report, receipt, continuity audit, or cross-agent handoff package, treat missing handoff inventory evidence as a targeted rework item rather than accepting a generic summary.

### Claims that an operation ran

When a claim relies on an exported tool receipt, use the approved source and a selector that
matches exactly one record. If a hash is recorded, compare it with the bytes actually read. Read
the outcome from the selected record, including operation-specific skipped, blocked, or `notRun`
fields. Check any quoted receipt against the original. Missing, ambiguous, or mismatched evidence
leaves the claim pending or rejected. A successful tool response can carry a non-execution result.
Record it as skipped or pending. An empty result supports an absence claim only within a checked
scope and time range after the query actually ran.
Record any fallback as its own check, with its method, executor, and result. A projection or an
independent readback does not establish that the original call ran.

Record when the original operation happened and when it was reviewed. Label historical readback,
local replay, current execution, and business acceptance separately. Tie test evidence to the
revision and environment actually tested and state the remaining verification layer explicitly
when a passing test covers only part of the requested behavior.
For a monitor, distinguish a manually successful probe from scheduler execution and actual
coverage of the claimed interval. Silence, empty output, or an exit code alone cannot establish
that all intended events were checked.

References: use `references/artifact_quality_validator.md` for the scoring table and `references/artifact_quality_schema.json` for machine-readable results.

## Smoke Test

Run from the `skillcraft` repository root:

```sh
python3 -X utf8 skills/artifact-quality-gate/scripts/validate_artifact_quality.py README.md
```

Use the available local Python executable. UTF-8 mode keeps multilingual output readable on
Windows consoles with a legacy code page.

Execution mode: `real_execution` for the local command; validator mode remains `heuristic_local_validator`. If the input is a mock, fixture, dry-run, or candidate-only artifact, preserve that label in the result summary.

## Bundled Resources

- `scripts/validate_artifact_quality.py`: heuristic local validator.
- `references/artifact_quality_validator.md`: scoring rubric.
- `references/artifact_quality_schema.json`: machine-readable result schema.
