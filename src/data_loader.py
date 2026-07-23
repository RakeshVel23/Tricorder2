"""
data_loader.py
--------------
Module for data ingestion and transformation.

1. Read Excel file.
2. Validate required sheets exist.
3. Pivot wide data to long format.
4. Clean and normalize identifiers.
5. Extract metadata.
6. Join geographic data if available.
7. Fill missing counts with 0.
8. Filter out empty records.
9. Verify numeric types.
10. Return typed DashboardData.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import yaml

from src.data_models import (
    GP_COLUMNS,
    SITE_COLUMNS,
    WEEKLY_COLUMNS,
    DashboardData,
)

import yaml

logger = logging.getLogger(__name__)

def _load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def load_config(config_dir: Path) -> tuple:
    thresholds = _load_yaml(config_dir / "thresholds.yaml")
    column_mapping = _load_yaml(config_dir / "column_mapping.yaml")
    return thresholds, column_mapping


def load_dashboard_data(
    excel_path: Path,
    config_dir: Path,
) -> DashboardData:
    """Entry point: loads preprocessed CSV data and returns DashboardData.
    
    If the processed CSVs do not exist, it raises an error instructing the user
    to run the preprocessing script.
    """
    data_dir = excel_path.parent
    processed_dir = data_dir / "processed"
    
    if not processed_dir.exists():
        raise FileNotFoundError(
            f"Processed data directory not found at {processed_dir}. "
            f"Please run 'python scripts/preprocess_data.py' to generate the CSV files."
        )

    logger.info("Loading preprocessed data from %s", processed_dir)

    try:
        # We need to coerce 'weekly_recordings' back to Int64 since CSV doesn't store nullable types cleanly
        site_df = pd.read_csv(processed_dir / "site_data.csv")
        gp_df = pd.read_csv(processed_dir / "gp_data.csv")
        
        # Load weekly data and parse dates
        weekly_df = pd.read_csv(processed_dir / "weekly_data.csv")
        weekly_df["week_start"] = pd.to_datetime(weekly_df["week_start"])
        weekly_df["weekly_recordings"] = pd.to_numeric(weekly_df["weekly_recordings"], errors="coerce").astype("Int64")
    except FileNotFoundError as e:
        logger.error("Missing processed CSV file: %s", e)
        raise FileNotFoundError(
            f"Missing processed CSV file: {e}. "
            f"Please run 'python scripts/preprocess_data.py'."
        )

    # --- Metadata ---
    week_min = weekly_df["week_start"].min()
    week_max = weekly_df["week_start"].max()

    data = DashboardData(
        site_df=site_df,
        gp_df=gp_df,
        weekly_df=weekly_df,
        data_refresh_date=datetime.now().strftime("%Y-%m-%d"),
        total_practices=len(site_df),
        total_gps=len(gp_df),
        week_range=(
            week_min.strftime("%Y-%m-%d") if pd.notna(week_min) else "",
            week_max.strftime("%Y-%m-%d") if pd.notna(week_max) else "",
        ),
    )

    logger.info(
        "Data loaded: %d practices, %d GPs, weekly range %s to %s",
        data.total_practices,
        data.total_gps,
        data.week_range[0],
        data.week_range[1],
    )

    return data
