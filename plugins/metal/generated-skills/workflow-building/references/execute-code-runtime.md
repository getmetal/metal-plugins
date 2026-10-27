# Execute-Code Sandbox Runtime

Use this reference when building or debugging an `executeCode` step, choosing Python libraries, or deciding whether a file should live in structured output, an artifact, or a first-class run Output record.

## Runtime

- Python major/minor: 3.12.
- Node.js major: 24.
- OS family: Debian Bookworm slim, running as non-root user `sandbox`.
- Home and default working directory: `/home/sandbox`.
- All steps of a run share this one sandbox: parallel iterator items, branch arms, and sequential steps run on the same filesystem, so a path that does not vary per item is shared state between concurrent items.
- PATH includes `/opt/venv/bin` and `/opt/node/bin`.
- `PYTHONPATH` includes `/home/sandbox/scripts`.
- The sandbox has no network egress. Do not rely on package installation that fetches from npm, PyPI, apt, or another registry. External `curl` and `git clone` fetches fail for the same reason.
- `npm` is installed, but code must use the baked Node package set. Runtime `pip`, `setuptools`, and `wheel` are removed, so Python dependencies must also be baked into the image.
- This reference does not pin package patch versions. Code that depends on a specific version must verify it in the runtime before using version-specific behavior.

## System Tools

Available command-line tools include `bash`, `python3`, `node`, `npm`, `curl`, `gcc`, `git`, `jq`, `pandoc`, `pdftotext` and other `poppler-utils`, `qpdf`, `tesseract-ocr`, `tini`, `unzip`, and LibreOffice Calc, Impress, and Writer in no-GUI mode.

## Python capabilities

The baked Python environment supports tabular analysis, statistics, Arrow data, spreadsheet authoring, Word and PowerPoint documents, PDF parsing and generation, OCR, HTML-to-PDF rendering, templates, dates, and XML processing. Representative packages include `numpy`, `pandas`, `scipy`, `statsmodels`, `pyarrow`, `openpyxl`, `xlsxwriter`, `python-docx`, `python-pptx`, `pypdf`, `pdfplumber`, `pillow`, `pytesseract`, `reportlab`, `jinja2`, `weasyprint`, and `lxml`. Treat this as a capability guide, not an exhaustive package inventory.

## Node capabilities

The entrypoint links `/home/sandbox/node_modules` to the preinstalled package set under `/opt/sandbox-node/node_modules`. The baked packages support PDF work, Word and PowerPoint generation, React rendering, image processing, linting, and shared JavaScript globals. Representative packages include `pdf-lib`, `pdfjs-dist`, `docx`, `pptxgenjs`, `react`, `react-dom`, `react-icons`, `sharp`, `eslint`, and `globals`. Treat this as a capability guide, not an exhaustive package inventory.

## Helper Scripts

The image copies built-in helper scripts into `/opt/sandbox-scripts`, and the entrypoint hydrates them into `/home/sandbox/scripts` on container start. Script groups include `docx_tools`, `pdf_tools`, `pptx_tools`, `xlsx_tools`, `dcf_model_tools`, `redline_validator`, `web_tools`, and shared `office_tools`.

## Execute-Code Contract

- The workflow runner writes the literal script to `/home/sandbox/.workflow_steps/<pathSegment>/script.py`.
- The runner writes rendered input JSON to `/home/sandbox/.workflow_steps/<pathSegment>/input.json`.
- The runner calls `python3 <script.py> <input.json>`, so scripts read workflow input from `sys.argv[1]`.
- The `script` field is not template-rendered. The `input`, `workingDirectory`, `inputFiles[].filename`, `inputFiles[].dataEntityId`, `inputFiles[].path`, `outputFiles[].path`, and `outputFiles[].filename` fields are template-rendered before execution, and every rendered value is validated before the first sandbox side effect.
- `workingDirectory` must render to an absolute path without glob characters. Omitted, it defaults to `/home/sandbox`; a configured template that renders empty fails the run.
- Empty `input` renders as `{}`. With `inputFiles`, rendered input must be a JSON object and `_inputFiles` is reserved because the runner injects the uploaded-file manifest there.
- The runner captures stdout, stderr, and exit code. With `outputSchema`, stdout must be one JSON value matching the schema before the step publishes declared `outputFiles`.
- Keep execute-code dependencies inspectable through mounted files, artifacts, `inputFiles`, or readable source code. Do not reconstruct hidden files from encoded payloads such as base64, compressed strings, hex blobs, marshal or pickle payloads, large string constants, or decoded `exec` patterns.

## File Publishing

- Each `inputFiles[]` entry declares exactly one source: `filename` or `dataEntityId`. Both are template-renderable.
- `inputFiles.filename` uploads a file through `sandbox_upload_artifact` semantics against the run's artifacts and attached files. Use an exact filename whenever possible. Partial filename matching is acceptable only when the match is known unique; it is name matching, not glob matching. The rendered filename must not contain path separators.
- `inputFiles.dataEntityId` uploads a platform data entity through `sandbox_upload_data_entity`, staged at the exact rendered destination via `sandbox_path`. The rendered value must be a 24-character hex ObjectID, and the run principal's access checks apply.
- `inputFiles[]` does not support glob patterns; each entry resolves one source to one exact destination, and `inputFiles[].path` must render to an absolute path with no glob syntax.
- An executeCode step inside an iterator with concurrency > 1 (the default is 6) must give every path it reads or writes an item-unique value (the item's document ID, itemIndex, or another per-item field), because items run concurrently on the shared sandbox. A constant path is last-writer-wins: concurrent items overwrite each other's staged file and can read another item's data. For example, stage a per-item workbook at /home/sandbox/cmt_<workbook_doc_id>.xlsx, never /home/sandbox/cmt.xlsx.
- `outputFiles` are the only files the runner publishes from the sandbox. Files left on disk without a declared `outputFiles` entry are not workflow artifacts or run Output records.
- Exact output paths must exist after the script exits. Missing exact paths fail after script execution.
- Glob output paths support `*`, `?`, bracket expressions such as `[0-9]`, and recursive `**`. They expand after script execution, return regular files only, sort matches, and fail when they match zero files or more than 25 files. `outputFiles[].filename` is invalid on a glob path. `[` counts as glob syntax everywhere, so it is rejected in the working directory and input paths.
- `outputFiles[].createOutput: true` creates first-class run Output records for matched files and stores successful IDs in `results.outputIds`. Those Output records are what the run UI presents as workflow files.
