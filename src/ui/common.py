"""
common.py
---------
Reusable UI components: KPI cards, filter panels,
download buttons and warning banners.
"""

from typing import Optional

from htmltools import Tag, TagList, tags
from shiny import ui


# ---------------------------------------------------------------
# Summary Table
# ---------------------------------------------------------------

def summary_table(rows: list[tuple[str, str, str]], table_id: str = "") -> Tag:
    """Renders a GA4 style table for summary statistics.
    rows: list of tuples (Metric Name, Value, Description)
    """
    tr_tags = [
        tags.tr(
            tags.td(tags.strong(name)),
            tags.td(value),
            tags.td(tags.span(desc, class_="text-muted", style="font-size: 12px; color: var(--color-text-secondary);")),
        )
        for name, value, desc in rows
    ]
    
    return tags.div(
        tags.table(
            tags.thead(
                tags.tr(
                    tags.th("Metric"),
                    tags.th("Value"),
                    tags.th("Description"),
                )
            ),
            tags.tbody(*tr_tags),
            class_="data-table",
        ),
        id=table_id,
        style="overflow-x: auto;"
    )


# ---------------------------------------------------------------
# Panel / section
# ---------------------------------------------------------------

def panel_card(title: str, *children: Tag, panel_id: str = "") -> Tag:
    """Section container with title and border."""
    return tags.div(
        tags.h3(title),
        *children,
        class_="panel-card",
        id=panel_id,
    )


# ---------------------------------------------------------------
# Dependency badge
# ---------------------------------------------------------------

def dependency_badge(category: str) -> Tag:
    """Badge coloreado para categoría de dependencia de champion."""
    css_map = {
        "Low dependency": "badge badge-low",
        "Moderate dependency": "badge badge-moderate",
        "High dependency": "badge badge-high",
    }
    css_class = css_map.get(category, "badge")
    return tags.span(category, class_=css_class)


# ---------------------------------------------------------------
# Banners de advertencia
# ---------------------------------------------------------------

def warning_banner(message: str) -> Tag:
    """Banner de advertencia (naranja)."""
    return tags.div(
        f"⚠ {message}",
        class_="warning-banner",
    )


def info_banner(message: str) -> Tag:
    """Banner informativo (azul)."""
    return tags.div(
        f"ℹ {message}",
        class_="info-banner",
    )


# ---------------------------------------------------------------
# Botón de descarga con estilo
# ---------------------------------------------------------------

def download_button_styled(
    output_id: str,
    label: str = "Download CSV",
) -> Tag:
    """Botón de descarga estilizado."""
    return ui.download_button(
        output_id,
        label,
        class_="btn btn-outline-secondary btn-sm",
    )
