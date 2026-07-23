"""
metrics.py
----------
Calculation of derived metrics for GPs, practices, and weekly series.

Responsible for calculating rates, scores, percentiles, and rankings
based on the raw counts from the data loading layer.
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------
# GP level metrics (Section 8.4)
# ---------------------------------------------------------------

def compute_gp_metrics(gp_df: pd.DataFrame) -> pd.DataFrame:
    """Calculates derived metrics for each GP."""
    df = gp_df.copy()

    # --- Active status ---
    df["is_active"] = df["rec_count"] > 0

    # --- Recordings per tagged patient ---
    df["recordings_per_patient"] = np.where(
        df["patient_count"] > 0,
        df["rec_count"] / df["patient_count"],
        np.nan,  # "Not calculable" - formatted in UI
    )

    # --- Assignment rate ---
    df["assignment_rate"] = np.where(
        df["rec_count"] > 0,
        (df["assigned_rec_count"] / df["rec_count"]) * 100,
        0.0,
    )

    # --- Recording quality rates ---
    df["poor_pcg_rate"] = np.where(
        df["rec_count"] > 0,
        (df["poor_pcg_count"] / df["rec_count"]) * 100,
        0.0,
    )
    df["poor_ecg_rate"] = np.where(
        df["rec_count"] > 0,
        (df["poor_ecg_count"] / df["rec_count"]) * 100,
        0.0,
    )

    # --- Diagnostic flag rates ---
    df["murmur_flag_rate"] = np.where(
        df["rec_count"] > 0,
        (df["murmur_flag_count"] / df["rec_count"]) * 100,
        0.0,
    )
    df["low_ef_flag_rate"] = np.where(
        df["rec_count"] > 0,
        (df["low_ef_flag_count"] / df["rec_count"]) * 100,
        0.0,
    )
    df["af_flag_rate"] = np.where(
        df["rec_count"] > 0,
        (df["af_flag_count"] / df["rec_count"]) * 100,
        0.0,
    )

    return df


def compute_gp_rankings(gp_df: pd.DataFrame) -> pd.DataFrame:
    """Calculates rankings and percentiles for each GP.

    Generates rankings among all GPs, only active ones, and within
    each practice. Default percentile is among active ones.
    """
    df = gp_df.copy()

    # Global ranking (all)
    df["rank_all"] = df["rec_count"].rank(ascending=False, method="min").astype(int)

    # Ranking only among active GPs
    active_mask = df["is_active"]
    df["rank_active"] = np.nan
    if active_mask.any():
        df.loc[active_mask, "rank_active"] = (
            df.loc[active_mask, "rec_count"]
            .rank(ascending=False, method="min")
            .astype(int)
        )

    # Ranking within the practice
    df["rank_in_practice"] = (
        df.groupby("site_name")["rec_count"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    # National percentile (among active)
    total_active = active_mask.sum()
    if total_active > 0:
        df["national_percentile"] = np.where(
            active_mask,
            ((total_active - df["rank_active"]) / total_active * 100).round(1),
            np.nan,
        )
    else:
        df["national_percentile"] = np.nan

    # Percentage contribution to the practice
    practice_totals = (
        df.groupby("site_name")["rec_count"]
        .transform("sum")
    )
    df["contribution_pct"] = np.where(
        practice_totals > 0,
        (df["rec_count"] / practice_totals) * 100,
        0.0,
    )

    return df


# ---------------------------------------------------------------
# Practice level metrics (Section 7.4)
# ---------------------------------------------------------------

def compute_practice_metrics(
    site_df: pd.DataFrame,
    gp_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculates derived metrics for each practice.

    Uses the sum of GP-level recordings as the denominator for the
    champion-dependency score (denominator decision, Section 7.4).
    """
    df = site_df.copy()

    # --- GP Counts ---
    gp_counts = gp_df.groupby("site_name").agg(
        registered_gp_count=("gp_id", "count"),
        active_gp_count=("is_active", "sum"),
    ).reset_index()

    df = df.merge(gp_counts, on="site_name", how="left")
    df["registered_gp_count"] = df["registered_gp_count"].fillna(0).astype(int)
    df["active_gp_count"] = df["active_gp_count"].fillna(0).astype(int)

    # --- Active GP rate ---
    df["active_gp_rate"] = np.where(
        df["registered_gp_count"] > 0,
        (df["active_gp_count"] / df["registered_gp_count"]) * 100,
        0.0,
    )

    # --- Champion-dependency score ---
    # Denominator = sum of rec_count at GP level for that practice
    gp_practice_totals = (
        gp_df.groupby("site_name")["rec_count"].sum().reset_index()
    )
    gp_practice_totals.columns = ["site_name", "gp_level_total"]

    top_gp = (
        gp_df.groupby("site_name")["rec_count"].max().reset_index()
    )
    top_gp.columns = ["site_name", "top_gp_recordings"]

    # Top 3 GP contribution
    top3_gp = (
        gp_df.sort_values("rec_count", ascending=False)
        .groupby("site_name")
        .head(3)
        .groupby("site_name")["rec_count"]
        .sum()
        .reset_index()
    )
    top3_gp.columns = ["site_name", "top3_gp_recordings"]

    df = df.merge(gp_practice_totals, on="site_name", how="left")
    df = df.merge(top_gp, on="site_name", how="left")
    df = df.merge(top3_gp, on="site_name", how="left")

    df["champion_dependency_score"] = np.where(
        df["gp_level_total"] > 0,
        (df["top_gp_recordings"] / df["gp_level_total"]) * 100,
        0.0,
    )

    df["top3_dependency_score"] = np.where(
        df["gp_level_total"] > 0,
        (df["top3_gp_recordings"] / df["gp_level_total"]) * 100,
        0.0,
    )

    # --- Reconciliation difference ---
    df["reconciliation_diff"] = df["rec_count"] - df["gp_level_total"].fillna(0)

    # --- Active status of the practice ---
    df["is_active"] = df["rec_count"] > 0

    # --- Derived rates (same as GP) ---
    df["recordings_per_patient"] = np.where(
        df["patient_count"] > 0,
        df["rec_count"] / df["patient_count"],
        np.nan,
    )
    df["assignment_rate"] = np.where(
        df["rec_count"] > 0,
        (df["assigned_rec_count"] / df["rec_count"]) * 100,
        0.0,
    )
    df["poor_pcg_rate"] = np.where(
        df["rec_count"] > 0,
        (df["poor_pcg_count"] / df["rec_count"]) * 100,
        0.0,
    )
    df["poor_ecg_rate"] = np.where(
        df["rec_count"] > 0,
        (df["poor_ecg_count"] / df["rec_count"]) * 100,
        0.0,
    )
    df["murmur_flag_rate"] = np.where(
        df["rec_count"] > 0,
        (df["murmur_flag_count"] / df["rec_count"]) * 100,
        0.0,
    )
    df["low_ef_flag_rate"] = np.where(
        df["rec_count"] > 0,
        (df["low_ef_flag_count"] / df["rec_count"]) * 100,
        0.0,
    )
    df["af_flag_rate"] = np.where(
        df["rec_count"] > 0,
        (df["af_flag_count"] / df["rec_count"]) * 100,
        0.0,
    )

    return df


# ---------------------------------------------------------------
# Time series metrics (Section 9.8, 10.4)
# ---------------------------------------------------------------

def compute_weekly_metrics(weekly_df: pd.DataFrame) -> pd.DataFrame:
    """Adds moving average and cumulative to weekly data."""
    df = weekly_df.copy()
    df = df.sort_values(["site_name", "week_start"])

    # 4-week rolling average per practice
    df["rolling_avg_4w"] = (
        df.groupby("site_name")["weekly_recordings"]
        .transform(lambda x: x.rolling(window=4, min_periods=1).mean())
    )

    # Cumulative per practice
    df["cumulative_recordings"] = (
        df.groupby("site_name")["weekly_recordings"]
        .transform("cumsum")
    )

    return df


def compute_programme_weekly(weekly_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates weekly metrics at the whole programme level."""
    programme = (
        weekly_df.groupby("week_start")
        .agg(
            total_weekly=("weekly_recordings", "sum"),
            active_practices=("site_name", "nunique"),
        )
        .reset_index()
        .sort_values("week_start")
    )

    programme["rolling_avg_4w"] = (
        programme["total_weekly"].rolling(window=4, min_periods=1).mean()
    )
    programme["cumulative"] = programme["total_weekly"].cumsum()

    return programme
