# Checkpoint Mode

Use this when the task is still healthy but should remain restartable.

## Prompt

```text
Use agent-continuity checkpoint mode.

Update the existing `handoff.md` when a verified result, decision, blocker, or change to the next action affects how another session will resume.

Do not expand scope. Do not perform unrelated work.

Record:
- original goal, binding user constraints, and completion conditions
- confirmed current state with evidence
- recent progress that affects continuation
- exact next minimal step, where to find its evidence, and what result to check
- next 3 steps
- unfinished work by priority
- blockers or risks
- failed attempts that could be repeated, with the action, observed result, original evidence location, and retry condition
- key files/artifacts
- decisions and assumptions
- 15-second quick resume note
```

## Rules

- Checkpoint at a meaningful phase boundary when there is a verified result, decision, blocker,
  or change to the next action that the next session needs.
- Prefer concrete artifact references over prose memory.
- Keep `Next Minimal Step` to one action.
- Preserve prior blockers and do-not-retry notes unless they are explicitly resolved.
- If a claim has no evidence, mark it as `Assumption`. Label unconfirmed causes as hypotheses.
- The `## Status` section must start with `READY TO CONTINUE`, `NEEDS REVIEW`, or `BLOCKED ON <specific blocker>` so `scripts/validate_handoff.py` can verify it.
- For self-distillation or generated artifact packages, put `handoff.md` in the output directory if that is the safest continuation root.
- Measure the existing handoff in bytes before adding checkpoint material. If it already exceeds
  150,000 bytes or the planned update would exceed that size, report the file and measured size.
  While proposing a split for approval, make small edits to the sections needed to resume safely.
  Keep `Status`, `Blockers`, and `Next Minimal Step` current. Sync `Quick Resume` with the new next
  action and record any new do-not-retry guidance in `Do Not Retry Without New Evidence`.
- For an approved split, preserve the existing file verbatim in the first unused sibling history
  path. Start with `<name>-history.md`, then use `<name>-<UTC timestamp>-history.md` or add a numeric
  suffix on collision. Verify the copy byte-for-byte or by cryptographic hash before replacing the
  main file. Retain the named sections, unresolved blockers, do-not-retry notes, and the next
  executable action in the concise `handoff.md`. Link the preserved file in `Files And Artifacts`.
- Validate the resulting `handoff.md` and report its byte size and the verified history path.
- Start a new session with the current `handoff.md` and recheck the live state that governs the
  next action. If key evidence is missing, read only the relevant excerpts from prior chats,
  files, diffs, or logs, including the preserved history when it holds that evidence.

## Bad Checkpoint

```text
We made progress and should continue fixing things.
```

## Good Checkpoint

```text
`src/importer.ts` now parses quoted CSV fields; `npm test -- importer` passes.
Next minimal step: update `docs/import.md` with the new quote-handling behavior.
Do not retry `npm test` for the full suite until `packages/ui` dependencies are available.
The last full run stopped with `MODULE_NOT_FOUND` before running tests. See `tmp/full-suite.log`.
Hypothesis: the `packages/ui` dependency install was incomplete.
```

## Self-Distillation Checkpoint

Use an output-directory handoff when the task generates reports or skill candidates but does not edit a source project.

```text
Output root: `outputs/self_distillation_20260705`.
Confirmed: `Handoff_Inventory.md` and `work/handoff_inventory.json` were generated from two user-supplied roots.
Confirmed: `artifact-quality-gate` scored `00_receipt.md` as `90 / ready`.
Next minimal step: review `16_installation_plan_and_rollback.md` before installing any candidate.
Do not edit source projects until the user explicitly approves the candidate patch.
```
