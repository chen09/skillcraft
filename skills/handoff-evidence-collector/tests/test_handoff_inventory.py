import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
COLLECTOR = REPO_ROOT / "skills" / "handoff-evidence-collector" / "scripts" / "handoff_inventory.py"
VALIDATOR = REPO_ROOT / "skills" / "agent-continuity" / "scripts" / "validate_handoff.py"
BUNDLED_QUALITY_VALIDATOR = (
    REPO_ROOT
    / "skills"
    / "handoff-evidence-collector"
    / "scripts"
    / "validate_artifact_quality.py"
)
FIXTURE_HANDOFF = (
    REPO_ROOT
    / "skills"
    / "handoff-evidence-collector"
    / "examples"
    / "smoke-root"
    / "project-a"
    / "handoff.md"
)
FIXTURE_CURSOR_HANDOFF = (
    REPO_ROOT
    / "skills"
    / "handoff-evidence-collector"
    / "examples"
    / "smoke-root"
    / "project-b"
    / "docs"
    / "cursor-example-handoff.md"
)


class HandoffInventoryTests(unittest.TestCase):
    def test_collector_reuses_current_interpreter_when_python3_is_not_on_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_root = tmp_path / "01_RPA別" / "03_実装候補"
            source_root.mkdir(parents=True)
            shutil.copyfile(FIXTURE_HANDOFF, source_root / "handoff.md")
            output_root = tmp_path / "output"

            env = os.environ.copy()
            env["PATH"] = ""
            proc = subprocess.run(
                [
                    sys.executable,
                    str(COLLECTOR),
                    "--output-root",
                    str(output_root),
                    "--root",
                    str(tmp_path / "01_RPA別"),
                    "--validator-path",
                    str(VALIDATOR),
                    "--execution-mode",
                    "fixture",
                ],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                timeout=20,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads((output_root / "work" / "handoff_inventory.json").read_text(encoding="utf-8"))
            self.assertEqual(data["records"][0]["validation"]["returncode"], 0)
            self.assertIn("01_RPA別", data["records"][0]["validation"]["stdout"])

    def test_collector_decodes_utf8_validator_output_under_non_utf8_locale(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_root = tmp_path / "01_RPA別" / "03_実装候補"
            source_root.mkdir(parents=True)
            shutil.copyfile(FIXTURE_HANDOFF, source_root / "handoff.md")
            output_root = tmp_path / "output"
            validator = tmp_path / "validator.py"
            validator.write_text(
                "import sys\n"
                "message = f'OK: 日本語-中文-🚀/{sys.argv[1]}\\n'.encode('utf-8') + b'\\xff\\n'\n"
                "sys.stdout.buffer.write(message)\n"
                "sys.stderr.write('diagnostic | 日本語-🚀\\nsecond line\\n')\n",
                encoding="utf-8",
            )

            env = os.environ.copy()
            env.update(
                {
                    "LANG": "C",
                    "LC_ALL": "C",
                    "PYTHONCOERCECLOCALE": "0",
                    "PYTHONIOENCODING": "cp932",
                    "PYTHONUTF8": "0",
                }
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(COLLECTOR),
                    "--output-root",
                    str(output_root),
                    "--root",
                    str(tmp_path / "01_RPA別"),
                    "--validator-path",
                    str(validator),
                    "--execution-mode",
                    "fixture",
                ],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                timeout=20,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads((output_root / "work" / "handoff_inventory.json").read_text(encoding="utf-8"))
            self.assertEqual(data["records"][0]["validation"]["returncode"], 0)
            self.assertIn("日本語-中文-🚀", data["records"][0]["validation"]["stdout"])
            self.assertIn("�", data["records"][0]["validation"]["stdout"])
            self.assertIn("diagnostic | 日本語-🚀", data["records"][0]["validation"]["stderr"])
            markdown = (output_root / "Handoff_Inventory.md").read_text(encoding="utf-8")
            record_lines = [line for line in markdown.splitlines() if line.startswith("| `")]
            self.assertEqual(len(record_lines), 1)
            self.assertIn(r"diagnostic \| 日本語-🚀<br>second line", record_lines[0])

    def test_inventory_exposes_size_boundary_without_breaking_markdown_records(self):
        base = FIXTURE_HANDOFF.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_root = tmp_path / "source"
            for name, size_bytes in (("at-limit", 150_000), ("over-limit", 150_001)):
                handoff = source_root / name / "handoff.md"
                handoff.parent.mkdir(parents=True)
                handoff.write_bytes(base + (b"x" * (size_bytes - len(base))))
            output_root = tmp_path / "output"

            proc = subprocess.run(
                [
                    sys.executable,
                    str(COLLECTOR),
                    "--output-root",
                    str(output_root),
                    "--root",
                    str(source_root),
                    "--validator-path",
                    str(VALIDATOR),
                    "--execution-mode",
                    "fixture",
                ],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads((output_root / "work" / "handoff_inventory.json").read_text(encoding="utf-8"))
            self.assertEqual(data["size_warning_threshold_bytes"], 150_000)
            records = {Path(record["path"]).parent.name: record for record in data["records"]}
            self.assertEqual(records["at-limit"]["size"], 150_000)
            self.assertEqual(records["at-limit"]["size_bytes"], 150_000)
            self.assertFalse(records["at-limit"]["oversized"])
            self.assertEqual(records["over-limit"]["size"], 150_001)
            self.assertEqual(records["over-limit"]["size_bytes"], 150_001)
            self.assertTrue(records["over-limit"]["oversized"])
            self.assertIn("WARN:", records["over-limit"]["validation"]["stdout"])
            self.assertIn("\nOK:", records["over-limit"]["validation"]["stdout"])

            markdown = (output_root / "Handoff_Inventory.md").read_text(encoding="utf-8")
            self.assertIn("| Path | Kind | Size (bytes) | Oversized |", markdown)
            record_lines = [line for line in markdown.splitlines() if line.startswith("| `")]
            self.assertEqual(len(record_lines), 2)
            over_limit_line = next(line for line in record_lines if "over-limit" in line)
            self.assertIn("| 150001 | yes |", over_limit_line)
            self.assertIn("<br>", over_limit_line)

    def test_bundled_quality_validator_reports_oversized_handoff_gap(self):
        base = FIXTURE_HANDOFF.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            handoff = Path(tmp) / "handoff.md"
            handoff.write_bytes(base + (b"x" * (150_001 - len(base))))

            proc = subprocess.run(
                [sys.executable, str(BUNDLED_QUALITY_VALIDATOR), str(handoff)],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            self.assertEqual(len(result["gaps"]), 1)
            self.assertIn("oversized_handoff_without_history", result["gaps"][0])

    def test_history_is_evidence_only_while_existing_classifications_stay_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_root = tmp_path / "source"
            fixtures = {
                source_root / "live" / "handoff.md": FIXTURE_HANDOFF.read_text(encoding="utf-8"),
                source_root / "history" / "handoff-history.md": FIXTURE_HANDOFF.read_text(encoding="utf-8"),
                source_root / "cursor" / "cursor-example-handoff.md": FIXTURE_CURSOR_HANDOFF.read_text(
                    encoding="utf-8"
                ),
                source_root / "guides" / "install-handoff.md": "# Handoff Guide\n\nInstall this skill locally.\n",
                source_root / "notes" / "notes-handoff.md": "# Working Notes\n\nContinuation evidence.\n",
                source_root / "references" / "handoff.md": FIXTURE_HANDOFF.read_text(encoding="utf-8"),
            }
            for path, text in fixtures.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            output_root = tmp_path / "output"

            proc = subprocess.run(
                [
                    sys.executable,
                    str(COLLECTOR),
                    "--output-root",
                    str(output_root),
                    "--root",
                    str(source_root),
                    "--validator-path",
                    str(VALIDATOR),
                    "--execution-mode",
                    "fixture",
                ],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads((output_root / "work" / "handoff_inventory.json").read_text(encoding="utf-8"))
            self.assertEqual(
                data["counts"],
                {
                    "agent_continuity_handoff": 1,
                    "cursor_handoff": 1,
                    "handoff_history": 1,
                    "handoff_like": 1,
                    "template_or_reference": 1,
                    "usage_handoff_or_guide": 1,
                },
            )
            history = next(record for record in data["records"] if record["kind"] == "handoff_history")
            self.assertFalse(history["validation"]["attempted"])


if __name__ == "__main__":
    unittest.main()
