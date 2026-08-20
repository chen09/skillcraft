import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "skills" / "artifact-quality-gate" / "scripts" / "validate_artifact_quality.py"
FIXTURE_ARTIFACT = (
    REPO_ROOT
    / "skills"
    / "artifact-quality-gate"
    / "SKILL.md"
)


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
