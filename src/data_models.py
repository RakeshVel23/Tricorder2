"""
data_models.py
--------------
Estructuras de datos tipadas para las tres tablas principales del dashboard.
Centraliza los nombres de columna esperados después de la transformación.
"""

from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd


@dataclass
class DashboardData:
    """Contenedor inmutable con los DataFrames procesados y métricas derivadas."""

    # --- Tablas principales ---
    site_df: pd.DataFrame          # Una fila por práctica (96 filas)
    gp_df: pd.DataFrame            # Una fila por GP (1003 filas)
    weekly_df: pd.DataFrame        # Formato largo: (site_name, week_start, weekly_recordings)

    # --- Métricas derivadas (adjuntadas a los DataFrames) ---
    # Se calculan en metrics.py y se añaden como columnas extra

    # --- Metadatos ---
    data_refresh_date: str = ""    # Fecha de la última carga
    total_practices: int = 0
    total_gps: int = 0
    week_range: tuple = ()         # (primera semana, última semana)

    # --- Validación ---
    validation_report: Dict = field(default_factory=dict)


# Columnas esperadas después de la transformación
SITE_COLUMNS = [
    "site_name",
    "patient_count",
    "rec_count",
    "poor_pcg_count",
    "poor_ecg_count",
    "murmur_flag_count",
    "low_ef_flag_count",
    "af_flag_count",
    "assigned_rec_count",
    "assigned_poor_pcg_count",
    "assigned_poor_ecg_count",
    "assigned_murmur_flag_count",
    "assigned_low_ef_flag_count",
    "assigned_af_flag_count",
    "postcode",
    "latitude",
    "longitude",
]

GP_COLUMNS = [
    "gp_id",
    "gp_label",          # Formato GP-001, GP-002, etc.
    "site_name",
    "patient_count",
    "rec_count",
    "poor_pcg_count",
    "poor_ecg_count",
    "murmur_flag_count",
    "low_ef_flag_count",
    "af_flag_count",
    "assigned_rec_count",
    "assigned_poor_pcg_count",
    "assigned_poor_ecg_count",
    "assigned_murmur_flag_count",
    "assigned_low_ef_flag_count",
    "assigned_af_flag_count",
]

WEEKLY_COLUMNS = [
    "site_name",
    "week_start",
    "weekly_recordings",
    "cumulative_recordings",
]
