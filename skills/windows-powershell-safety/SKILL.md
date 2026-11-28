---
name: windows-powershell-safety
description: Use when running commands in Windows PowerShell or generating DSH run_code programs, especially shell searches with `rg`, `git grep`, `Select-String`, `findstr`, Git revision path syntax, fixed-string patterns, quoted code snippets, native CLI arguments, npm/node/playwright commands, variable interpolation, commands copied from Bash, or calls to tools.grep and MCP browser tools. Prevents quoting, escaping, wildcard, pipeline, stderr, secret-log, and argument-boundary mistakes, JavaScript/JSON/regex/Windows-path escaping mistakes, missing current tool arguments such as pageId, and unsafe whole-program retries after partial effects.
---

# Windows PowerShell Safety

## DSH run_code: Mandatory Preflight

Apply this BEFORE every nontrivial DSH run_code program, even when no PowerShell is involved.
- Treat transport JSON, TypeScript/JavaScript source, tool argument JSON, regex, and PowerShell/native argv as DIFFERENT layers. Single quotes in JavaScript do not make a raw string.
- Use declared SDK grep/glob/read/edit tools instead of shell text-search/file-reading commands when they are available. Shell examples below do not override the active tool policy.
- Prefer a regex with no backslash when matching literal punctuation: opening parenthesis [(], closing parenthesis [)], dot [.].
- For actual backslashes, prefer String.raw tagged templates. The outer JSON still needs normal JSON escaping; serialize structured arguments rather than manually guessing extra escape levels.
- For Windows paths in JavaScript, prefer forward-slash paths or String.raw. Never paste unescaped backslashes into an ordinary JS literal: numeric path components can cause strict-mode octal SyntaxError; \t/\n/\v can silently alter paths.
- String.raw disables escape processing, NOT template interpolation. PowerShell ${name} can still be interpolated by JavaScript; keep such command text in an ordinary quoted string or explicitly protect the dollar sign.
- A backtick also ends a JavaScript template literal, including inside String.raw. When PowerShell text is embedded in a template, avoid the PowerShell backtick escape (for example `? or `: after a variable); build the string by concatenation instead: '$K/files/'+$e+'?ref='+$sha.
- Some SDK tools are deferred and can reject inside a program with "is deferred and not yet loaded" even after earlier use (seen with subagent and send_message). Load them in a separate step with tool_search or defer_execute_tool, then retry only the rejected call; earlier calls in that program may already have completed, so never replay the whole program.
- Keep programs short and group only independent read-only operations. Run an unfamiliar required-argument tool probe separately BEFORE combining it with writes. Never replay a whole partially executed program blindly.

Verified source-level examples (these are JavaScript/TypeScript, not outer transport JSON):

```typescript
const pattern = 'service_now_request[(]';
await tools.grep({ pattern, path: 'repo/app', include: '*.py' });
// For an escaped regex instead:
const escaped = String.raw`service_now_request\(`;
// Inspect only non-secret arguments: JSON.stringify({ pattern: escaped })
const forward = 'C:/example/0548315/app';
const native = String.raw`C:\example\0548315\app`;
```

Do NOT copy this broken ordinary literal:

```typescript
const broken = 'service_now_request\('; // JS loses the backslash; regex has an unclosed group.
```

## MCP Current-Contract Check

- Use the current tool input schema, not a remembered SDK version. If a binding is typed unknown, the description alone is NOT proof of its required fields.
- On MCC, the captured navigate_page and take_snapshot schemas required pageId. This is dated source evidence, not the receiver tool contract: check the current schema on the target host. If it requires pageId, obtain the actual ID from list_pages and keep it explicit; never hardcode a future page ID or import MCC arguments into another browser API.
- First navigate/snapshot separately as read-only probes; only then perform UI mutations using the newest snapshot. Do not guess schemas for other browser tools.
- Required at pageId / MCP -32602 is argument validation, not a website, permission, or service-outage error. Correct only the missing argument and retry that read-only call.
- An unauthenticated DSH root page is not a dead server. Use only an already authorized token URL when browser access is necessary; never restart a listening service or expose/search for credentials to solve an unrelated skill edit. Local user-skill text updates do not require browser login.

## Browser UI Editing And Automation Gates

- Rich designers (flow editors, Monaco-style inputs) may not commit synthetic text: `Input.insertText` after a JS selection can update only the visible DOM while the underlying definition keeps the old value, and a later save silently persists that old value. Use real input events instead: triple-click to select the field content, Backspace, per-character `Input.dispatchKeyEvent` with `text`, then Tab to commit. After saving, reload the page and read the server state (code view, definition, or API) to verify; the editor display alone is not proof.
- An automation gate built from hardcoded constant comparisons (for example `"LOCKED" equals "LOCKED"`) never evaluates true, and a run page that draws both branches can mislead: the branch label does not tell you whether an action ran. Check the action's own result icon on the run page (skipped is a grey dash, not a green check) and read the gate expression in code view before claiming that a guarded action did or did not execute.
- Treat a temporarily enabled send gate as an exposed write window: prepare the edit, run exactly once, then relock and verify by reloading, before reporting anything else. If a step in the window fails, restoring the gate takes priority over retries or reports.

## Failure Classification And Partial Effects

1. Syntax/compile error before run_code execution: no program operations ran. Fix source syntax/literals before retrying.
2. ToolCallError after earlier awaited calls: earlier goal/todo/file/network operations MAY already have completed. Inspect those effects; retry only the failed dependent operation.
3. Regex parse error: inspect the final non-secret pattern value, replace a literal delimiter with [(] when appropriate, and retry the scoped grep. Never switch to a forbidden shell search to hide the error.
4. Current MCP validation failure: consult the active schema/error, update required fields, probe read-only, then continue.
5. Distinguish expected failure assertions in a regression self-test from real operational errors. Do not deliberately submit known-broken tools to reproduce failures in the user session.

## Verification

From this skill directory, run node --check scripts/check_dsh_literals.mjs, then node scripts/check_dsh_literals.mjs. Both must exit0. The self-test uses synthetic fixed strings and compiles snippets without side effects; it does not invoke MCP or prove every provider schema.
After editing, reload this skill through the official skill tool and verify the new trigger/sections are present. For new schema versions, refresh the contract examples from real read-only evidence rather than asserting that documentation prevents all errors.

## Default Checks

Before running a non-trivial PowerShell command, check these points:

- Use single quotes for literal search patterns.
- Do not backslash-escape double quotes inside single-quoted strings.
- Use `${var}` when interpolating a variable before `:` or another name character.
- Prefer separate CLI arguments over one composed command string.
- Do not use Bash here-doc syntax in PowerShell.
- For file operations, use native PowerShell cmdlets with `-LiteralPath`.
- Treat `-like` and `-notlike` as wildcard operators, not literal string operators.
- Wrap generated output in `& { ... }` before piping a `foreach` loop.
- For native CLIs that may write benign stderr (`npm`, `node`, `playwright`, `python`, `gh`), capture output explicitly and check `$LASTEXITCODE`.
- For secret-bearing commands, write raw output to a temp log, redact before display, then remove the temp log.

## Literal Search Patterns

Distinguish PowerShell cmdlets from native executables.
PowerShell stores double quotes inside single-quoted strings literally, but native executables receive arguments through Windows argv parsing.
For native executables such as `git.exe`, `rg.exe`, and `python.exe`, embedded double quotes may be stripped unless escaped for native argv.

For PowerShell cmdlets such as `Select-String`, do not escape double quotes:

```powershell
$pattern = 'name="delivery_outside_tel"'
Select-String -Path .\src\file.tsx -Pattern $pattern -SimpleMatch
```

For native CLIs, either escape embedded double quotes or search for a shorter quote-free token:

```powershell
git grep -n -F 'name=\"delivery_outside_tel\"' origin/main -- src
git grep -n -F 'restrictInput(e.target.value' origin/pr/1701 -- src
rg -n -F 'setValue(\"address2\"' src
```

To inspect what a native executable receives, print argv:

```powershell
python -c "import sys; print(repr(sys.argv[1]))" 'setValue(\"address2\"'
```

Expected output:

```text
'setValue("address2"'
```

If this prints `setValue(address2`, the quotes were stripped before the target CLI received the argument.

## Variable Interpolation

PowerShell treats `:` after a variable name as part of scoped variable syntax.
Use `${var}` when a variable is followed by `:`.

Good:

```powershell
"--- ${file}:$($line)"
```

Bad:

```powershell
"--- $file:$($line)"
```

The bad form can fail with `Variable reference is not valid`.

## Literal Versus Wildcard Matching

PowerShell wildcard operators interpret `*`, `?`, and `[]`.
Do not use `-like` for literal markers that contain square brackets, such as GitHub issue tags.

Good:

```powershell
$comment.body.StartsWith('[controller-key-rotation-published][mcc]')
$comment.body.Contains('[mcc-e2e-complete]')
$comment.body -match ('^' + [regex]::Escape('[review-complete]'))
```

Bad:

```powershell
$comment.body -like '[controller-key-rotation-published][mcc]*'
```

The bad form treats bracketed text as wildcard character classes and can throw `WildcardPatternException`.

## Piping Loop Output

PowerShell does not pipe directly from a `foreach` statement.
Wrap the loop in a script block when generated objects should flow into another command.

Good:

```powershell
& {
  foreach ($path in $paths) {
    [pscustomobject]@{
      Path = $path
      Exists = (Test-Path -LiteralPath $path)
    }
  }
} | Format-Table -AutoSize
```

Bad:

```powershell
foreach ($path in $paths) {
  [pscustomobject]@{ Path = $path }
} | Format-Table -AutoSize
```

The bad form can fail with `An empty pipe element is not allowed`.

## Git Revision Paths

Use a backtick before `:` when constructing `rev:path` inside an interpolated string.
If this PowerShell text is embedded in a DSH run_code template literal, the backtick terminates the template; use concatenation such as `git show ($rev + ':' + $path)` instead.

Good:

```powershell
git show "origin/main`:src/components/atomic/ActiveTextField.tsx"
git show "${rev}`:${path}"
```

For a literal rev path, no backtick is needed:

```powershell
git show origin/main:src/components/atomic/ActiveTextField.tsx
```

## Paths, CLI Contracts, And Owned Temporary Handles

- Discover unfamiliar existing paths with the filesystem glob tool before reading; do not assume mirrored repositories use the same test directory. A failed read makes no file change, but earlier calls in the program may already have completed.
- A read result may contain fewer lines than requested because of payload limits. Before any whole-file reconstruction, verify continuous line numbers through `totalLines`; continue with `offset = lastReturnedLine + 1` until complete. Never overwrite a long file from only the returned prefix. Prefer targeted edits; if an owned-only truncation occurs, stop, verify its exact path/lease, recover only that file from the known clean baseline and prove the tail/functions are intact before continuing.
- In generated JavaScript program source, avoid hand-quoted single-quote strings containing prose apostrophes such as `don't`; bind text with a correctly serialized JSON string or safe double-quoted literal. Compile/pure-preflight generated source before any tool side effects. Parser rejection means no tools in that program ran; do not infer partial mutations from that rejection.
- When filtering by time in PowerShell, convert both sides with `.ToUniversalTime()` before comparing. `[datetime]` parsing of API ISO timestamps and of a literal such as `'2026-11-26T01:16:23Z'` can yield local or UTC kinds, which silently shifts the cutoff by the UTC offset (9 hours in JST) and drops events. Alternatively keep ISO strings with `ConvertFrom-Json -DateKind String` and compare normalized UTC strings.
- Check the exact native subcommand help before using an unverified flag in a mutation. GitHub CLI REST `gh api` uses a fully qualified endpoint and does not accept the `gh pr` subcommand's `--repo` flag.
- Never use `git remote -v`, remote URL getters, or raw Git config output as routine repo orientation: URLs can contain embedded credentials. Supplied owner/repo, root, branch, status and commit ids suffice. If exposed, stop repeating it, report the fact without the value, and request human account handling rather than rotating credentials silently.
- In Windows-only offline tests that redirect file logging into an owned temporary directory, close every owned handler before cleanup. Put `logging.shutdown()` or explicit handler closes in `finally` before `TemporaryDirectory` exits. Tests passing followed by a cleanup error is NOT a successful command; fix the harness and rerun without changing production code.

## Native CLI Arguments

Prefer direct argument lists.
Do not compose one large command string unless there is no alternative.

Good:

```powershell
git grep -n -F 'restrictInput(e.target.value' origin/pr/1701 -- src/components
rg -n -F 'field.onChange(filteredValue)' src/components
```

Avoid:

```powershell
$cmd = "git grep -n -F 'restrictInput(e.target.value' origin/pr/1701 -- src/components"
Invoke-Expression $cmd
```

## Native CLI Stderr And Exit Codes

Windows PowerShell can surface native stderr as `NativeCommandError`, especially under `$ErrorActionPreference = 'Stop'`.
Do not let warning text from `node`, `npm`, `playwright`, `python`, or similar tools decide whether a command succeeded.
Capture stdout and stderr to a log, then check `$LASTEXITCODE`.

For commands where raw output may include secrets, do not stream output to the chat.
Write to a temp log, redact, summarize, and remove the log.

Preferred pattern:

```powershell
$logPath = Join-Path $env:TEMP ('tool-' + [guid]::NewGuid().ToString('N') + '.log')
$command = 'npm run test > "' + $logPath + '" 2>&1'
& cmd.exe /d /s /c $command
$exitCode = $LASTEXITCODE

$raw = Get-Content -LiteralPath $logPath -Raw
$redacted = $raw `
  -replace 'Bearer\s+[^\s''"\}\],)]+', 'Bearer [REDACTED]' `
  -replace '(ATH_(E2E_)?MACHINE_KEY\s*=\s*)[^\s]+', '$1[REDACTED]'

Remove-Item -LiteralPath $logPath -Force -ErrorAction SilentlyContinue
if ($exitCode -ne 0) {
  throw "Command failed with exit code ${exitCode}`n${redacted}"
}
```

Use this pattern for Playwright or staging tests that may include auth headers, API keys, cookies, traces, screenshots, or replayable requests.

## Bash Syntax To Avoid

PowerShell does not support Bash here-docs:

```powershell
python - <<'PY'
```

Use `python -c`, a temporary file, or a script already in the repository.

## Recovery Rule

If a search returns no matches but the pattern is expected to exist:

1. Identify whether the search tool is a PowerShell cmdlet or native executable.
2. Print the exact native argv with `python -c "import sys; print(repr(sys.argv[1]))" <pattern>`.
3. Try a shorter quote-free fixed string first.
4. Use `git show rev:path` or `Get-Content -Encoding UTF8` to inspect the target lines.
