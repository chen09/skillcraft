import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "skills" / "artifact-quality-gate" / "scripts" / "validate_artifact_quality.py"
FIXTURE_ARTIFACT = (
    REPO_ROOT
    / "skills"
    / "artifact-quality-gate"
    / "SKILL.md"
)
HIGH_SCORE_REPORT = """# Task goal status outcome
No task was performed.
# Evidence references
See {reference}, Handoff_Inventory.md, and handoff_inventory.json.
# Input output workflow acceptance completion
No artifact was produced.
# Test verification and execution mode
validator validate verify smoke. real_execution mock fixture candidate_only. No test was run.
# Repair rollback
failure recover. receipt handoff entrypoint. No receipt exists.
"""


def run_validator(path: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr)
    return json.loads(proc.stdout)


class ArtifactQualityGateTests(unittest.TestCase):
    def test_evidence_links_split_across_lines_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            (report.parent / "receipt.md").touch()
            cases = {
                "inline title": '[required](missing.md\n "Required evidence")',
                "reference definition": "[required][test]\n\n[test]:\n  missing.md\n",
            }
            for name, link in cases.items():
                with self.subTest(name=name):
                    report.write_text(
                        HIGH_SCORE_REPORT.format(reference=f"[existing](receipt.md) and {link}"),
                        encoding="utf-8",
                    )

                    result = run_validator(report)

                    self.assertEqual(result["threshold"], "usable")
                    self.assertEqual(
                        result["review"]["local_evidence"]["missing"], [str(report.with_name("missing.md"))]
                    )

    def test_inline_code_span_does_not_hide_following_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            (report.parent / "receipt.md").touch()
            ticks = chr(96) * 3
            report.write_text(
                HIGH_SCORE_REPORT.format(reference="[existing](receipt.md)")
                + f"\n{ticks}literal{ticks}\n\n[required](missing.md)\n",
                encoding="utf-8",
            )

            result = run_validator(report)

            self.assertEqual(result["threshold"], "usable")
            self.assertEqual(result["review"]["local_evidence"]["missing"], [str(report.with_name("missing.md"))])

    def test_example_in_blockquoted_fence_is_not_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            (report.parent / "receipt.md").touch()
            ticks = chr(96) * 3
            report.write_text(
                HIGH_SCORE_REPORT.format(reference="[existing](receipt.md)")
                + f"\n> {ticks}md\n> [example](ignored.md)\n> {ticks}\n",
                encoding="utf-8",
            )

            result = run_validator(report)

            self.assertEqual(result["threshold"], "ready")
            self.assertEqual(result["review"]["local_evidence"]["missing"], [])

    def test_escaped_link_opening_bracket_is_literal(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            (report.parent / "receipt.md").touch()
            for prefix, expected in (("\\", "ready"), ("\\\\", "usable")):
                with self.subTest(prefix=prefix):
                    report.write_text(
                        HIGH_SCORE_REPORT.format(reference=f"[existing](receipt.md) and {prefix}[example](missing.md)"),
                        encoding="utf-8",
                    )

                    self.assertEqual(run_validator(report)["threshold"], expected)

    def test_missing_link_with_a_title_prevents_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            (report.parent / "receipt.md").touch()
            report.write_text(
                HIGH_SCORE_REPORT.format(
                    reference='[existing](receipt.md) and [required](missing.md "Required evidence")'
                ),
                encoding="utf-8",
            )

            result = run_validator(report)

            self.assertEqual(result["threshold"], "usable")
            self.assertEqual(result["review"]["local_evidence"]["missing"], [str(report.with_name("missing.md"))])

    def test_reference_links_resolve_their_used_definitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            receipt = report.with_name("test receipt.md")
            receipt.touch()
            report.write_text(
                HIGH_SCORE_REPORT.format(reference="[result][Test Receipt]")
                + '\n[Test receipt]: <test receipt.md> "Test output"\n[unused]: missing.md\n',
                encoding="utf-8",
            )

            result = run_validator(report)

            self.assertEqual(result["threshold"], "ready")
            self.assertEqual(result["review"]["local_evidence"]["present"], [str(receipt)])
            self.assertEqual(result["review"]["local_evidence"]["missing"], [])

    def test_evidence_after_a_longer_closing_fence_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            (report.parent / "receipt.md").touch()
            for marker in (chr(96), "~"):
                with self.subTest(marker=marker):
                    report.write_text(
                        HIGH_SCORE_REPORT.format(reference="[existing](receipt.md)")
                        + f"\n{marker * 3}md\n[example](ignored.md)\n{marker * 4}\n\n[required](missing.md)\n",
                        encoding="utf-8",
                    )

                    result = run_validator(report)

                    self.assertEqual(result["threshold"], "usable")
                    self.assertEqual(result["review"]["local_evidence"]["missing"], [str(report.with_name("missing.md"))])

    def test_windows_review_marks_posix_absolute_paths_unchecked(self):
        check = runpy.run_path(str(VALIDATOR))["check_evidence_references"]
        foreign_path = "/Volumes/another-host/test-receipt.md"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(check.__globals__, {"Path": PureWindowsPath}):
            result = check(f"[remote evidence]({foreign_path})", Path(tmp) / "report.md")

        self.assertEqual(result, {"present": [], "missing": [], "unchecked": [foreign_path]})

    def test_high_score_with_missing_evidence_is_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "report.md"
            missing = artifact.with_name("missing evidence.md")
            (artifact.parent / "existing.md").write_text("Another local artifact\n", encoding="utf-8")
            artifact.write_text(
                HIGH_SCORE_REPORT.format(reference=f"`{missing}` and [existing](existing.md)"),
                encoding="utf-8",
            )

            result = run_validator(artifact)

            self.assertGreaterEqual(result["score"], 90)
            self.assertEqual(result["threshold"], "usable")
            self.assertEqual(result["score_threshold"], "ready")
            self.assertEqual(result["review"]["local_evidence"]["missing"], [str(missing)])
            self.assertEqual(result["review"]["independent_verification"], "not_performed")
            self.assertEqual(result["review"]["acceptance"], "pending")

    def test_relative_markdown_evidence_resolves_from_report_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "report.md"
            receipt = artifact.with_name("test receipt.md")
            receipt.write_text("Test runner output\n", encoding="utf-8")
            artifact.write_text(
                HIGH_SCORE_REPORT.format(reference="[receipt](test%20receipt.md#result)").replace(
                    "No test was run.", "See the test receipt."
                ) + "\n```md\n[template](example-missing.md)\n```\n",
                encoding="utf-8",
            )

            result = run_validator(artifact)

            self.assertEqual(result["threshold"], "ready")
            self.assertEqual(result.get("review", {}).get("local_evidence", {}).get("present"), [str(receipt)])
            self.assertEqual(result["review"]["local_evidence"]["missing"], [])

    def test_unchecked_web_evidence_is_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "report.md"
            artifact.write_text(
                HIGH_SCORE_REPORT.format(reference="[receipt](https://example.com/receipt)"),
                encoding="utf-8",
            )

            result = run_validator(artifact)

            self.assertEqual(result["threshold"], "usable")
            self.assertEqual(result["review"]["local_evidence"]["missing"], [])
            self.assertEqual(
                result["review"]["local_evidence"]["unchecked"], ["https://example.com/receipt"]
            )

    def test_oversized_handoff_is_a_gap_only_when_verbatim_history_is_missing(self):
        base = FIXTURE_ARTIFACT.read_bytes()
        oversized = base + (b"x" * (150_001 - len(base)))
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            at_limit = tmp_path / "at-limit" / "handoff.md"
            at_limit.parent.mkdir()
            at_limit.write_bytes(base + (b"x" * (150_000 - len(base))))
            without_history = tmp_path / "without-history" / "handoff.md"
            without_history.parent.mkdir()
            without_history.write_bytes(oversized)
            with_empty_history = tmp_path / "with-empty-history" / "handoff.md"
            with_empty_history.parent.mkdir()
            with_empty_history.write_bytes(oversized)
            with_empty_history.with_name("handoff-history.md").touch()
            with_history = tmp_path / "with-history" / "handoff.md"
            with_history.parent.mkdir()
            with_history.write_bytes(oversized)
            with_history.with_name("handoff-history.md").write_text("verbatim history\n", encoding="utf-8")

            at_limit_result = run_validator(at_limit)
            missing_result = run_validator(without_history)
            empty_result = run_validator(with_empty_history)
            present_result = run_validator(with_history)

            self.assertEqual(missing_result["score"], present_result["score"])
            self.assertEqual(missing_result["threshold"], present_result["threshold"])
            self.assertEqual(at_limit_result["gaps"], [])
            self.assertEqual(present_result["gaps"], [])
            self.assertEqual(len(empty_result["gaps"]), 1)
            self.assertEqual(len(missing_result["gaps"]), 1)
            self.assertIn("150,001 bytes", missing_result["gaps"][0])
            self.assertIn("handoff-history.md", missing_result["gaps"][0])


if __name__ == "__main__":
    unittest.main()
