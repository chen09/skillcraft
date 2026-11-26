import json
from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "evals" / "check_resume_trace.py"


def start(call_id, path):
    return {"event": "read_start", "id": call_id, "path": path}


def result(call_id, *, ok=True, complete=True, text=None):
    event = {"event": "read_result", "id": call_id, "ok": ok, "complete": complete}
    if text is not None:
        event["text"] = text
    return event


def run_case(case, events):
    trace = "\n".join(json.dumps(event) for event in events)
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "--case", case, "-"],
        input=trace,
        text=True,
        capture_output=True,
        check=False,
    )


class CheckResumeTraceTests(unittest.TestCase):
    def assert_passes(self, case, events):
        report = run_case(case, events)
        self.assertEqual(report.returncode, 0, report.stderr)

    def assert_rejects(self, case, events, reason):
        report = run_case(case, events)
        self.assertEqual(report.returncode, 1, report.stderr)
        self.assertIn(reason, report.stderr)

    def test_generic_allows_parallel_reads_after_handoff_result(self):
        self.assert_passes("generic", [
            start("h", "handoff.md"), result("h"),
            start("s", "current-state.txt"), start("r", "old-chat-retry.txt"),
            result("r"), result("s"),
        ])

    def test_generic_rejects_start_before_handoff_result_even_if_it_returns_later(self):
        self.assert_rejects("generic", [
            start("h", "handoff.md"), start("s", "current-state.txt"),
            result("h"), result("s"),
            start("r", "old-chat-retry.txt"), result("r"),
        ], "before handoff.md completed successfully")

    def test_generic_requires_successful_complete_handoff_read(self):
        for handoff_result in (result("h", ok=False, complete=False), result("h", complete=False)):
            with self.subTest(handoff_result=handoff_result):
                self.assert_rejects("generic", [
                    start("h", "handoff.md"), handoff_result,
                    start("s", "current-state.txt"), result("s"),
                    start("r", "old-chat-retry.txt"), result("r"),
                ], "before handoff.md completed successfully")

    def test_generic_can_retry_a_failed_handoff_before_other_reads(self):
        self.assert_passes("generic", [
            start("h1", "handoff.md"), result("h1", ok=False, complete=False),
            start("h2", "handoff.md"), result("h2"),
            start("s", "current-state.txt"), result("s"),
            start("r", "old-chat-retry.txt"), result("r"),
        ])

    def test_generic_rejects_unrelated_history_even_after_handoff(self):
        self.assert_rejects("generic", [
            start("h", "handoff.md"), result("h"),
            start("r", "old-chat-bulk.txt"), result("r"),
        ], "unrelated")

    def test_dependent_selects_the_archive_declared_by_the_state_result(self):
        for archive in ("old-chat-east.txt", "old-chat-west.txt"):
            with self.subTest(archive=archive):
                self.assert_passes("dependent", [
                    start("h", "handoff.md"), result("h"),
                    start("s", "current-state.txt"), result("s", text=f"archive: {archive}"),
                    start("r", archive), result("r"),
                ])

    def test_dependent_accepts_a_numbered_state_result_with_crlf(self):
        self.assert_passes("dependent", [
            start("h", "handoff.md"), result("h"),
            start("s", "current-state.txt"),
            result("s", text="1: Current job: KITE-47\r\n2: archive: old-chat-west.txt\r\n"),
            start("r", "old-chat-west.txt"), result("r"),
        ])

    def test_dependent_does_not_count_an_archive_read_started_during_state_read(self):
        self.assert_rejects("dependent", [
            start("h", "handoff.md"), result("h"), start("s", "current-state.txt"),
            start("r", "old-chat-west.txt"),
            result("s", text="archive: old-chat-west.txt"), result("r"),
        ], "before current-state.txt completed successfully")

    def test_dependent_rejects_stale_archive_even_if_the_correct_one_is_also_read(self):
        self.assert_rejects("dependent", [
            start("h", "handoff.md"), result("h"),
            start("s", "current-state.txt"),
            result("s", text="archive: old-chat-west.txt"),
            start("r1", "old-chat-east.txt"), result("r1"),
            start("r2", "old-chat-west.txt"), result("r2"),
        ], "selected old-chat-west.txt")

    def test_unmatched_result_cannot_unlock_the_handoff_gate(self):
        self.assert_rejects("generic", [
            start("h", "handoff.md"), result("wrong"),
            start("s", "current-state.txt"), result("s"),
        ], "without a matching read_start")


if __name__ == "__main__":
    unittest.main()
