#!/usr/bin/env node
/**
 * Read-only DSH history compatibility preflight.
 *
 * It intentionally never alters session artifacts. Every listed session is
 * opened and fully read through the active runtime's JSONL persistence layer,
 * which performs the same physical-frame, header, migration, vocabulary, and
 * contiguous-event validation as normal DSH history loading.
 */
import { existsSync, statSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

function usage(message) {
  throw new Error(`${message}\nUsage: Repair-DSH-History.mjs <sessions-root> --json [--apply]`)
}

const [sessionsRootArg, ...flags] = process.argv.slice(2)
if (!sessionsRootArg) usage('Missing sessions root.')
if (!flags.includes('--json')) usage('Machine-readable --json output is required.')
if (flags.some(flag => flag !== '--json' && flag !== '--apply')) {
  usage(`Unknown flag: ${flags.find(flag => flag !== '--json' && flag !== '--apply')}`)
}

const runtimeRoot = process.env.DSH_RUNTIME_ROOT
if (!runtimeRoot) usage('DSH_RUNTIME_ROOT must identify the candidate runtime.')
const resolvedRuntime = resolve(runtimeRoot)
const sessionsRoot = resolve(sessionsRootArg)
if (!existsSync(sessionsRoot) || !statSync(sessionsRoot).isDirectory()) {
  usage(`Sessions root is unavailable: ${sessionsRoot}`)
}

const moduleUrl = relative => pathToFileURL(resolve(resolvedRuntime, relative)).href
const [{ Context }, { default: JsonlSessionPersistence }] = await Promise.all([
  import(moduleUrl('vendor/cordis/lib/index.js')),
  import(moduleUrl('packages/session/session-persistence-jsonl/lib/index.js')),
])

const context = new Context()
const persistence = new JsonlSessionPersistence(context, {
  root: sessionsRoot,
  compression: 'zstd',
})

const failures = []
let eventCount = 0
let snapshots = []
try {
  snapshots = await persistence.list()
} catch (error) {
  failures.push({ stage: 'list', error: error instanceof Error ? error.message : String(error) })
}

for (const snapshot of snapshots) {
  let handle
  try {
    handle = await persistence.open(snapshot.header.id, 'read')
    const read = await handle.read()
    eventCount += read.events.length
  } catch (error) {
    failures.push({
      stage: 'open-read',
      sessionId: snapshot.header.id,
      error: error instanceof Error ? error.message : String(error),
    })
  } finally {
    if (handle) await handle.close()
  }
}

const summary = {
  schemaVersion: 1,
  mode: flags.includes('--apply') ? 'apply-noop' : 'dry-run',
  runtimeRoot: resolvedRuntime,
  sessionsRoot,
  scannedSessions: snapshots.length,
  currentSessions: failures.length === 0 ? snapshots.length : snapshots.length - failures.filter(item => item.sessionId).length,
  unaffectedSessions: failures.length === 0 ? snapshots.length : snapshots.length - failures.filter(item => item.sessionId).length,
  validatedEvents: eventCount,
  repairedEvents: 0,
  results: [],
  failures,
}
process.stdout.write(`${JSON.stringify(summary)}\n`)
process.exitCode = failures.length === 0 ? 0 : 1
