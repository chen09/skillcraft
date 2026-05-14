# excel-deep-parsing-agent

Portable Cursor Skill for deep Office analysis with traceable outputs.

## What this skill does

- Deep parse Office files (`.xlsx/.xlsm/.xls/.csv/.docx/.doc/.pptx/.ppt`)
- Inspect spreadsheet workbook/sheet/cell structures (including hidden sheet/object signals)
- Inspect Word/PPT structures (paragraphs/tables/slides/notes/image signals)
- Export visual artifacts (PDF/PNG when available)
- Run OCR over visual exports
- Produce human summary and machine-readable JSON

## Directory

```text
excel-deep-parsing-agent/
├── SKILL.md
├── reference.md
├── examples.md
├── output_template.md
├── troubleshooting.md
├── checklist.md
├── handoff.md
├── FAQ.md
├── CHANGELOG.md
├── VERSION
├── CONTRIBUTING.md
├── LICENSE
├── runtime/
│   ├── __init__.py
│   ├── executables.py
│   └── pipeline.py
└── scripts/
    ├── run_pipeline.py
    ├── export_visuals.py
    ├── ocr_runner.py
    ├── smoke_test.py
    └── requirements.txt
```

## Quick start

Use a virtual environment or other Python runtime that already has the required packages. `openpyxl` is the only core package for spreadsheet parsing; the rest improve markdown, document, visual, and OCR coverage.

Install dependencies:

```bash
python -m pip install -r .cursor/skills/excel-deep-parsing-agent/scripts/requirements.txt
```

If the network is restricted, install from an internal mirror or wheelhouse, for example:

```bash
python -m pip install --no-index --find-links "<wheelhouse_dir>" -r .cursor/skills/excel-deep-parsing-agent/scripts/requirements.txt
```

Smoke test:

```bash
python .cursor/skills/excel-deep-parsing-agent/scripts/smoke_test.py
```

Full run:

```bash
python .cursor/skills/excel-deep-parsing-agent/scripts/run_pipeline.py --input-path "<input_path>" --output-root "<output_root>"
```

## Known limitations

- File type handling is extension-driven first, then parser-validated. Unsupported or corrupt files are reported with warnings instead of treated as success.
- `markitdown` base install may not include all format extras (`xlsx`, `docx`), so markdown extraction can fail for some files while deep parsing still continues.
- `.xls/.doc/.ppt` require LibreOffice conversion before deep parsing. The runtime checks common `soffice` locations on macOS, Windows, and PATH. If LibreOffice is missing, those legacy formats are reported with warnings and lower confidence.
- PDF export also depends on `soffice`; without it, embedded-image extraction and structural parsing still run where possible.
- Local OCR requires both the `pytesseract` Python package and the `tesseract` executable. The runtime checks common `tesseract` locations on macOS, Windows, and PATH. If either is missing, OCR artifacts record a skipped status.
- Scripts are cross-platform Python, but example paths may use Windows `D:/...` because many source design packages are Windows-authored.
- Runtime output avoids absolute source paths in result artifacts. Use the original command line or file inventory root to map relative paths back to local files.

Recommended optional setup:

```bash
python -m pip install "markitdown[all]"
```

## Output artifacts

- `file_inventory.md`
- `workbook_inventory.md`
- `document_inventory.md`
- `extracted_markdown/`
- `visual_exports/`
- `ocr_results/`
- `deep_reading_notes/`
- `final_summary.md`
- `structured_data.json`

## Documentation map

- Execution rules: [`SKILL.md`](SKILL.md)
- Full policy text: [`reference.md`](reference.md)
- Practical examples: [`examples.md`](examples.md)
- QA gate: [`checklist.md`](checklist.md)
- Troubleshooting: [`troubleshooting.md`](troubleshooting.md)
- Team handoff: [`handoff.md`](handoff.md)
- FAQ: [`FAQ.md`](FAQ.md)
