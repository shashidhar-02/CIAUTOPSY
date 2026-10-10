# Configuration & CLI Reference

CIAUTOPSY is configured through command-line options and sensible built-in defaults (`ciautopsy.config`).

---

## 1. CLI Commands & Options

### `ciautopsy analyze`

Analyze a target log file or ZIP archive:

```bash
ciautopsy analyze <TARGET> [OPTIONS]
```

#### Arguments
- `TARGET`: Path to a CI log file (`.log`, `.txt`) or ZIP archive (`.zip`).

#### Options
- `-b, --baseline PATH`: Optional path to a successful baseline log for differential analysis.
- `-f, --format [console|markdown|json]`: Output format (default: `console`).
- `-o, --output PATH`: Write output to the specified file path instead of stdout.
- `--max-lines INT`: Maximum lines to ingest (default: `50000`).

---

### `ciautopsy rules`

List all active diagnostic rules registered in the catalog:

```bash
ciautopsy rules
```

---

### `ciautopsy version`

Display CIAUTOPSY version, release name, and JSON schema compatibility:

```bash
ciautopsy version
```

---

## 2. Ingestion & Security Defaults

The default limits configured in `ciautopsy.config.IngestionConfig` and `SecurityConfig` are:

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `max_lines` | `50,000` | Maximum number of log lines ingested per run |
| `max_line_length` | `8,192` | Maximum character length of a single log line |
| `max_zip_file_size_bytes` | `52,428,800` (50 MB) | Maximum size of an uploaded ZIP archive |
| `max_zip_members` | `200` | Maximum number of files inside a ZIP archive |
| `max_zip_uncompressed_bytes` | `104,857,600` (100 MB) | Maximum uncompressed size per file |
| `max_compression_ratio` | `100.0` | Maximum allowable compression ratio before rejection |

---

## 3. Exit Code Contract

CIAUTOPSY adheres to a stable, documented exit code contract:

| Exit Code | Meaning |
|-----------|---------|
| `0` | Analysis completed successfully (regardless of whether the target CI build passed or failed). |
| `2` | Bad arguments or invalid input (e.g. file not found, unreadable archive, security limit exceeded). |
| `3` | Internal processing error occurred during diagnostic analysis. |
