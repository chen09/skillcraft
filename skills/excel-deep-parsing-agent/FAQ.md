# FAQ

## Q1. Can this skill run in any repository?

Yes. Runtime is bundled under `runtime/`, so scripts do not depend on repository-specific `tools/` paths.

## Q2. Is `markitdown` mandatory?

No. If missing, markdown extraction is logged as skipped, and other stages continue.

## Q2-1. Why can markitdown fail even when installed?

Some file converters are optional extras in MarkItDown.
If `.xlsx` or `.docx` markdown extraction fails, install:

```bash
python -m pip install "markitdown[all]"
```

## Q3. How is `.xls` handled?

The pipeline attempts `.xls -> .xlsx` conversion via LibreOffice (`soffice`) and then performs deep parse.
If conversion is unavailable, it logs warnings and marks uncertainty.

## Q3-1. How are `.doc` and `.ppt` handled?

They use the same legacy conversion pattern via LibreOffice:

- `.doc -> .docx`
- `.ppt -> .pptx`

If `soffice` is unavailable or conversion fails, the document is still listed, but deep structure extraction is limited and warnings are written.

## Q4. Why are OCR results weak?

Likely image quality, language model data, or OCR backend setup. See `troubleshooting.md`.

## Q4-1. Do I need `soffice` and `tesseract`?

Recommended, not always mandatory:

- `soffice`: improves legacy conversion (`.xls/.doc/.ppt`) and PDF export
- `tesseract`: enables local OCR extraction

The Python package `pytesseract` is also required for local OCR. If either package or executable is missing, OCR result files use `skipped` or `failed` status.

## Q5. What is the minimum output set to share with stakeholders?

At least:

- `file_inventory.md`
- `workbook_inventory.md`
- `deep_reading_notes/`
- `final_summary.md`
- `structured_data.json`

## Q6. Where should I check quality before delivery?

Use `checklist.md` and validate all required fields in `final_summary.md`.

## Q7. Why do output filenames contain hashes?

Hashes prevent collisions when different source files share a basename, such as `sample.xlsx`, `sample.docx`, and `subdir/sample.xlsx`.

## Q8. Do result artifacts include absolute local paths?

No. Shared outputs use relative source paths and relative output artifact paths to avoid leaking local usernames, mount points, or customer folder structure outside the agreed input scope.
