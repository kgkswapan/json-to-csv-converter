# json-to-csv (standard library only)

Convert JSON to CSV with sane defaults. Built for locked-down enterprise desktops (no third-party deps).

## Why this exists
- **Bank-friendly:** 100% Python standard library (argparse, json, csv, logging).
- **Practical:** Handles both *dict-of-dicts* and *list-of-dicts* JSON.
- **Usable:** Good CLI UX, helpful errors, stable field inference, optional `--fields`.

## Quick start
```bash
python json_to_csv.py -h

usage: json_to_csv.py [-h] [--output OUTPUT] [--fields FIELDS]
                      [--encoding ENCODING] [--delimiter DELIMITER] [--verbose]
                      input_json
## basic usage

# Auto-writes next to input as data.csv
python json_to_csv.py data.json

# Explicit output path
python json_to_csv.py data.json -o result.csv

# Force field order (columns)
python json_to_csv.py data.json --fields id,name,role

# Verbose logs
python json_to_csv.py data.json -v

# Windows/Excel users: in some locales Excel expects ; as separator
python json_to_csv.py data.json --delimiter ";"
```
## Supported input shapes

### Dict of Dicts
```bash
{
  "1": {"name": "Alice", "role": "Admin"},
  "2": {"name": "Bob",   "role": "User" }
}

# output
id,name,role
1,Alice,Admin
2,Bob,User
```

### List of Dicts
```bash
[
  {"id": "1", "name": "Alice", "role": "Admin"},
  {"id": "2", "name": "Bob",   "role": "User" }
]
```

## Options
--output, -o Path to output CSV. Defaults to <input>.csv.

--fields Comma-separated list of columns (order enforced). Extra JSON keys are ignored.

--encoding Text encoding (default: utf-8).

--delimiter CSV delimiter (default: ,).

--verbose, -v Verbose logging.

## Logging & exit codes

--INFO/DEBUG logs go to stdout/stderr depending on level. Use -v for debugging.

--Exit codes:

| Code | Meaning                                 |
| ---: | --------------------------------------- |
|    0 | Success                                 |
|    1 | OS errors (file not found/permissions)  |
|    2 | Data/usage errors (bad JSON, bad shape) |
|   99 | Unexpected exception                    |

## Design Notes
No third-party modules. Safe for restricted environments.

Deterministic columns. If --fields is omitted, columns are inferred in a stable order.

Windows-safe CSV. Uses newline='' to avoid blank lines.

Performance: Loads JSON into memory. For very large JSON files, consider chunking upstream or NDJSON (future enhancement).

## Examples

Force a specific column set (drops others silently):
```bash
python json_to_csv.py data.json --fields id,name,role
```

Change delimiter to semicolon (common in EU Excel):
```bash
python json_to_csv.py data.json --delimiter ";"
```

Custom encoding:
```bash
python json_to_csv.py data.json --encoding cp1252
```

## Security & compliance
Pure read → transform → write. No network calls, no eval/exec.

Predictable I/O and explicit error messages for auditability.

## License
MIT
