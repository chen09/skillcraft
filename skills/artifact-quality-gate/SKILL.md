---
name: artifact-quality-gate
description: Validate reports, receipts, skill candidates, handoffs, handoff-first inventories, research outputs, and implementation summaries for evidence, verification, real-vs-mock clarity, repair path, and human-openable entrypoints. Use when a non-trivial Codex artifact may be too thin, generic, unverified, hard for a human to accept, or claims self-distillation/continuity results that should be grounded in handoff evidence.
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
6. For an input named `handoff.md`, record an `oversized_handoff_without_history` gap when the
   file exceeds 150,000 bytes and has no non-empty sibling `handoff-history.md`. This gap adds a
   rework task but does not change the score or threshold.
7. Before reporting acceptance, open the evidence that supports each key claim, confirm the
   independent check and its result, and list any remaining acceptance items. Report an unavailable
   check as pending. A path check cannot establish the contents of a file or that a test ran.
8. When accepting a handoff for a context reset or transfer to another agent or machine, check
   resumability using only the handoff and its cited sources. Confirm the original constraints
   and completion conditions, locate the evidence needed for the first action, and verify that
   its expected result can be checked. Run a read-only probe in the receiving environment when
   available. If the first action changes state, check a prerequisite without performing the
   action. Record what was checked and the result, and mark any check you could not run pending.

## Output

Return JSON plus a short Markdown summary. Report the heuristic `score` and `score_threshold`,
the evidence-aware `threshold`, missing or unchecked references from `review.local_evidence`,
and `gaps` such as an oversized handoff. The CLI leaves independent verification and acceptance
pending. Report the actual verification mode and result separately.

## Evidence Handling

Use concrete local paths, repo-relative paths, command outputs, source dates, handoff inventory artifacts, or `evidence_missing` markers when scoring an artifact. For local `skillcraft` artifacts, cite repo-relative paths such as `skills/artifact-quality-gate/SKILL.md` rather than generic descriptions.

When the artifact is a self-distillation report, receipt, continuity audit, or cross-agent handoff package, treat missing handoff inventory evidence as a targeted rework item rather than accepting a generic summary.

References: use `references/artifact_quality_validator.md` for the scoring table and `references/artifact_quality_schema.json` for machine-readable results.

## Smoke Test

Run from the `skillcraft` repository root:

```sh
python3 skills/artifact-quality-gate/scripts/validate_artifact_quality.py README.md
```

Execution mode: `real_execution` for the local command; validator mode remains `heuristic_local_validator`. If the input is a mock, fixture, dry-run, or candidate-only artifact, preserve that label in the result summary.

## Bundled Resources

- `scripts/validate_artifact_quality.py`: heuristic local validator.
- `references/artifact_quality_validator.md`: scoring rubric.
- `references/artifact_quality_schema.json`: machine-readable result schema.
