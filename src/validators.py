"""
validators.py
-------------
Data quality validations according to Section 14.3.

Generates a structured validation report displayed
in the Data Quality tab and downloadable as CSV.
"""

import logging
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


def validate_data(
    site_df: pd.DataFrame,
    gp_df: pd.DataFrame,
    weekly_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Executes all validations and returns a structured report."""
    report: Dict[str, Any] = {}

    # 1. General counts
    report["total_practices"] = len(site_df)
    report["total_gp_records"] = len(gp_df)
    report["unique_gp_ids"] = gp_df["gp_id"].nunique()

    # 2. Duplicate GP IDs
    dup_gps = gp_df[gp_df.duplicated(subset=["gp_id"], keep=False)]
    report["duplicate_gp_ids"] = len(dup_gps["gp_id"].unique())
    report["duplicate_gp_details"] = (
        dup_gps[["gp_id", "gp_label", "site_name"]].to_dict("records")
        if not dup_gps.empty
        else []
    )

    # 3. Missing practice names
    report["missing_practice_names"] = int(
        site_df["site_name"].isna().sum()
        + (site_df["site_name"].str.strip() == "").sum()
    )

    # 4. GPs with unmatched practices
    site_names = set(site_df["site_name"].unique())
    gp_unmatched = gp_df[~gp_df["site_name"].isin(site_names)]
    report["unmatched_gp_practices"] = len(gp_unmatched)
    report["unmatched_gp_details"] = (
        gp_unmatched[["gp_label", "site_name"]].to_dict("records")
        if not gp_unmatched.empty
        else []
    )

    # 5. Practices without linked GPs
    gp_sites = set(gp_df["site_name"].unique())
    sites_without_gps = site_df[~site_df["site_name"].isin(gp_sites)]
    report["practices_without_gps"] = len(sites_without_gps)

    # 6. Missing postcodes (placeholder - no geo data yet)
    report["missing_postcodes"] = "N/A — geographic data not yet supplied"
    report["invalid_postcodes"] = "N/A — geographic data not yet supplied"
    report["missing_coordinates"] = "N/A — geographic data not yet supplied"

    # 7. Negative values in counts
    count_cols = [
        c for c in site_df.columns
        if c.endswith("_count") or c == "rec_count"
    ]
    negative_site = 0
    for col in count_cols:
        if col in site_df.columns:
            negative_site += int((site_df[col] < 0).sum())

    count_cols_gp = [
        c for c in gp_df.columns
        if c.endswith("_count") or c == "rec_count"
    ]
    negative_gp = 0
    for col in count_cols_gp:
        if col in gp_df.columns:
            negative_gp += int((gp_df[col] < 0).sum())

    report["negative_values_site"] = negative_site
    report["negative_values_gp"] = negative_gp

    # 8. Reconciliation of practice vs GP totals
    site_total = site_df["rec_count"].sum()
    gp_total = gp_df["rec_count"].sum()
    report["site_level_total_recordings"] = int(site_total)
    report["gp_level_total_recordings"] = int(gp_total)
    report["reconciliation_difference"] = int(site_total - gp_total)

    # Reconciliation by practice
    gp_by_practice = gp_df.groupby("site_name")["rec_count"].sum().reset_index()
    gp_by_practice.columns = ["site_name", "gp_sum"]
    recon = site_df[["site_name", "rec_count"]].merge(
        gp_by_practice, on="site_name", how="left"
    )
    recon["diff"] = recon["rec_count"] - recon["gp_sum"].fillna(0)
    mismatched = recon[recon["diff"] != 0]
    report["practices_with_reconciliation_diff"] = len(mismatched)
    report["reconciliation_details"] = (
        mismatched[["site_name", "rec_count", "gp_sum", "diff"]].to_dict("records")
        if not mismatched.empty
        else []
    )

    logger.info(
        "Validation completed: %d practices, %d GPs, %d dups, reconciliation diff=%d",
        report["total_practices"],
        report["total_gp_records"],
        report["duplicate_gp_ids"],
        report["reconciliation_difference"],
    )

    return report


def validation_report_to_df(report: Dict[str, Any]) -> pd.DataFrame:
    """Converts the validation report into a DataFrame for display/download."""
    rows: List[Dict[str, str]] = [
        {"Check": "Total practices", "Result": str(report["total_practices"])},
        {"Check": "Total GP records", "Result": str(report["total_gp_records"])},
        {"Check": "Unique GP identifiers", "Result": str(report["unique_gp_ids"])},
        {"Check": "Duplicate GP identifiers", "Result": str(report["duplicate_gp_ids"])},
        {"Check": "Missing practice names", "Result": str(report["missing_practice_names"])},
        {"Check": "GPs with unmatched practices", "Result": str(report["unmatched_gp_practices"])},
        {"Check": "Practices without linked GPs", "Result": str(report["practices_without_gps"])},
        {"Check": "Missing postcodes", "Result": str(report["missing_postcodes"])},
        {"Check": "Invalid postcodes", "Result": str(report["invalid_postcodes"])},
        {"Check": "Missing coordinates", "Result": str(report["missing_coordinates"])},
        {"Check": "Negative values (site level)", "Result": str(report["negative_values_site"])},
        {"Check": "Negative values (GP level)", "Result": str(report["negative_values_gp"])},
        {
            "Check": "Practice vs GP total reconciliation",
            "Result": str(report["reconciliation_difference"]),
        },
        {
            "Check": "Practices with per-practice reconciliation difference",
            "Result": str(report["practices_with_reconciliation_diff"]),
        },
    ]
    return pd.DataFrame(rows)
