"""
Phase 1: Exploratory Data Analysis (EDA) Script
Inspects, validates relational integrity, and prints summary distributions
for the MechanicDB dataset.
"""
import json
import pandas as pd
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

def inspect_datasets():
    print("=" * 70)
    print("STEP 1: MECHANICDB DATASET EXPLORATION & INTEGRITY CHECK")
    print("=" * 70)

    # 1. Load CSVs with pipe separator
    dtc_df = pd.read_csv(config.DTC_CODES_CSV, sep="|")
    fixes_df = pd.read_csv(config.DIAGNOSTIC_FIXES_CSV, sep="|")
    joined_df = pd.read_csv(config.DTC_FIXES_JOINED_CSV, sep="|")
    parts_df = pd.read_csv(config.REPLACEMENT_PARTS_CSV, sep="|")
    
    with open(config.COST_METADATA_JSON, "r", encoding="utf-8") as f:
        cost_meta = json.load(f)
    with open(config.ORDERING_METADATA_JSON, "r", encoding="utf-8") as f:
        ordering_meta = json.load(f)

    # 2. Basic Dimensions
    print("\n[1] DATASET DIMENSIONS")
    print(f"  * dtc_codes.csv:         {dtc_df.shape[0]} rows, {dtc_df.shape[1]} columns")
    print(f"  * diagnostic_fixes.csv:  {fixes_df.shape[0]} rows, {fixes_df.shape[1]} columns")
    print(f"  * dtc_fixes_joined.csv:  {joined_df.shape[0]} rows, {joined_df.shape[1]} columns")
    print(f"  * replacement_parts.csv: {parts_df.shape[0]} rows, {parts_df.shape[1]} columns")

    # 3. Missing Value Check
    print("\n[2] MISSING VALUES CHECK")
    for name, df in [("DTC Codes", dtc_df), ("Fixes", fixes_df), ("Parts", parts_df)]:
        null_counts = df.isnull().sum()
        cols_with_nulls = null_counts[null_counts > 0]
        if len(cols_with_nulls) > 0:
            print(f"  - {name} columns with nulls:")
            for col, count in cols_with_nulls.items():
                print(f"      • {col}: {count} missing ({count/len(df)*100:.1f}%)")
        else:
            print(f"  - {name}: No missing values.")

    # 4. Relational Integrity Checks
    print("\n[3] RELATIONAL INTEGRITY VERIFICATION")
    # Verify code_id links
    orphan_fixes = fixes_df[~fixes_df['code_id'].isin(dtc_df['code_id'])]
    print(f"  - Orphan fixes (fixes with no valid code_id): {len(orphan_fixes)}")
    
    # Verify parts links
    orphan_parts = parts_df[~parts_df['fix_id'].isin(fixes_df['fix_id'])]
    print(f"  - Orphan parts (parts with no valid fix_id): {len(orphan_parts)}")

    # Check DTC to Fix coverage
    codes_with_fixes = fixes_df['code_id'].unique()
    codes_without_fixes = dtc_df[~dtc_df['code_id'].isin(codes_with_fixes)]
    print(f"  - DTC codes with associated fixes: {len(codes_with_fixes)} / {len(dtc_df)}")
    if len(codes_without_fixes) > 0:
        print(f"    WARNING: {len(codes_without_fixes)} codes lack fix procedures!")

    # 5. Domain Category Distributions
    print("\n[4] SYSTEM CATEGORIES DISTRIBUTION (dtc_codes)")
    for cat, cnt in dtc_df['system_category'].value_counts().items():
        print(f"  - {cat:15}: {cnt:3d} codes ({cnt/len(dtc_df)*100:.1f}%)")

    print("\n[5] DIFFICULTY LEVELS (diagnostic_fixes)")
    for diff, cnt in fixes_df['difficulty_level'].value_counts().items():
        print(f"  - {diff:22}: {cnt:3d} procedures ({cnt/len(fixes_df)*100:.1f}%)")

    # 6. Cost & Labor Statistics
    print("\n[6] REPAIR COST & LABOR STATISTICS")
    print(f"  - Min Parts Cost ($):   mean=${fixes_df['est_parts_cost_min_usd'].mean():.2f}, median=${fixes_df['est_parts_cost_min_usd'].median():.2f}, max=${fixes_df['est_parts_cost_max_usd'].max():.2f}")
    print(f"  - Labor Hours:          mean={fixes_df['est_labor_hours'].mean():.2f} hrs, median={fixes_df['est_labor_hours'].median():.2f} hrs, max={fixes_df['est_labor_hours'].max():.2f} hrs")

    # 7. Metadata Meaning
    print("\n[7] CRITICAL METADATA SEMANTICS (ordering_metadata.json)")
    print(f"  - 'probability_rank' Meaning: {ordering_meta.get('order_meaning')}")
    print(f"  - Does NOT measure: {', '.join(ordering_meta.get('does_not_measure', []))}")

    print("\n" + "=" * 70)
    print("EDA CHECK COMPLETED SUCCESSFULLY.")
    print("=" * 70)

if __name__ == "__main__":
    inspect_datasets()
