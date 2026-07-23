"""
utils.py
--------
Funciones utilitarias para formato, descargas y componentes reutilizables.
"""

import io
from typing import Optional

import pandas as pd


def format_number(value: float, decimals: int = 0) -> str:
    """Formatea un número con separador de miles."""
    if pd.isna(value):
        return "—"
    if decimals == 0:
        return f"{int(value):,}"
    return f"{value:,.{decimals}f}"


def format_rate(value: float, decimals: int = 1) -> str:
    """Formatea un porcentaje con símbolo %."""
    if pd.isna(value):
        return "—"
    return f"{value:.{decimals}f}%"


def format_ratio(value: float, decimals: int = 1) -> str:
    """Formatea una razón (e.g. grabaciones por paciente)."""
    if pd.isna(value):
        return "Not calculable"
    return f"{value:.{decimals}f}"


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convierte un DataFrame a bytes CSV para descarga."""
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8")
    return buffer.getvalue()


def safe_divide(
    numerator: float,
    denominator: float,
    multiply: float = 1.0,
    default: Optional[float] = None,
) -> Optional[float]:
    """División segura que devuelve default si el denominador es 0."""
    if denominator == 0 or pd.isna(denominator):
        return default
    return (numerator / denominator) * multiply
