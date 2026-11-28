---
name: dsh-upgrade-history-safety
description: Safely upgrade, rebuild, switch, or repair a local DeepSeek Harness (DSH) installation that has persisted sessions. Use before any DSH runtime or plugin update, launcher change, restart following a format change, or history-load failure, especially errors mentioning SessionFormatUnsupportedError, v0/v1/v2/v3 migration, an unknown event, a subagent descriptor, or web/openai-codex-search-llm-request.
---

# DSH upgrade and history-safety gate

## Non-negotiable boundary

- Treat `$DSH_HOME/sessions` as immutable evidence. Never rename, delete, decompress-in-place, or overwrite `session*.jsonl[.zstd]` source generations.
- Never point the scheduled launcher or desktop shortcut at a candidate runtime until the candidate passes the full history preflight.
- A successful `http://127.0.0.1:3080` response is not enough: it proves the server started, not that historical sessions can open.
- Keep the last working runtime and a verified persistent local backup of the entire DSH home until post-upgrade history validation succeeds. Select an approved destination actually present on the receiver; MCC disk letters are not requirements.

## Required upgrade sequence

1. State the candidate version, current active version, persistent `DSH_HOME`, and the planned rollback runtime. Do not use `master` when a release/tag is the stated target.
2. Back up the whole DSH home, especially `sessions`, to a timestamped approved persistent location with sufficient space, independently recoverable from the runtime. Record that the copy completed before any upgrade mutation.
3. Build/install the candidate runtime in a parallel directory. Do not switch the launcher, scheduled task, or shortcut yet.
4. Run the complete candidate preflight using [scripts/Invoke-DSH-History-Preflight.ps1](scripts/Invoke-DSH-History-Preflight.ps1). It uses the candidate's format catalog to dry-run every highest historical session generation and runs the independent `dsh-codex` repair preflight.
5. If **any** preflight failure remains, stop the upgrade cutover. Do not mark the runtime update as complete. Diagnose the exact event/schema and add a narrow, tested migration that creates only a new current generation.
6. Only after a 0-failure dry-run, stop every DSH writer (scheduled supervisor, worker, and Web process) and verify that the actual approved listener port is no longer listening; pass that port to the helper with `-ListeningPort`. Then run the same helper with `-Apply`.
7. Rerun the helper without `-Apply`; it must report 0 failures and 0 remaining repairs. If a separately reviewed migration was required, confirm the generated current-format sibling files coexist with unchanged older source files. The bundled reader itself performs no migration.
8. Switch the launcher, restart DSH, verify the authenticated Web server, and open a representative recent session plus every session previously reported as broken. If an old-session route fails, roll back the launcher rather than deleting session files.

## Read-only compatibility preflight

`$DSH_HOME/maintenance/Repair-DSH-History.mjs` is the durable local history reader on MCC. A distribution snapshot is included at [scripts/Repair-DSH-History.mjs](scripts/Repair-DSH-History.mjs). The reader imports the **candidate** runtime's actual JSONL persistence implementation and opens/fully reads every current session generation, including frame, header, migration, vocabulary, and event validation. It requires the source-build layout `vendor/cordis/lib` and `packages/session/session-persistence-jsonl/lib`; do not claim it supports a packaged runtime with a different layout without adapting and testing it.

It is read-only: `--apply` is an explicit no-op compatibility mode and never alters a source generation. The previously needed legacy repairs have already published validated v3 siblings; keep those older generations as evidence. If a future candidate reports an unsupported shape, stop the cutover and add only an exact, lossless, independently tested sibling-generation migration. Never weaken the reader or mark an unknown event ignorable merely to make preflight pass.

The independent `dsh-codex repair-session --json` preview is invoked directly from `$DSH_HOME\profiles\web\node_modules\dsh-codex\lib\bin.js`; do not route this gate through `dsh plugin exec` on Windows because that wrapper can leave a detached package-manager child after a cold build.

## Reboot and liveness safety on this host

- The following D:/S: and 3080 conventions are MCC-specific. Apply them only where those disks, launchers and port actually exist; other Windows hosts and macOS must retain their own approved installation and startup mechanisms.
- `D:\apps` is a disposable runtime cache. Keep launchers, profiles, credentials, history validators, and bootstrap diagnostics under persistent user paths. If the D: runtime is absent or stale, wait for the required S: source files before starting the supervisor; do not let a transient post-logon mount delay consume its retry circuit.
- A DSH Web route is authenticated by a launch token. Never use an unauthenticated HTTP response (`/`, `favicon.svg`, or a plugin route) as the supervisor's liveness check: `401`, timeout, or redirect does not mean the Web process is unhealthy. The supervisor should use the bound local port for liveness; the desktop opener must obtain and open the token URL recorded in the active run's stdout.
- A full cold rebuild on this host may take up to 900 seconds after the source is ready. The supervisor waits up to 900 seconds for S:; the desktop opener must allow the combined 1800-second end-to-end cold start. Keep the scheduled task and desktop shortcut on the independent launcher chain. Do not launch a foreground Web process owned by the current agent as a replacement.

## Invocation

On Windows, resolve the installed skill directory and approved candidate runtime from the target machine, then use the helper after the candidate has been built. Its bundled reader can be supplied explicitly; no MCC user directory is required:

```powershell
& (Join-Path $skillRoot 'scripts/Invoke-DSH-History-Preflight.ps1') `
  -RuntimeRoot $candidateRuntime -DshHome $persistentDshHome `
  -MaintenanceScript (Join-Path $skillRoot 'scripts/Repair-DSH-History.mjs')
```

After the dry-run passes and all DSH writers are stopped:

```powershell
& (Join-Path $skillRoot 'scripts/Invoke-DSH-History-Preflight.ps1') `
  -RuntimeRoot $candidateRuntime -DshHome $persistentDshHome `
  -MaintenanceScript (Join-Path $skillRoot 'scripts/Repair-DSH-History.mjs') -Apply
```

The helper returns non-zero on any failure, remaining repair, invalid candidate runtime, running service on the configured listener port during `-Apply`, or disagreement between independent preflights. Treat this as a hard release gate.

On macOS/Linux, the bundled Node reader is available but the PowerShell process/port check is Windows-specific. With target-local `DSH_RUNTIME_ROOT` and `DSH_HOME` set, run `node <skill-dir>/scripts/Repair-DSH-History.mjs <DSH_HOME>/sessions --json`, then the installed `dsh-codex/lib/bin.js repair-session --json` directly. Inspect both exit codes and all failures/pending results. Determine and stop every writer using the target host's own process/service controls before any actual migration. macOS execution has not been validated by MCC; source-layout compatibility and real history opens must be independently verified there.

## Reporting requirement

Before saying an upgrade or repair is complete, report: candidate version/commit, backup location, dry-run summary, applied-session count, post-apply zero-failure summary, raw-source preservation evidence, service health, and actual session-open verification. Update the active continuity handoff with these facts.
