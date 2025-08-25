#!/usr/bin/env python3
"""
json_to_csv.py — Convert JSON to CSV with sane defaults (standard library only).

Usage:
  python json_to_csv.py input.json [--output output.csv] [--fields id,name,role]
                                  [--encoding utf-8] [--delimiter ,] [--verbose]

Behavior:
- If --output is omitted, writes alongside the JSON file with .csv extension.
- Accepts JSON as:
    1) dict of dicts: {"1": {"name": "Alice", "role": "Admin"}, ...}
       -> 'id' column comes from the outer dict key (unless you override --fields)
    2) list of dicts: [{"id": "1", "name": "Alice", "role": "Admin"}, ...]
- If --fields is omitted, fields are inferred from data in a stable order.
"""

from __future__ import annotations
import argparse
import csv
import json
import logging
import os
import sys
from typing import Iterable, List, Dict, Any, Tuple

def infer_fields_from_list(rows: List[Dict[str, Any]]) -> List[str]:
    """Infer stable field order from a list of dicts."""
    seen: Dict[str, None] = {}
    for row in rows:
        for k in row.keys():
            if k not in seen:
                seen[k] = None
    return list(seen.keys())

def normalize_records(data: Any, default_id_key: str = "id") -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Normalize supported JSON structures to a list of flat dicts and a field list.
    Supported:
      - dict of dicts: outer keys become `default_id_key` unless already present
      - list of dicts
    """
    if isinstance(data, dict):
        records: List[Dict[str, Any]] = []
        for k, v in data.items():
            if not isinstance(v, dict):
                raise TypeError("When JSON is a dict, its values must be objects (dicts).")
            row = dict(v)
            if default_id_key not in row:
                row[default_id_key] = k
            records.append(row)
        fields = infer_fields_from_list(records)
        if default_id_key in fields:
            fields = [default_id_key] + [f for f in fields if f != default_id_key]
        return records, fields

    if isinstance(data, list):
        if not all(isinstance(x, dict) for x in data):
            raise TypeError("When JSON is a list, all elements must be objects (dicts).")
        fields = infer_fields_from_list(data)
        return data, fields

    raise TypeError("Top-level JSON must be either an object (dict) or an array (list).")

def json_to_csv(
    json_file: str,
    output_csv: str | None = None,
    fields: List[str] | None = None,
    encoding: str = "utf-8",
    delimiter: str = ",",
) -> str:
    """Convert a JSON file to CSV. Returns the output path."""
    if output_csv is None:
        base, _ = os.path.splitext(json_file)
        output_csv = base + ".csv"

    logging.debug("Reading JSON: %s", json_file)
    with open(json_file, "r", encoding=encoding) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

    records, inferred_fields = normalize_records(data)
    fieldnames = fields if fields else inferred_fields
    if not fieldnames:
        raise ValueError("No fields found to write. Provide --fields or check your JSON structure.")

    logging.debug("Writing CSV: %s", output_csv)
    with open(output_csv, "w", newline="", encoding=encoding) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            writer.writerow(row)

    logging.info("CSV created: %s (rows: %d, columns: %d)", output_csv, len(records), len(fieldnames))
    return output_csv

def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert JSON to CSV with schema auto-detection.")
    p.add_argument("input_json", help="Path to input JSON file.")
    p.add_argument("--output", "-o", help="Output CSV path. Defaults to <input>.csv")
    p.add_argument("--fields", help="Comma-separated list of fields to write (order enforced).")
    p.add_argument("--encoding", default="utf-8", help="Text encoding (default: utf-8).")
    p.add_argument("--delimiter", default=",", help="CSV delimiter (default: ,)")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging.")
    return p.parse_args(argv)

def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    try:
        fields = args.fields.split(",") if args.fields else None
        out = json_to_csv(
            json_file=args.input_json,
            output_csv=args.output,
            fields=fields,
            encoding=args.encoding,
            delimiter=args.delimiter,
        )
        print(out)
        return 0
    except (FileNotFoundError, PermissionError) as e:
        logging.error("%s", e)
        return 1
    except (TypeError, ValueError) as e:
        logging.error("%s", e)
        return 2
    except Exception as e:
        logging.exception("Unexpected error: %s", e)
        return 99

if __name__ == "__main__":
    raise SystemExit(main())
