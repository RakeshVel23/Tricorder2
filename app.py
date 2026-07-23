"""
app.py
------
Main entry point for the Landmark Tricorder Dashboard.

Orchestrates authentication, data loading, metric calculation,
and rendering of the tabs.
"""

import logging
from pathlib import Path

from shiny import App, reactive, render, ui

from src.data_loader import load_config, load_dashboard_data
from src.metrics import (
    compute_gp_metrics,
    compute_gp_rankings,
    compute_practice_metrics,
    compute_programme_weekly,
    compute_weekly_metrics,
)
from src.validators import validate_data

from src.ui.tab_overview import overview_server, overview_ui
from src.ui.tab_practice import practice_server, practice_ui
from src.ui.tab_gp import gp_server, gp_ui
from src.ui.tab_map import map_server, map_ui
from src.ui.tab_dynamic_graph import dynamic_graph_server, dynamic_graph_ui

# ---------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Paths
# ---------------------------------------------------------------

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "tricorder_enrollment_20260503 anonymised with identifier codes.xlsx"
CONFIG_DIR = BASE_DIR / "config"

# ---------------------------------------------------------------
# Data loading on startup (one time)
# ---------------------------------------------------------------

logger.info("Starting data load...")

thresholds, _col_map = load_config(CONFIG_DIR)
dashboard_data = load_dashboard_data(DATA_PATH, CONFIG_DIR)

# Calculate derived metrics for GPs
dashboard_data.gp_df = compute_gp_metrics(dashboard_data.gp_df)
dashboard_data.gp_df = compute_gp_rankings(dashboard_data.gp_df)

# Calculate derived metrics for practices
dashboard_data.site_df = compute_practice_metrics(
    dashboard_data.site_df, dashboard_data.gp_df
)

# Enrich weekly data
dashboard_data.weekly_df = compute_weekly_metrics(dashboard_data.weekly_df)

# Programme level metrics
dashboard_data.programme_weekly = compute_programme_weekly(dashboard_data.weekly_df)

# Validation
dashboard_data.validation_report = validate_data(
    dashboard_data.site_df, dashboard_data.gp_df, dashboard_data.weekly_df
)

logger.info("Data processed successfully.")


# ---------------------------------------------------------------
# UI
# ---------------------------------------------------------------

app_ui = ui.page_fluid(
    ui.head_content(
        ui.include_css(BASE_DIR / "static" / "styles.css"),
        ui.tags.link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap",
        ),
        # Forzar tema claro de Bootstrap
        ui.tags.script(
            """
            (function() {
                var observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(m) {
                        if (m.attributeName === 'data-bs-theme') {
                            if (document.documentElement.getAttribute('data-bs-theme') !== 'light') {
                                document.documentElement.setAttribute('data-bs-theme', 'light');
                            }
                        }
                    });
                });
                observer.observe(document.documentElement, { attributes: true });
                document.documentElement.setAttribute('data-bs-theme', 'light');
            })();
            """
        ),
    ),

    # --- Main Dashboard ---
    ui.output_ui("dashboard_ui"),
)


# ---------------------------------------------------------------
# Server
# ---------------------------------------------------------------

def server(input, output, session):
    # --- Reactive data (constant after load) ---
    data = reactive.value(dashboard_data)

    # --- Render dashboard ---
    @render.ui
    def dashboard_ui():
        # --- Main dashboard ---
        return ui.div(
            # Header
            ui.div(
                ui.h2("Tricorder Dashboard"),
                ui.div(
                    ui.span(f"Data refresh: {dashboard_data.data_refresh_date}"),
                    ui.span(f"Period: {dashboard_data.week_range[0]} to {dashboard_data.week_range[1]}"),
                    ui.input_action_button(
                        "reset_filters",
                        "Reset Filters",
                        class_="btn btn-outline-secondary btn-sm",
                    ),
                    class_="header-meta",
                ),
                class_="dashboard-header",
            ),

            # Tabs
            ui.navset_tab(
                ui.nav_panel("Overview", overview_ui("overview")),
                ui.nav_panel("Practice Explorer", practice_ui("practice")),
                ui.nav_panel("GP Explorer", gp_ui("gp")),
                ui.nav_panel("Dynamic Graph", dynamic_graph_ui("dynamic_graph")),
                ui.nav_panel("Geographic Map", map_ui("map")),
            ),
        )

    # --- Initialize module servers ---
    # Note: servers are called unconditionally because
    # Shiny registers them regardless of whether the UI is visible
    overview_server("overview", data=data)
    practice_server("practice", data=data)
    gp_server("gp", data=data)
    dynamic_graph_server("dynamic_graph", data=data)
    map_server("map", data=data)


# ---------------------------------------------------------------
# Application
# ---------------------------------------------------------------

app = App(
    app_ui,
    server,
    static_assets=str(BASE_DIR / "static"),
)
