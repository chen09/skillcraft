import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "skills" / "agent-continuity" / "scripts" / "validate_handoff.py"
FIXTURE_HANDOFF = (
    REPO_ROOT
    / "skills"
    / "agent-continuity"
    / "references"
    / "handoff-template.md"
)


class ValidateHandoffTests(unittest.TestCase):
    def test_size_warning_starts_above_150000_bytes_without_failing_validation(self):
        base = FIXTURE_HANDOFF.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            for size_bytes, expect_warning in ((150_000, False), (150_001, True)):
                with self.subTest(size_bytes=size_bytes):
                    handoff = Path(tmp) / f"handoff-{size_bytes}.md"
                    handoff.write_bytes(base + (b"x" * (size_bytes - len(base))))

                    proc = subprocess.run(
                        [sys.executable, str(VALIDATOR), str(handoff)],
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=20,
                    )

                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    self.assertEqual("WARN:" in proc.stdout, expect_warning)
                    self.assertTrue(proc.stdout.rstrip().endswith(f"OK: {handoff}"))


if __name__ == "__main__":
    unittest.main()
