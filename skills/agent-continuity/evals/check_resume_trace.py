"""Check task-file read dependencies in a normalized continuity trace."""

import argparse
import json
from pathlib import Path
import re
import sys


HANDOFF = "handoff.md"
STATE = "current-state.txt"
GENERIC_HISTORY = "old-chat-retry.txt"
DEPENDENT_HISTORY = {"old-chat-east.txt", "old-chat-west.txt"}
ARCHIVE_FIELD = re.compile(
    r"[ \t]*(?:\d+:[ \t]*)?archive:[ \t]*(old-chat-(?:east|west)\.txt)[ \t]*"
)


def archive_choices(text):
    if not isinstance(text, str):
        return []
    return [
        match[1] for line in text.splitlines() if (match := ARCHIVE_FIELD.fullmatch(line))
    ]


def check_trace(lines, case):
    histories = DEPENDENT_HISTORY if case == "dependent" else {GENERIC_HISTORY}
    allowed = {HANDOFF, STATE, *histories}
    pending = {}
    finished = set()
    complete = set()
    selected = None

    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("expected a JSON object")
            call_id = record.get("id")
            if not isinstance(call_id, str) or not call_id:
                raise ValueError("expected a non-empty read ID")

            if record.get("event") == "read_start":
                path = record.get("path")
                if not isinstance(path, str) or path not in allowed:
                    raise ValueError("read of an unrelated or unknown task file")
                if call_id in pending or call_id in finished:
                    raise ValueError("duplicate read ID")
                if path != HANDOFF and HANDOFF not in complete:
                    raise ValueError(f"{path} started before handoff.md completed successfully")
                if case == "dependent" and path in histories:
                    if STATE not in complete:
                        raise ValueError(f"{path} started before current-state.txt completed successfully")
                    if path != selected:
                        raise ValueError(f"read {path} but current-state.txt selected {selected}")
                pending[call_id] = path

            elif record.get("event") == "read_result":
                if call_id not in pending:
                    raise ValueError("read_result without a matching read_start")
                path = pending.pop(call_id)
                finished.add(call_id)
                ok, whole = record.get("ok"), record.get("complete")
                if not isinstance(ok, bool) or not isinstance(whole, bool):
                    raise ValueError("read_result requires boolean ok and complete fields")
                if ok and whole:
                    if case == "dependent" and path == STATE:
                        choices = archive_choices(record.get("text"))
                        if len(choices) != 1:
                            raise ValueError("current-state.txt must name exactly one supported archive")
                        if selected is not None and choices[0] != selected:
                            raise ValueError("archive selection changed during the fixture run")
                        selected = choices[0]
                    complete.add(path)
            else:
                raise ValueError("expected a read_start or read_result event")
        except ValueError as error:
            raise ValueError(f"line {number}: {error}") from error

    if pending:
        raise ValueError("read_start without a matching read_result")
    required = {HANDOFF, STATE, selected if case == "dependent" else GENERIC_HISTORY}
    missing = [path or "selected archive" for path in required - complete]
    if missing:
        raise ValueError("missing successful complete reads: " + ", ".join(sorted(missing)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=("generic", "dependent"))
    parser.add_argument("trace", help="normalized UTF-8 JSONL path, or - for stdin")
    args = parser.parse_args()
    try:
        if args.trace == "-":
            check_trace(sys.stdin, args.case)
        else:
            with Path(args.trace).open(encoding="utf-8") as trace:
                check_trace(trace, args.case)
    except (OSError, ValueError) as error:
        print(f"FAIL {args.case}: {error}", file=sys.stderr)
        return 1
    print(f"PASS {args.case}: task-file read dependencies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
