"""
IDX Exchange - Mortgage Rate Enrichment
Adds the national 30-year fixed mortgage rate (FRED series MORTGAGE30US) to the
filtered sold and listings datasets, joined on calendar month.

FRED publishes this rate weekly, so each month gets the average of its weekly
rates. Sold rows are keyed on CloseDate and listing rows on ListingContractDate,
the same dates the monthly MLS files are split on.

Input:  output/CRMLSSold_filtered.csv, output/CRMLSListing_filtered.csv (from week2_eda.py)
Output: output/CRMLSSold_enriched.csv, output/CRMLSListing_enriched.csv

Results (run 2026-10-11; full output in mortgage_output.txt): all 414,054 sold
and 547,162 listing rows matched a monthly rate, and the merge left both row
counts unchanged. Rates ranged from 6.05% (Feb 2026) to 7.06% (May 2024).
"""

import pandas as pd

from week1_combine_mls import OUTPUT_DIR

# FRED's public CSV download - no API key needed
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"


def monthly_mortgage_rates():
    weekly = pd.read_csv(FRED_URL, parse_dates=[0], index_col=0, na_values=".")
    monthly = weekly["MORTGAGE30US"].groupby(weekly.index.to_period("M")).mean()
    return monthly.rename("Mortgage30Rate").rename_axis("YearMonth").reset_index()


def main():
    rates = monthly_mortgage_rates()
    print("Monthly average 30-year fixed rate (%):")
    print(rates[rates["YearMonth"] >= pd.Period("2024-01", "M")].to_string(index=False))

    for prefix, date_col in [("CRMLSSold", "CloseDate"), ("CRMLSListing", "ListingContractDate")]:
        df = pd.read_csv(OUTPUT_DIR / f"{prefix}_filtered.csv", low_memory=False)
        df["YearMonth"] = pd.to_datetime(df[date_col], errors="coerce").dt.to_period("M")

        # Left join: every MLS row keeps its place; m:1 fails loudly if a month repeats in rates
        enriched = df.merge(rates, on="YearMonth", how="left", validate="m:1")

        print(f"\n{prefix}: {len(df):,} rows before merge, {len(enriched):,} after, "
              f"{enriched['Mortgage30Rate'].isna().sum():,} without a rate")
        enriched.to_csv(OUTPUT_DIR / f"{prefix}_enriched.csv", index=False)
        print(f"Saved output/{prefix}_enriched.csv")


if __name__ == "__main__":
    main()
