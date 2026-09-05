#!/usr/bin/env python3
"""
Stage 2 — Ingestion & Parsing
------------------------------
Reads bulk Bitcoin transaction/network metadata from CSV, JSON, or XML,
normalizes it into one canonical schema, validates it, and writes a
cleaned dataset ready for graph construction (Stage 3).

Usage:
    python3 parser.py <input_file> [--out cleaned_transactions.csv]

Examples:
    python3 parser.py ../dataset/transactions.csv
    python3 parser.py ../dataset/transactions.json --out cleaned.csv

Canonical schema produced (one row per transaction):
    timestamp        - pandas Timestamp
    src_ip, dst_ip    - str
    src_port, dst_port - int
    txid              - str
    input_addresses   - list[str]
    output_addresses  - list[str]
    input_amounts     - list[float]
    output_amounts    - list[float]
    fee               - float
    script_type       - str
    geo_country       - str
    asn               - int
    total_in          - float  (derived)
    total_out         - float  (derived)
    n_inputs          - int    (derived)
    n_outputs         - int    (derived)
"""

import argparse
import ipaddress
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

REQUIRED_FIELDS = [
    "timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "txid",
    "input_addresses", "output_addresses", "input_amounts", "output_amounts",
    "fee", "script_type", "geo_country", "asn",
]


# ----------------------------
# LOADERS — one per format
# ----------------------------
def load_csv(path):
    """CSV stores list fields as pipe-separated strings; split them back into lists."""
    df = pd.read_csv(path, dtype={"src_port": "Int64", "dst_port": "Int64", "asn": "Int64"})

    def split_list(cell, cast=str):
        if pd.isna(cell) or cell == "":
            return []
        return [cast(x) for x in str(cell).split("|")]

    df["input_addresses"] = df["input_addresses"].apply(lambda c: split_list(c, str))
    df["output_addresses"] = df["output_addresses"].apply(lambda c: split_list(c, str))
    df["input_amounts"] = df["input_amounts"].apply(lambda c: split_list(c, float))
    df["output_amounts"] = df["output_amounts"].apply(lambda c: split_list(c, float))
    return df


def load_json(path):
    with open(path) as f:
        data = json.load(f)
    return pd.DataFrame(data)


def load_xml(path):
    """
    Expects a structure like:
    <transactions>
      <transaction>
        <timestamp>...</timestamp>
        <src_ip>...</src_ip>
        ...
        <input_addresses><address>...</address><address>...</address></input_addresses>
        <input_amounts><amount>...</amount><amount>...</amount></input_amounts>
        ...
      </transaction>
    </transactions>
    """
    tree = ET.parse(path)
    root = tree.getroot()
    rows = []
    for tx_el in root.findall("transaction"):
        row = {}
        for field in REQUIRED_FIELDS:
            el = tx_el.find(field)
            if el is None:
                row[field] = None
                continue
            if field in ("input_addresses", "output_addresses"):
                row[field] = [child.text for child in el.findall("address")]
            elif field in ("input_amounts", "output_amounts"):
                row[field] = [float(child.text) for child in el.findall("amount")]
            else:
                row[field] = el.text
        rows.append(row)
    return pd.DataFrame(rows)


LOADERS = {".csv": load_csv, ".json": load_json, ".xml": load_xml}


# ----------------------------
# VALIDATION
# ----------------------------
def is_valid_ip(value):
    try:
        ipaddress.ip_address(str(value))
        return True
    except ValueError:
        return False


def validate(df):
    """Runs a set of sanity checks and returns (clean_df, issues_report)."""
    issues = {}
    n_before = len(df)

    # 1. Required columns present
    missing_cols = [c for c in REQUIRED_FIELDS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    # 2. Drop rows with missing critical fields
    critical = ["txid", "timestamp", "src_ip", "dst_ip"]
    na_mask = df[critical].isna().any(axis=1)
    issues["dropped_missing_critical_fields"] = int(na_mask.sum())
    df = df[~na_mask].copy()

    # 3. Drop duplicate TXIDs (keep first occurrence)
    dup_mask = df.duplicated(subset="txid", keep="first")
    issues["dropped_duplicate_txids"] = int(dup_mask.sum())
    df = df[~dup_mask].copy()

    # 4. Validate IP format
    bad_ip_mask = ~(df["src_ip"].apply(is_valid_ip) & df["dst_ip"].apply(is_valid_ip))
    issues["dropped_invalid_ip"] = int(bad_ip_mask.sum())
    df = df[~bad_ip_mask].copy()

    # 4b. Malformed lists: input_amounts/input_addresses length mismatch (or vice versa
    # for outputs) means the row's structure itself is corrupt -- can't safely map
    # amounts to addresses, so it's dropped rather than guessed at.
    def lists_mismatched(row):
        return len(row["input_addresses"]) != len(row["input_amounts"]) or \
               len(row["output_addresses"]) != len(row["output_amounts"])

    malformed_mask = df.apply(lists_mismatched, axis=1)
    issues["dropped_malformed_lists"] = int(malformed_mask.sum())
    df = df[~malformed_mask].copy()

    # 5. Parse timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    bad_ts_mask = df["timestamp"].isna()
    issues["dropped_bad_timestamp"] = int(bad_ts_mask.sum())
    df = df[~bad_ts_mask].copy()

    # 6. Amounts must be non-negative lists
    def all_nonneg(lst):
        return all(a >= 0 for a in lst) if isinstance(lst, list) else False

    bad_amt_mask = ~(df["input_amounts"].apply(all_nonneg) & df["output_amounts"].apply(all_nonneg))
    issues["dropped_invalid_or_negative_amounts"] = int(bad_amt_mask.sum())
    df = df[~bad_amt_mask].copy()

    # 7. Derived fields
    df["total_in"] = df["input_amounts"].apply(sum)
    df["total_out"] = df["output_amounts"].apply(sum)
    df["n_inputs"] = df["input_addresses"].apply(len)
    df["n_outputs"] = df["output_addresses"].apply(len)

    # 8. Fee sanity (flag, don't drop): fee must be non-negative and numeric
    df["fee"] = pd.to_numeric(df["fee"], errors="coerce")
    invalid_fee_mask = df["fee"].isna() | (df["fee"] < 0)
    issues["flagged_invalid_fee"] = int(invalid_fee_mask.sum())
    df["fee"] = df["fee"].fillna(0.0).clip(lower=0.0)

    # 9. Flag (but don't drop) transactions where balance looks off:
    #    inputs should roughly equal outputs + fee. Flag if off by > 1%.
    expected_out = df["total_out"] + df["fee"]
    df["balance_mismatch"] = (df["total_in"] - expected_out).abs() > (0.01 * df["total_in"].clip(lower=1e-8))
    issues["flagged_balance_mismatch"] = int(df["balance_mismatch"].sum())

    # 10. Port sanity (flag, don't drop — could be legitimate non-standard ports)
    df["src_port"] = pd.to_numeric(df["src_port"], errors="coerce")
    df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce")
    df["port_out_of_range"] = ~df["src_port"].between(1, 65535) | ~df["dst_port"].between(1, 65535)
    issues["flagged_invalid_ports"] = int(df["port_out_of_range"].sum())

    # 11. ASN sanity (flag, don't drop): valid ASN range is 1 to 4294967295
    df["asn"] = pd.to_numeric(df["asn"], errors="coerce")
    invalid_asn_mask = df["asn"].isna() | ~df["asn"].between(1, 4294967295)
    issues["flagged_invalid_asn"] = int(invalid_asn_mask.sum())

    issues["rows_in"] = n_before
    issues["rows_out"] = len(df)
    issues["rows_dropped_total"] = n_before - len(df)

    return df.reset_index(drop=True), issues


# ----------------------------
# MAIN
# ----------------------------
def load_transactions(path):
    """Single entry point: detects format from extension and returns a raw DataFrame."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in LOADERS:
        raise ValueError(f"Unsupported file format '{ext}'. Supported: {list(LOADERS)}")
    return LOADERS[ext](path)


def main():
    parser = argparse.ArgumentParser(description="Ingest and validate Bitcoin transaction metadata.")
    parser.add_argument("input_file", help="Path to input .csv, .json, or .xml file")
    parser.add_argument("--out", default="cleaned_transactions.csv", help="Output cleaned CSV path")
    args = parser.parse_args()

    print(f"Loading: {args.input_file}")
    df = load_transactions(args.input_file)
    print(f"  Raw rows loaded: {len(df)}")

    print("Validating & cleaning...")
    clean_df, issues = validate(df)

    print("\n=== Validation Report ===")
    for k, v in issues.items():
        print(f"  {k}: {v}")

    # Save cleaned output (flatten list columns back to pipe-separated strings for CSV)
    out_df = clean_df.copy()
    for col in ["input_addresses", "output_addresses"]:
        out_df[col] = out_df[col].apply(lambda x: "|".join(x))
    for col in ["input_amounts", "output_amounts"]:
        out_df[col] = out_df[col].apply(lambda x: "|".join(str(v) for v in x))

    out_df.to_csv(args.out, index=False)
    print(f"\nCleaned dataset written to: {args.out}")
    print(f"Final row count: {len(clean_df)}")


if __name__ == "__main__":
    main()
