#!/usr/bin/env python3
"""Quick validation for skill runtime and dependencies."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path


def main() -> int:
    skill_root = Path(__file__).resolve().parents[1]
    if str(skill_root) not in sys.path:
        sys.path.insert(0, str(skill_root))

    from runtime.executables import find_executable

    report = {
        "python": {"status": "ok", "detail": f"{sys.implementation.name} {sys.version.split()[0]}"},
        "imports": {"core": {}, "optional": {}},
        "executables": {},
    }

    for module in ("openpyxl", "runtime.pipeline"):
        try:
            __import__(module)
            report["imports"]["core"][module] = {"status": "ok"}
        except Exception as exc:  # noqa: BLE001
            report["imports"]["core"][module] = {"status": "missing_or_failed", "detail": str(exc)}

    for module in ("pytesseract", "PIL", "pypdfium2", "docx", "pptx", "win32com"):
        try:
            __import__(module)
            report["imports"]["optional"][module] = {"status": "ok"}
        except Exception as exc:  # noqa: BLE001
            report["imports"]["optional"][module] = {"status": "missing_or_failed", "detail": str(exc)}

    for exe in ("markitdown", "soffice", "powershell", "tesseract"):
        path = find_executable(exe)
        report["executables"][exe] = {"status": "ok" if path else "missing", "detail": "available" if path else ""}
    report["executables"]["windows_excel_automation"] = {
        "status": "available_if_excel_installed" if platform.system() == "Windows" else "not_applicable",
        "detail": "uses pywin32 when installed, otherwise PowerShell COM on Windows",
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))

    failed_core = [k for k, v in report["imports"]["core"].items() if v["status"] != "ok"]
    return 1 if failed_core else 0


if __name__ == "__main__":
    raise SystemExit(main())
