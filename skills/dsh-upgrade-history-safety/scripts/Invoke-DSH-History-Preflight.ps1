[CmdletBinding()]
param(
  [Parameter(Mandatory)]
  [ValidateNotNullOrEmpty()]
  [string]$RuntimeRoot,
  [ValidateNotNullOrEmpty()]
  [string]$DshHome = (Join-Path $env:USERPROFILE '.dsh'),
  [string]$MaintenanceScript = (Join-Path $DshHome 'maintenance\Repair-DSH-History.mjs'),
  [ValidateRange(1, 65535)]
  [int]$ListeningPort = 3080,
  [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$cli = Join-Path $RuntimeRoot 'apps\cli\lib\bin.js'
$sessions = Join-Path $DshHome 'sessions'
$codexCli = Join-Path $DshHome 'profiles\web\node_modules\dsh-codex\lib\bin.js'
foreach ($path in @($RuntimeRoot, $cli, $DshHome, $sessions, $MaintenanceScript, $codexCli)) {
  if (-not (Test-Path -LiteralPath $path)) { throw "Required DSH preflight path is unavailable: $path" }
}

if ($Apply) {
  $listener = Get-NetTCPConnection -LocalPort $ListeningPort -State Listen -ErrorAction SilentlyContinue
  if ($null -ne $listener) {
    throw "Refusing to publish session migrations while port $ListeningPort is listening. Stop every owned DSH writer first."
  }
}

$env:DSH_RUNTIME_ROOT = $RuntimeRoot
$env:DSH_HOME = $DshHome

function Invoke-JsonCommand([scriptblock]$Command, [string]$Name) {
  $runOutput = & $Command 2>&1
  $exitCode = $LASTEXITCODE
  $line = $runOutput | Where-Object { $_ -match '^\{"schemaVersion":' } | Select-Object -Last 1
  if ($null -eq $line) {
    $tail = ($runOutput | Select-Object -Last 40) -join [Environment]::NewLine
    throw "$Name did not emit its machine-readable summary (exit $exitCode):$([Environment]::NewLine)$tail"
  }
  $summary = $line | ConvertFrom-Json
  if ($exitCode -ne 0 -or @($summary.failures).Count -ne 0) {
    throw "$Name failed: exit $exitCode; failures $(@($summary.failures).Count)"
  }
  return $summary
}

$historyArgs = @($MaintenanceScript, $sessions, '--json')
if ($Apply) { $historyArgs += '--apply' }
$history = Invoke-JsonCommand { & node.exe @historyArgs } 'DSH history compatibility preflight'

if ($Apply -and @($history.results).Count -gt 0) {
  $postArgs = @($MaintenanceScript, $sessions, '--json')
  $post = Invoke-JsonCommand { & node.exe @postArgs } 'DSH history post-apply preflight'
  if (@($post.results).Count -ne 0) { throw 'DSH history post-apply preflight still has pending repairs.' }
}

# Invoke the package executable directly.  The generic `dsh plugin exec`
# launcher can detach its package-manager child on Windows, leaving a stale
# preflight process after a cold rebuild.  This CLI is self-contained and has
# the same read-only repair-session preview semantics.
$codex = Invoke-JsonCommand { & node.exe $codexCli repair-session --json } 'dsh-codex independent preflight'
if (@($codex.results).Count -ne 0) { throw 'dsh-codex independent preflight still has pending repairs.' }

[PSCustomObject]@{
  runtimeRoot = $RuntimeRoot
  dshHome = $DshHome
  applied = [bool]$Apply
  history = [PSCustomObject]@{
    scannedSessions = $history.scannedSessions
    currentSessions = $history.currentSessions
    unaffectedSessions = $history.unaffectedSessions
    pendingRepairs = @($history.results).Count
    repairedEvents = $history.repairedEvents
  }
  codex = [PSCustomObject]@{
    scannedSessions = $codex.scannedSessions
    currentSessions = $codex.currentSessions
    unaffectedSessions = $codex.unaffectedSessions
    pendingRepairs = @($codex.results).Count
  }
} | ConvertTo-Json -Depth 5 -Compress
