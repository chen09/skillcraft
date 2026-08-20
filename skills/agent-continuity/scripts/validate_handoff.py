#!/usr/bin/env python3
"""Validate that a handoff.md has the required agent-continuity sections."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_HEADINGS = [
    "## Status",
    "## Original Goal",
    "## Current State",
    "## Recent Progress",
    "## Next Minimal Step",
    "## Next 3 Steps",
    "## Unfinished Work",
    "## Blockers",
    "## Do Not Retry Without New Evidence",
    "## Files And Artifacts",
    "## Decisions",
    "## Assumptions",
    "## Quick Resume",
]

VALID_STATUS_PREFIXES = (
    "READY TO CONTINUE",
    "NEEDS REVIEW",
    "BLOCKED ON ",
)
SIZE_WARN_BYTES = 150_000


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="handoff.md")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: missing {path}")
        return 1

    text = path.read_text(encoding="utf-8")
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in text]
    if missing:
        print("ERROR: missing required headings:")
        for heading in missing:
            print(f"- {heading}")
        return 1

    status_section = text.split("## Status", 1)[1].split("\n## ", 1)[0].strip()
    if not status_section.startswith(VALID_STATUS_PREFIXES):
        print("ERROR: status must start with READY TO CONTINUE, NEEDS REVIEW, or BLOCKED ON <reason>")
        return 1

    if len(text.split("## Quick Resume", 1)[1].strip()) < 20:
        print("ERROR: Quick Resume is too short")
        return 1

    size_bytes = path.stat().st_size
    if size_bytes > SIZE_WARN_BYTES:
        history_name = f"{path.stem}-history{path.suffix}"
        print(
            f"WARN: {path} is {size_bytes:,} bytes. Consider splitting it into a current-truth "
            f"layer and an unused verbatim history file (start with {history_name}; use a "
            f"timestamped *-history.md name on collision) before the next checkpoint."
        )

    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
