"""
IDX Exchange - Week 1 Deliverable
Combine monthly CRMLS Listing and Sold files (Jan 2024 -> most recently
completed calendar month), filter to PropertyType == 'Residential', and save
the results as new CSVs.

Output:
    output/CRMLSListing_combined_residential.csv
    output/CRMLSSold_combined_residential.csv

Row-count confirmation (run 2026-10-04; files available 202401 -> 202604,
28 months each - 202605..202609 not yet downloaded):

    LISTINGS
      Sum of 28 monthly files (before concat):  860,898
      After concat:                             860,898   (matches)
      Before Residential filter:                860,898
      After Residential filter:                 547,162

    SOLD
      Sum of 28 monthly files (before concat):  615,707
      After concat:                             615,707   (matches)
      Before Residential filter:                615,707
      After Residential filter:                 414,054

    Note: CRMLSListing202601.csv has only 2,606 rows (vs ~20-40k in other
    months) and looks like an incomplete export.
"""

import re
from datetime import date
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
# Folders searched for monthly files, in priority order.
DATA_DIRS = [BASE_DIR / "csv", BASE_DIR]
OUTPUT_DIR = BASE_DIR / "output"

START_YEAR, START_MONTH = 2024, 1


def last_completed_month(today=None):
    """Return (year, month) of the most recently completed calendar month."""
    today = today or date.today()
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def month_range(start, end):
    """Yield 'YYYYMM' strings from start to end inclusive."""
    y, m = start
    while (y, m) <= end:
        yield f"{y}{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def find_file(prefix, yyyymm):
    """Locate a monthly file. Prefer the plain export, fall back to *_filled."""
    for name in (f"{prefix}{yyyymm}.csv", f"{prefix}{yyyymm}_filled.csv"):
        for d in DATA_DIRS:
            path = d / name
            if path.exists():
                return path
    return None


def drop_duplicate_columns(df):
    """Some early exports repeat column names (e.g. PropertyType twice).
    pandas renames repeats to 'Col.1'; drop those and keep the first copy."""
    dupes = [
        c for c in df.columns
        if re.search(r"\.\d+$", c) and re.sub(r"\.\d+$", "", c) in df.columns
    ]
    return df.drop(columns=dupes)


def combine(prefix, months):
    """Read every monthly file for `prefix`, print per-file row counts, concat."""
    frames, total_rows, missing = [], 0, []
    print(f"\n=== {prefix} ===")
    for yyyymm in months:
        path = find_file(prefix, yyyymm)
        if path is None:
            missing.append(yyyymm)
            continue
        df = pd.read_csv(path, low_memory=False)
        df = drop_duplicate_columns(df)
        df["SourceMonth"] = yyyymm  # keeps the time-series origin of each row
        frames.append(df)
        total_rows += len(df)
        print(f"  {path.relative_to(BASE_DIR)}: {len(df):,} rows")

    if missing:
        print(f"  WARNING - no file found for: {', '.join(missing)}")

    combined = pd.concat(frames, ignore_index=True)
    print(f"  Files loaded: {len(frames)}")
    print(f"  Sum of rows before concat: {total_rows:,}")
    print(f"  Rows after concat:         {len(combined):,}")
    assert len(combined) == total_rows, "Row count changed during concat!"
    return combined


def filter_residential(df, label):
    before = len(df)
    out = df[df["PropertyType"] == "Residential"].copy()
    print(f"  [{label}] before Residential filter: {before:,}")
    print(f"  [{label}] after Residential filter:  {len(out):,}")
    return out


def main():
    end = last_completed_month()
    months = list(month_range((START_YEAR, START_MONTH), end))
    print(f"Target range: {months[0]} -> {months[-1]} ({len(months)} months)")

    listings = combine("CRMLSListing", months)
    listings = filter_residential(listings, "Listings")

    sold = combine("CRMLSSold", months)
    sold = filter_residential(sold, "Sold")

    OUTPUT_DIR.mkdir(exist_ok=True)
    listings.to_csv(OUTPUT_DIR / "CRMLSListing_combined_residential.csv", index=False)
    sold.to_csv(OUTPUT_DIR / "CRMLSSold_combined_residential.csv", index=False)
    print(f"\nSaved combined files to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
