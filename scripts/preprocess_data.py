import logging
import os
import sys
from pathlib import Path

import pandas as pd
import yaml

# Add project root to python path so we can import from src
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.data_models import (
    GP_COLUMNS,
    SITE_COLUMNS,
    WEEKLY_COLUMNS,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("preprocess")

def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def load_config(config_dir: Path) -> tuple:
    thresholds = _load_yaml(config_dir / "thresholds.yaml")
    column_mapping = _load_yaml(config_dir / "column_mapping.yaml")
    return thresholds, column_mapping

def _transform_site_level(raw_df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    df = raw_df.copy()
    df = df.rename(columns=col_map)
    count_cols = [c for c in SITE_COLUMNS if c != "site_name"]
    for col in count_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    geo_cols = {"postcode", "latitude", "longitude"}
    missing = [c for c in SITE_COLUMNS if c not in df.columns and c not in geo_cols]
    if missing:
        raise ValueError(f"Missing columns in site_level: {missing}")
    for col in geo_cols:
        if col not in df.columns:
            df[col] = None
    df["site_name"] = df["site_name"].str.strip()
    return df[SITE_COLUMNS].reset_index(drop=True)

def _transform_user_level(raw_df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    df = raw_df.copy()
    df = df.rename(columns=col_map)
    df["gp_id"] = pd.to_numeric(df["gp_id"], errors="coerce").fillna(0).astype(int)
    df["gp_label"] = df["gp_id"].apply(lambda x: f"GP-{x:03d}")
    count_cols = [c for c in GP_COLUMNS if c not in ("gp_id", "gp_label", "site_name")]
    for col in count_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["site_name"] = df["site_name"].str.strip()
    missing = [c for c in GP_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in user_level: {missing}")
    return df[GP_COLUMNS].reset_index(drop=True)

def _transform_site_weekly(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df["site_name"] = df["site_name"].str.strip()
    date_cols = [c for c in df.columns if c != "site_name"]
    long_df = df.melt(
        id_vars=["site_name"],
        value_vars=date_cols,
        var_name="week_start",
        value_name="weekly_recordings",
    )
    long_df["week_start"] = pd.to_datetime(long_df["week_start"], errors="coerce")
    long_df = long_df.dropna(subset=["week_start"])
    # Convert to Int64 to allow NaN but treat as nullable integers
    long_df["weekly_recordings"] = pd.to_numeric(long_df["weekly_recordings"], errors="coerce").astype("Int64")
    long_df = long_df.sort_values(["site_name", "week_start"]).reset_index(drop=True)

    # Calcular suma acumulada por práctica, ignorando NaN
    long_df["cumulative_recordings"] = (
        long_df
        .groupby("site_name")["weekly_recordings"]
        .transform(lambda s: s.fillna(0).cumsum())
        .astype("Int64")
    )

    return long_df[WEEKLY_COLUMNS]

def main():
    data_dir = project_root / "data"
    config_dir = project_root / "config"
    excel_path = data_dir / "tricorder_enrollment_20260503 anonymised with identifier codes.xlsx"
    processed_dir = data_dir / "processed"
    
    logger.info(f"Starting preprocessing of {excel_path}...")
    
    if not excel_path.exists():
        logger.error(f"Could not find Excel file at {excel_path}")
        sys.exit(1)
        
    processed_dir.mkdir(parents=True, exist_ok=True)
    _, column_mapping = load_config(config_dir)
    
    xl = pd.ExcelFile(excel_path)
    logger.info("Transforming site_level...")
    site_df = _transform_site_level(xl.parse("site_level"), column_mapping["site_level"])
    
    logger.info("Transforming user_level...")
    gp_df = _transform_user_level(xl.parse("user_level", header=1), column_mapping["user_level"])
    
    logger.info("Transforming site_weekly...")
    weekly_df = _transform_site_weekly(xl.parse("site_weekly"))
    
    # Merge coords
    coords_path = data_dir / "practice_coordinates.csv"
    if coords_path.exists():
        logger.info("Merging practice_coordinates.csv...")
        coords_df = pd.read_csv(coords_path)
        site_df = site_df.drop(columns=["postcode", "latitude", "longitude"], errors="ignore")
        site_df = pd.merge(site_df, coords_df, on="site_name", how="left")
    
    site_df = site_df[SITE_COLUMNS]
    
    # Write to CSV
    logger.info("Writing site_data.csv...")
    site_df.to_csv(processed_dir / "site_data.csv", index=False)
    
    logger.info("Writing gp_data.csv...")
    gp_df.to_csv(processed_dir / "gp_data.csv", index=False)
    
    logger.info("Writing weekly_data.csv...")
    weekly_df.to_csv(processed_dir / "weekly_data.csv", index=False)
    
    logger.info("Preprocessing complete! CSVs are saved in data/processed/")

if __name__ == "__main__":
    main()
