---
name: handoff-evidence-collector
description: Collect, classify, and validate local handoff files across Codex, Cursor, other agents, and project directories as evidence for continuation, audits, skill evolution, self-distillation, and project status. Use this as the first step when the user mentions self-distillation, continuity audits, cross-agent continuation, collected handoffs, agent-continuity handoff, Cursor handoff, or wants an agent to learn from prior handoff files under user-supplied project roots.
---

# Handoff Evidence Collector

## Goal

Turn scattered `handoff.md`, `*handoff*.md`, Cursor handoff docs, other-agent handoff notes, and agent-continuity handoffs into a usable evidence index without rewriting project files.

For self-distillation and continuity audits, run this skill before writing the report. The inventory becomes the evidence base that later artifacts should cite and that `artifact-quality-gate` can validate.

## Inputs

- Project roots supplied with repeatable `--root` arguments; if omitted, the scanner defaults to the current working directory. `HANDOFF_EVIDENCE_ROOTS` may provide an `os.pathsep`-separated root list.
- Known continuity tooling, especially the sibling `skills/agent-continuity/scripts/validate_handoff.py` validator in this repository. Use `--validator-path <path>` when the validator is installed elsewhere.
- User-provided project priority or time range.
- Do not hardcode one machine's project paths in reusable prompts, README examples, or smoke tests. Accept roots from the user, the current repo, environment variables, or local project markers.

## Workflow

1. Bounded scan:
   - walk only approved project roots;
   - skip `.git`, `node_modules`, model/checkpoint/cache/data/output directories;
   - cap depth unless the user approves a deeper scan.
2. Classify each handoff:
   - `agent_continuity_handoff`;
   - `cursor_handoff`;
   - `usage_handoff_or_guide`;
   - `handoff_like`;
   - `handoff_history` for evidence-only `<name>-history.md` files outside template/reference
     locations;
   - `template_or_reference`.
3. Validate only true `agent_continuity_handoff` files with the project validator.
4. Keep history and other non-continuity handoffs as evidence, but do not fail them against the
   continuity template.
5. Output a Markdown inventory and JSON index with path, kind, byte size, oversized status,
   mtime, validation status, and recommended next action.

## Bundled Resources

- `scripts/handoff_inventory.py`: bounded scanner/classifier for user-supplied roots or the current workspace.
- `scripts/validate_artifact_quality.py`: local artifact quality validator used after inventory generation.
- `references/handoff_quality_validator.md`: classification and repair rules for handoff files.
- `references/artifact_quality_validator.md`: scoring table for output quality.
- `references/artifact_quality_schema.json`: JSON schema for validator output.

## Smoke Test

Run from the `skillcraft` repository root or another writable workspace:

```sh
python3 skills/handoff-evidence-collector/scripts/handoff_inventory.py \
  --output-root /tmp/handoff-evidence-smoke-output \
  --root skills/handoff-evidence-collector/examples/smoke-root \
  --root skills/agent-continuity/references \
  --validator-path skills/agent-continuity/scripts/validate_handoff.py \
  --execution-mode fixture
python3 skills/handoff-evidence-collector/scripts/validate_artifact_quality.py /tmp/handoff-evidence-smoke-output/Handoff_Inventory.md
```

Execution mode: `fixture` when using the bundled smoke root, and `real_execution` when scanning real user/project roots. The scanner is read-only against source project roots and writes only to the requested output root. If a future run uses mock, fixture, dry-run, or candidate-only data, label that explicitly in the inventory.

Expected:

- finds handoff-like files under the supplied roots;
- validates true agent-continuity handoffs only;
- writes JSON/Markdown inventory to the configured output root;
- records the configured validator path and whether it exists;
- records `size`, `size_bytes`, and `oversized` for readable files, using a strict
  `> 150000`-byte warning threshold;
- records the threshold itself as `size_warning_threshold_bytes` and surfaces size/oversized
  columns in Markdown;
- does not edit project files.

## Output Contract

- `handoff_inventory.json`
- `Handoff_Inventory.md`
- validation results for agent-continuity handoffs
- repair candidates for failed handoffs
- evidence-only records for history files and templates/reference guides

For compatibility, each readable JSON record retains the existing `size` field and also exposes
the explicit alias `size_bytes`; both are byte counts. `oversized` is true only when the byte count
is greater than 150,000. Validator stdout/stderr remain unchanged in JSON, while embedded newlines
and table delimiters are escaped in the Markdown view.

## Evidence Handling

Use repo-relative paths, generated inventory paths, validator stdout/stderr, and explicit `evidence_missing` markers when source roots are unavailable or unreadable.

References: use `references/handoff_quality_validator.md` for classification rules, `references/artifact_quality_validator.md` for output-quality scoring, and `references/artifact_quality_schema.json` for machine-readable validator output.

Concrete local evidence examples include `skills/handoff-evidence-collector/scripts/handoff_inventory.py`, `skills/agent-continuity/scripts/validate_handoff.py`, `handoff_inventory.json`, and `Handoff_Inventory.md`.

## Completion Criteria

- Every collected file has a kind.
- Every true agent-continuity handoff has validator output.
- Every readable file reports byte size and whether it exceeds the warning threshold.
- `<name>-history.md` files outside template/reference locations are classified as
  `handoff_history` and are not validated as active handoffs.
- Templates are not counted as live project handoffs.
- Cursor handoffs are preserved as evidence but not forced into the agent-continuity schema.

## Failure Recovery

- If scan is too slow, stop and switch to max-depth bounded scanning.
- If a handoff fails validation, generate a patch candidate, not an automatic edit.
- If a project root is huge or unreadable, mark it as `scan_limited` or `permission_denied`.
