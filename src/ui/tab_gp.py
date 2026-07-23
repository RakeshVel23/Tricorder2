"""
tab_gp.py
---------
Tab 3: GP Explorer (Section 11 of the specification).

GP selector, summary, ranking, GP-practice comparison,
diagnostic and quality profile, and limitation note.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.ui.common import (
    info_banner,
    summary_table,
    panel_card,
    warning_banner,
)
from src.utils import format_number, format_rate, format_ratio


@module.ui
def gp_ui():
    return ui.div(
        # --- Selector ---
        ui.input_selectize(
            "gp_select",
            "Select GP:",
            choices=[],
            width="100%",
        ),

        # --- Summary ---
        ui.output_ui("gp_summary"),

        # --- Ranking ---
        panel_card(
            "GP Ranking",
            ui.output_ui("gp_ranking"),
            ui.p(
                "Rankings are calculated among active GPs by default.",
                style="color: var(--color-text-muted); font-size: 0.8rem;",
            ),
        ),

        # --- GP vs Practice Comparison ---
        panel_card(
            "GP vs Practice Comparison",
            output_widget("gp_practice_chart"),
        ),

        # --- Diagnostic and Quality Profile ---
        ui.row(
            ui.column(
                6,
                panel_card(
                    "Recording Quality Profile",
                    ui.output_ui("gp_quality_profile"),
                ),
            ),
            ui.column(
                6,
                panel_card(
                    "Diagnostic Flag Profile",
                    ui.output_ui("gp_flag_profile"),
                ),
            ),
        ),

        # --- Limitation Note ---
        info_banner(
            "GP-level weekly data is not available in Version 1. "
            "The chart above shows this GP's cumulative utilisation "
            "alongside the weekly trend for their associated practice."
        ),

        # --- Combined Graph: GP cumulative + practice weekly ---
        panel_card(
            "GP Cumulative vs Practice Weekly Trend",
            output_widget("gp_combined_chart"),
        ),
    )


@module.server
def gp_server(input, output, session, data):

    @reactive.effect
    def _populate_gp_selector():
        d = data()
        # Build options: GP-001 (Practice Name)
        options = {
            row["gp_label"]: f"{row['gp_label']} — {row['site_name']}"
            for _, row in d.gp_df.iterrows()
        }
        ui.update_selectize("gp_select", choices=options)

    @reactive.calc
    def selected_gp():
        d = data()
        label = input.gp_select()
        if not label:
            return None
        row = d.gp_df[d.gp_df["gp_label"] == label]
        return row.iloc[0] if not row.empty else None

    # --- Summary ---
    @render.ui
    def gp_summary():
        g = selected_gp()
        if g is None:
            return ui.p("Select a GP to view details.")

        return summary_table([
            ("GP", str(g["gp_label"]), ""),
            ("Practice", str(g["site_name"]), ""),
            ("Total Recordings", format_number(g["rec_count"]), ""),
            ("Labelled Patients", format_number(g["patient_count"]), ""),
            ("Assigned Recordings", format_number(g["assigned_rec_count"]), ""),
            ("Recs per Patient", format_ratio(g.get("recordings_per_patient")), ""),
            ("Assignment Rate", format_rate(g.get("assignment_rate", 0)), ""),
            ("Poor PCG Rate", format_rate(g.get("poor_pcg_rate", 0)), ""),
            ("Poor ECG Rate", format_rate(g.get("poor_ecg_rate", 0)), ""),
            ("Murmur Flag Rate", format_rate(g.get("murmur_flag_rate", 0)), ""),
            ("Low EF Flag Rate", format_rate(g.get("low_ef_flag_rate", 0)), ""),
            ("AF Flag Rate", format_rate(g.get("af_flag_rate", 0)), ""),
        ])

    # --- Ranking ---
    @render.ui
    def gp_ranking():
        g = selected_gp()
        if g is None:
            return ui.p("—")

        return ui.tags.table(
            ui.tags.tr(
                ui.tags.td("Rank among all GPs:"),
                ui.tags.td(format_number(g.get("rank_all", 0))),
            ),
            ui.tags.tr(
                ui.tags.td("Rank among active GPs:"),
                ui.tags.td(
                    format_number(g["rank_active"])
                    if pd.notna(g.get("rank_active")) else "—"
                ),
            ),
            ui.tags.tr(
                ui.tags.td("Rank within practice:"),
                ui.tags.td(format_number(g.get("rank_in_practice", 0))),
            ),
            ui.tags.tr(
                ui.tags.td("National percentile (active):"),
                ui.tags.td(
                    format_rate(g["national_percentile"], 1)
                    if pd.notna(g.get("national_percentile")) else "—"
                ),
            ),
            ui.tags.tr(
                ui.tags.td("Contribution to practice:"),
                ui.tags.td(format_rate(g.get("contribution_pct", 0))),
            ),
            class_="data-table",
        )

    # --- GP vs Practice Comparison ---
    @render_widget
    def gp_practice_chart():
        g = selected_gp()
        if g is None:
            fig = go.Figure()
            fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", height=300)
            return fig

        d = data()
        practice_name = g["site_name"]
        practice_gps = d.gp_df[d.gp_df["site_name"] == practice_name]
        active_gps = practice_gps[practice_gps["rec_count"] > 0]

        gp_val = g["rec_count"]
        avg_per_registered = practice_gps["rec_count"].mean()
        avg_per_active = active_gps["rec_count"].mean() if not active_gps.empty else 0

        # Median among all active GPs in the programme
        all_active = d.gp_df[d.gp_df["rec_count"] > 0]
        median_all = all_active["rec_count"].median() if not all_active.empty else 0

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["This GP", "Practice avg\n(all GPs)", "Practice avg\n(active GPs)", "National\nmedian (active)"],
            y=[gp_val, avg_per_registered, avg_per_active, median_all],
            marker_color=["#1a73e8", "#dadce0", "#34a853", "#fbbc04"],
        ))
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=20, b=60),
            height=300,
            yaxis_title="Recordings",
        )
        return fig

    # --- Quality Profile ---
    @render.ui
    def gp_quality_profile():
        g = selected_gp()
        if g is None:
            return ui.p("—")

        low_denom = g["rec_count"] < 5
        content = ui.tags.table(
            ui.tags.tr(ui.tags.th("Metric"), ui.tags.th("All"), ui.tags.th("Assigned")),
            ui.tags.tr(
                ui.tags.td("Poor PCG"),
                ui.tags.td(f"{format_number(g['poor_pcg_count'])} ({format_rate(g.get('poor_pcg_rate', 0))})"),
                ui.tags.td(format_number(g["assigned_poor_pcg_count"])),
            ),
            ui.tags.tr(
                ui.tags.td("Poor ECG"),
                ui.tags.td(f"{format_number(g['poor_ecg_count'])} ({format_rate(g.get('poor_ecg_rate', 0))})"),
                ui.tags.td(format_number(g["assigned_poor_ecg_count"])),
            ),
            class_="data-table",
        )

        if low_denom:
            return ui.div(
                warning_banner("Low denominator — rates may not be representative."),
                content,
            )
        return content

    # --- Flag Profile ---
    @render.ui
    def gp_flag_profile():
        g = selected_gp()
        if g is None:
            return ui.p("—")

        low_denom = g["rec_count"] < 5
        content = ui.tags.table(
            ui.tags.tr(ui.tags.th("Flag"), ui.tags.th("All"), ui.tags.th("Assigned")),
            ui.tags.tr(
                ui.tags.td("Murmur"),
                ui.tags.td(f"{format_number(g['murmur_flag_count'])} ({format_rate(g.get('murmur_flag_rate', 0))})"),
                ui.tags.td(format_number(g["assigned_murmur_flag_count"])),
            ),
            ui.tags.tr(
                ui.tags.td("Low EF"),
                ui.tags.td(f"{format_number(g['low_ef_flag_count'])} ({format_rate(g.get('low_ef_flag_rate', 0))})"),
                ui.tags.td(format_number(g["assigned_low_ef_flag_count"])),
            ),
            ui.tags.tr(
                ui.tags.td("AF"),
                ui.tags.td(f"{format_number(g['af_flag_count'])} ({format_rate(g.get('af_flag_rate', 0))})"),
                ui.tags.td(format_number(g["assigned_af_flag_count"])),
            ),
            class_="data-table",
        )

        if low_denom:
            return ui.div(
                warning_banner("Low denominator — rates may not be representative."),
                content,
            )
        return content

    # --- Combined Graph ---
    @render_widget
    def gp_combined_chart():
        g = selected_gp()
        if g is None:
            fig = go.Figure()
            fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", height=300)
            return fig

        d = data()
        practice_name = g["site_name"]
        wk = d.weekly_df[d.weekly_df["site_name"] == practice_name].copy()

        if wk.empty:
            fig = go.Figure()
            fig.add_annotation(text="No weekly data for this practice", showarrow=False)
            fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", height=300)
            return fig

        fig = go.Figure()

        # Practice weekly trend
        fig.add_trace(go.Scatter(
            x=wk["week_start"], y=wk["weekly_recordings"],
            mode="lines", name="Practice weekly",
            line=dict(color="#dadce0", width=1),
            yaxis="y",
            connectgaps=False,
        ))

        # GP horizontal line (total cumulative)
        fig.add_hline(
            y=g["rec_count"],
            line_dash="dash",
            line_color="#1a73e8",
            annotation_text=f"{g['gp_label']} total: {g['rec_count']}",
            annotation_font_color="#1a73e8",
        )

        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=20, b=40),
            height=350,
            xaxis_title="Week",
            yaxis_title="Recordings",
        )
        return fig
