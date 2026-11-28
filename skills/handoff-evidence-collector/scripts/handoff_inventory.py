#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROOTS = [Path.cwd()]
DEFAULT_VALIDATOR = REPO_ROOT / "skills" / "agent-continuity" / "scripts" / "validate_handoff.py"
BUNDLED_FIXTURES = Path(__file__).resolve().parents[1] / "examples" / "smoke-root"
BUNDLED_FIXTURE_LAYOUT = "handoff-evidence-collector/examples/smoke-root"
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "models",
    "checkpoints",
    "cache",
    ".cache",
    "outputs",
    "data",
}
MAX_DEPTH = 6
SIZE_WARN_BYTES = 150_000


def classify(path: Path, text: str) -> str:
    if "references" in path.parts or "template" in path.name.lower():
        return "template_or_reference"
    if path.name.lower().endswith("-history.md"):
        return "handoff_history"
    if "## Status" in text and "## Quick Resume" in text and "## Next Minimal Step" in text:
        return "agent_continuity_handoff"
    if "cursor" in path.name.lower() or "/cursor-" in str(path).lower():
        return "cursor_handoff"
    if "handoff guide" in text.lower() or "install" in text.lower()[:1200]:
        return "usage_handoff_or_guide"
    return "handoff_like"


def markdown_cell(value: object) -> str:
    return (
        str(value)
        .replace("|", r"\|")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "<br>")
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="handoff-evidence-smoke-output")
    parser.add_argument("--root", action="append", default=[])
    parser.add_argument("--validator-path")
    parser.add_argument(
        "--execution-mode",
        default="real_execution",
        choices=["real_execution", "fixture", "mock", "dry_run", "semi_real", "candidate_only"],
        help="Label the inventory evidence mode explicitly.",
    )
    args = parser.parse_args()

    out = Path(args.output_root).resolve()
    (out / "work").mkdir(parents=True, exist_ok=True)
    env_roots = [p for p in os.environ.get("HANDOFF_EVIDENCE_ROOTS", "").split(os.pathsep) if p]
    roots_arg = args.root or env_roots
    roots = [Path(p).expanduser().resolve() for p in roots_arg] if roots_arg else DEFAULT_ROOTS
    validator = Path(args.validator_path).expanduser().resolve() if args.validator_path else DEFAULT_VALIDATOR
    validator_missing = not validator.exists()

    paths = []
    scan_gaps = set()
    scanned_dirs = set()

    def record_walk_error(error: OSError) -> None:
        scan_gaps.add((str(error.filename), "unreadable_directory"))

    for root in roots:
        if not root.is_dir():
            scan_gaps.add((str(root), "unavailable_root"))
            continue
        for current, dirnames, filenames in os.walk(root, topdown=True, onerror=record_walk_error):
            cur = Path(current)
            scanned_dirs.add(cur)
            depth = len(cur.relative_to(root).parts)
            retained_dirs = []
            for name in dirnames:
                directory = cur / name
                if name in SKIP_DIRS:
                    scan_gaps.add((str(directory), "excluded_directory"))
                elif depth >= MAX_DEPTH:
                    scan_gaps.add((str(directory), "depth_limit"))
                elif directory.is_symlink():
                    scan_gaps.add((str(directory), "symlink_directory"))
                else:
                    retained_dirs.append(name)
            dirnames[:] = retained_dirs
            for fname in filenames:
                low = fname.lower()
                if low == "handoff.md" or ("handoff" in low and low.endswith(".md")):
                    paths.append(cur / fname)
    paths = sorted(set(p for p in paths if ".git" not in p.parts), key=lambda p: str(p).lower())

    records = []
    for path in paths:
        is_fixture = any(
            parent == BUNDLED_FIXTURES or parent.match(BUNDLED_FIXTURE_LAYOUT)
            for parent in path.parents
        )
        evidence_mode = "fixture" if is_fixture else args.execution_mode
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            st = path.stat()
        except Exception as exc:
            scan_gaps.add((str(path), "unreadable_file"))
            records.append({"path": str(path), "read_error": repr(exc), "evidence_mode": evidence_mode})
            continue
        kind = classify(path, text)
        validation = {"attempted": False}
        if kind == "agent_continuity_handoff" and validator_missing:
            validation = {
                "attempted": False,
                "reason": "validator_missing",
                "validator": str(validator),
            }
        elif kind == "agent_continuity_handoff":
            child_env = dict(os.environ)
            child_env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.run(
                # Reuse this process's interpreter instead of resolving a platform-specific python3.
                [sys.executable or "python3", str(validator), str(path)],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=child_env,
                timeout=10,
            )
            validation = {
                "attempted": True,
                "returncode": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
            }
        records.append({
            "path": str(path),
            "kind": kind,
            "evidence_mode": evidence_mode,
            "size": st.st_size,
            "size_bytes": st.st_size,
            "oversized": st.st_size > SIZE_WARN_BYTES,
            "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
            "has_status": "## Status" in text,
            "has_quick_resume": "## Quick Resume" in text,
            "has_next_minimal_step": "## Next Minimal Step" in text,
            "validation": validation,
        })

    counts = {}
    evidence_counts = {}
    for rec in records:
        counts[rec.get("kind", "unreadable")] = counts.get(rec.get("kind", "unreadable"), 0) + 1
        if "read_error" not in rec:
            mode = rec["evidence_mode"]
            evidence_counts[mode] = evidence_counts.get(mode, 0) + 1
    gaps = [
        {"path": path, "reason": reason}
        for path, reason in sorted(scan_gaps)
        if Path(path) not in scanned_dirs
    ]
    data = {
        "roots": [str(r) for r in roots],
        "validator": str(validator),
        "validator_exists": not validator_missing,
        "execution_mode": args.execution_mode,
        "size_warning_threshold_bytes": SIZE_WARN_BYTES,
        "counts": counts,
        "evidence_counts": evidence_counts,
        "scan_gaps": gaps,
        "records": records,
    }
    (out / "work" / "handoff_inventory.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", errors="surrogateescape")

    lines = [
        "# Handoff Inventory",
        "",
        "TASK: Collect and classify local Codex/Cursor/project handoff files.",
        "",
        "Goal: make local handoff files usable as evidence for Codex self-distillation and project continuation.",
        "",
        "Objective: collect handoffs without editing source projects, classify each file, and validate only true agent-continuity handoffs.",
        "",
        f"STATUS: {args.execution_mode}",
        "",
        "Outcome: generated a Markdown inventory plus JSON evidence index for the requested roots.",
        "",
        f"Execution mode: `{args.execution_mode}`. This script only reads source roots and writes this inventory to the requested output directory; it does not edit project files. Use `fixture`, `mock`, `dry_run`, `semi_real`, or `candidate_only` instead of `real_execution` whenever the input roots or evidence are not live project evidence.",
        "",
        "Evidence: each record below includes a concrete file path, byte size, oversized status, mtime, classification, and validator result when applicable. `evidence_missing` is used only when a root is unavailable or a file cannot be read.",
        "",
        "## Input / Workflow / Output",
        "",
        "Input roots:",
        "",
    ]
    for root in roots:
        lines.append(f"- `{root}`")
    lines += [
        "",
        "Workflow:",
        "",
        "1. Bounded walk under input roots.",
        "2. Skip dependency, cache, model, checkpoint, data, and output directories.",
        "3. Classify matching handoff Markdown files, including evidence-only history files.",
        "4. Validate true `agent_continuity_handoff` files with the configured validator.",
        "5. Write Markdown and JSON inventory artifacts.",
        "",
        "Output artifacts:",
        "",
        f"- `{out / 'Handoff_Inventory.md'}`",
        f"- `{out / 'work' / 'handoff_inventory.json'}`",
        "",
        "Acceptance:",
        "",
        "- The script exits 0.",
        "- Every collected file has a `kind` classification.",
        "- Cursor handoffs are indexed but not forced through the agent-continuity validator.",
        "- History handoffs are indexed as evidence but not validated as active handoffs.",
        "- Every readable record includes byte size and oversized status.",
        "- Project files are not modified.",
        "",
        "Repair / rollback:",
        "",
        "- If this inventory is wrong, rerun with narrower `--root` values or inspect `handoff_inventory.json`.",
        "- Rollback is not needed for project files because this is read-only against source roots.",
        "- If a live agent-continuity handoff fails validation, generate a patch candidate before editing the handoff.",
        "",
        "Human entrypoint:",
        "",
        f"- `{out / 'Handoff_Inventory.md'}`",
        "",
        "Roots:",
        "",
    ]
    for root in roots:
        lines.append(f"- `{root}`")
    lines += [
        "",
        f"Validator: `{validator}`",
        f"Validator status: `{'missing' if validator_missing else 'available'}`",
        f"Size warning threshold: `{SIZE_WARN_BYTES:,}` bytes (`oversized` is strictly greater).",
        "",
        "## Scan coverage",
        "",
        f"Maximum depth: {MAX_DEPTH}. For a handoff inside an excluded directory such as outputs, "
        "pass the narrow directory containing it as an explicit additional root.",
        "",
    ]
    lines.extend(
        f"- {gap['reason']}: `{markdown_cell(gap['path'])}`"
        for gap in gaps
    )
    if not gaps:
        lines.append("- No exclusions or scan errors encountered.")
    lines += [
        "",
        "## Counts by kind across all evidence modes",
        "",
        "| Kind | Count |",
        "|---|---:|",
    ]
    for key, value in sorted(counts.items()):
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        "## Readable records by evidence mode",
        "",
        "| Evidence mode | Count |",
        "|---|---:|",
    ]
    for mode, count in sorted(evidence_counts.items()):
        lines.append(f"| {mode} | {count} |")
    lines += [
        "",
        "## Records",
        "",
        "| Path | Kind | Size (bytes) | Oversized | mtime | Evidence mode | agent-continuity fields | Validation |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    for rec in records:
        fields = ",".join(
            key for key in ["has_status", "has_next_minimal_step", "has_quick_resume"] if rec.get(key)
        ) or "none"
        val = rec.get("validation", {})
        if val.get("attempted"):
            validation = f"rc={val.get('returncode')} {val.get('stdout') or val.get('stderr')}"
            if val.get("stdout") and val.get("stderr"):
                validation += f" stderr={val.get('stderr')}"
        elif val.get("reason") == "validator_missing":
            validation = "validator_missing"
        else:
            validation = "not_applicable"
        oversized = rec.get("oversized")
        oversized_text = "yes" if oversized is True else "no" if oversized is False else ""
        lines.append(
            f"| `{markdown_cell(rec['path'])}` | {rec.get('kind')} | {rec.get('size_bytes', '')} | "
            f"{oversized_text} | {rec.get('mtime','')} | {rec['evidence_mode']} | {fields} | {markdown_cell(validation)} |"
        )
    (out / "Handoff_Inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8", errors="surrogateescape")
    print(json.dumps({"output_root": str(out), "handoffs": len(records), "counts": counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
