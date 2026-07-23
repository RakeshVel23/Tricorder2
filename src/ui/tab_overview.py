"""
tab_overview.py
---------------
Tab 1: Executive Overview (Sección 9 de la especificación).

KPI cards, funnel de adopción, distribuciones, curva de concentración,
top 10 tables y tendencia semanal del programa.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.ui.common import (
    download_button_styled,
    info_banner,
    summary_table,
    warning_banner,
    panel_card,
)
from src.utils import df_to_csv_bytes, format_number, format_rate, format_ratio


# ---------------------------------------------------------------
# UI
# ---------------------------------------------------------------

@module.ui
def overview_ui():
    return ui.div(
        # --- KPI Cards ---
        ui.output_ui("kpi_section"),

        # # --- Adoption Funnel ---
        # panel_card(
        #     "Adoption & Activity Funnel",
        #     output_widget("funnel_chart"),
        # ),

        # --- Distributions ---
        # ui.row(
        #     ui.column(
        #         6,
        #         panel_card(
        #             "Practice Activity Distribution",
        #             ui.input_select(
        #                 "dist_metric",
        #                 "Metric:",
        #                 choices={
        #                     "rec_count": "Recordings",
        #                     "patient_count": "Patients",
        #                     "assigned_rec_count": "Assigned recordings",
        #                     "active_gp_rate": "Active GP rate",
        #                 },
        #             ),
        #             ui.input_switch("dist_log_scale", "Logarithmic scale", value=False),
        #             ui.input_switch("dist_include_zero", "Include zero-use", value=True),
        #             output_widget("practice_dist_chart"),
        #         ),
        #     ),
        #     ui.column(
        #         6,
        #         panel_card(
        #             "GP Activity Distribution",
        #             output_widget("gp_dist_chart"),
        #         ),
        #     ),
        # ),

        # --- Concentration Curve ---
        panel_card(
            "Recording Concentration Curve",
            output_widget("concentration_chart"),
            ui.p(
                "Shows the proportion of total recordings generated "
                "by the highest-utilising GPs.",
                style="color: var(--color-text-secondary); font-size: 0.85rem;",
            ),
        ),

        # --- Top 10 ---
        ui.row(
            ui.column(
                6,
                panel_card(
                    "Top 10 Practices",
                    ui.output_data_frame("top_practices_table"),
                    download_button_styled("download_top_practices"),
                ),
            ),
            ui.column(
                6,
                panel_card(
                    "Top 10 GPs",
                    ui.output_data_frame("top_gps_table"),
                    download_button_styled("download_top_gps"),
                ),
            ),
        ),

        # --- Programme Weekly Trend ---
        panel_card(
            "Weekly Programme Trend",
            ui.input_select(
                "trend_metric",
                "Display:",
                choices={
                    "total_weekly": "Weekly recordings",
                    "rolling_avg_4w": "4-week rolling average",
                    "cumulative": "Cumulative recordings",
                    "active_practices": "Active practices per week",
                },
            ),
            output_widget("programme_trend_chart"),
        ),
    )


# ---------------------------------------------------------------
# Server
# ---------------------------------------------------------------

@module.server
def overview_server(input, output, session, data):
    """Lógica del servidor para la pestaña Executive Overview.

    Args:
        data: reactive.Value conteniendo DashboardData con métricas calculadas.
    """

    # --- KPI Section ---
    @render.ui
    def kpi_section():
        d = data()
        site_df = d.site_df
        gp_df = d.gp_df

        total_practices = len(site_df)
        active_practices = int((site_df["rec_count"] > 0).sum())
        total_gps = len(gp_df)
        active_gps = int((gp_df["rec_count"] > 0).sum())
        active_gp_rate = (active_gps / total_gps * 100) if total_gps > 0 else 0
        total_patients = int(site_df["patient_count"].sum())
        total_recordings = int(site_df["rec_count"].sum())
        assigned_recordings = int(site_df["assigned_rec_count"].sum())
        assignment_rate = (
            assigned_recordings / total_recordings * 100
            if total_recordings > 0 else 0
        )
        recs_per_patient = (
            total_recordings / total_patients if total_patients > 0 else None
        )

        return summary_table([
            ("Practices Enrolled", format_number(total_practices), "Total number of practices in the dataset"),
            ("Active Practices", format_number(active_practices), "Practices with at least one recording"),
            ("Registered GPs", format_number(total_gps), "Total GP identifiers across all practices"),
            ("Active GPs", format_number(active_gps), "Registered GPs with at least 1 recording"),
            ("Active GP Rate", format_rate(active_gp_rate), "Percentage of registered GPs with at least 1 recording"),
            ("Labelled Patients", format_number(total_patients), "Patients whose exam was labelled"),
            ("Total Recordings", format_number(total_recordings), "Total recordings (may include multiple per patient)"),
            ("Assigned Recordings", format_number(assigned_recordings), "Recordings assigned to patients in the clinical system"),
            ("Assignment Rate", format_rate(assignment_rate), "Assigned recordings / total recordings"),
            ("Recs per Patient", format_ratio(recs_per_patient), "Total recordings / labelled patients"),
        ])

    # # --- Funnel ---
    # @render_widget
    # def funnel_chart():
    #     d = data()
    #     site_df = d.site_df
    #     gp_df = d.gp_df

    #     stages = [
    #         "Practices enrolled",
    #         "Practices active",
    #         "GPs registered",
    #         "GPs active",
    #         "Labelled patients",
    #         "Assigned recordings",
    #         "Total recordings",
    #     ]
    #     values = [
    #         len(site_df),
    #         int((site_df["rec_count"] > 0).sum()),
    #         len(gp_df),
    #         int((gp_df["rec_count"] > 0).sum()),
    #         int(site_df["patient_count"].sum()),
    #         int(site_df["assigned_rec_count"].sum()),
    #         int(site_df["rec_count"].sum()),
    #     ]

    #     fig = go.Figure(go.Funnel(
    #         y=stages,
    #         x=values,
    #         textinfo="value+percent initial",
    #         marker=dict(
    #             color=[
    #                 "#1a73e8", "#34a853", "#1a73e8", "#34a853",
    #                 "#fbbc04", "#34a853", "#1a73e8",
    #             ],
    #         ),
    #     ))
    #     fig.update_layout(
    #         template="plotly_white",
    #         paper_bgcolor="rgba(0,0,0,0)",
    #         plot_bgcolor="rgba(0,0,0,0)",
    #         margin=dict(l=20, r=20, t=20, b=20),
    #         height=350,
    #     )
    #     return fig

    # --- Practice distribution ---
    # @render_widget
    # def practice_dist_chart():
    #     d = data()
    #     df = d.site_df.copy()
    #     metric = input.dist_metric()

    #     if not input.dist_include_zero():
    #         df = df[df["rec_count"] > 0]

    #     fig = px.histogram(
    #         df,
    #         x=metric,
    #         nbins=30,
    #         labels={metric: metric.replace("_", " ").title()},
    #         color_discrete_sequence=["#1a73e8"],
    #     )
    #     if input.dist_log_scale() and metric != "active_gp_rate":
    #         fig.update_xaxes(type="log")

    #     fig.update_layout(
    #         template="plotly_white",
    #         paper_bgcolor="rgba(0,0,0,0)",
    #         plot_bgcolor="rgba(0,0,0,0)",
    #         margin=dict(l=40, r=20, t=20, b=40),
    #         height=300,
    #         yaxis_title="Number of practices",
    #     )
    #     return fig

    # --- GP distribution ---
    @render_widget
    def gp_dist_chart():
        d = data()
        df = d.gp_df.copy()

        fig = px.histogram(
            df,
            x="rec_count",
            nbins=40,
            labels={"rec_count": "Recordings"},
            color_discrete_sequence=["#34a853"],
        )
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=20, b=40),
            height=300,
            yaxis_title="Number of GPs",
        )
        return fig

    # --- Concentration curve ---
    @render_widget
    def concentration_chart():
        d = data()
        df = d.gp_df[d.gp_df["rec_count"] > 0].copy()

        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No active GPs", showarrow=False)
            return fig

        # Ordenar de mayor a menor
        df = df.sort_values("rec_count", ascending=False).reset_index(drop=True)
        total = df["rec_count"].sum()
        df["cum_pct"] = (df["rec_count"].cumsum() / total) * 100
        df["gp_pct"] = ((df.index + 1) / len(df)) * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["gp_pct"],
            y=df["cum_pct"],
            mode="lines",
            fill="tozeroy",
            line=dict(color="#1a73e8", width=2),
            fillcolor="rgba(26, 115, 232, 0.1)",
            name="Concentration",
        ))

        # Línea de igualdad
        fig.add_trace(go.Scatter(
            x=[0, 100],
            y=[0, 100],
            mode="lines",
            line=dict(color="#dadce0", dash="dash", width=1),
            name="Equal distribution",
        ))

        # Anotaciones en percentiles clave
        for pct in [1, 5, 10, 20]:
            idx = max(0, int(len(df) * pct / 100) - 1)
            cum_val = df.iloc[idx]["cum_pct"]
            fig.add_annotation(
                x=pct, y=cum_val,
                text=f"Top {pct}%: {cum_val:.0f}%",
                showarrow=True,
                arrowhead=2,
                font=dict(size=10, color="#fbbc04"),
            )

        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=20, b=40),
            height=350,
            xaxis_title="% of active GPs (ranked highest first)",
            yaxis_title="% of total recordings",
            showlegend=True,
            legend=dict(x=0.6, y=0.2),
        )
        return fig

    # --- Top 10 practices ---
    @render.data_frame
    def top_practices_table():
        d = data()
        top = (
            d.site_df
            .nlargest(10, "rec_count")
            [["site_name", "rec_count", "patient_count", "assigned_rec_count",
              "active_gp_count", "active_gp_rate"]]
            .copy()
        )
        top.columns = [
            "Practice", "Recordings", "Patients", "Assigned",
            "Active GPs", "Active GP Rate %",
        ]
        top["Active GP Rate %"] = top["Active GP Rate %"].round(1)
        return render.DataGrid(top, row_selection_mode="none")

    @render.download(filename="top_10_practices.csv")
    def download_top_practices():
        d = data()
        top = d.site_df.nlargest(10, "rec_count")
        yield df_to_csv_bytes(top)

    # --- Top 10 GPs ---
    @render.data_frame
    def top_gps_table():
        d = data()
        top = (
            d.gp_df
            .nlargest(10, "rec_count")
            [["gp_label", "site_name", "rec_count", "patient_count",
              "assigned_rec_count"]]
            .copy()
        )
        top.columns = [
            "GP", "Practice", "Recordings", "Patients",
            "Assigned",
        ]
        return render.DataGrid(top, row_selection_mode="none")

    @render.download(filename="top_10_gps.csv")
    def download_top_gps():
        d = data()
        top = d.gp_df.nlargest(10, "rec_count")
        yield df_to_csv_bytes(top)

    # --- Programme trend ---
    @render_widget
    def programme_trend_chart():
        d = data()
        prog = d.programme_weekly.copy()
        metric = input.trend_metric()

        label_map = {
            "total_weekly": "Weekly Recordings",
            "rolling_avg_4w": "4-Week Rolling Average",
            "cumulative": "Cumulative Recordings",
            "active_practices": "Active Practices",
        }

        fig = px.line(
            prog,
            x="week_start",
            y=metric,
            labels={
                "week_start": "Week",
                metric: label_map.get(metric, metric),
            },
            color_discrete_sequence=["#1a73e8"],
        )
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=20, b=40),
            height=350,
        )
        return fig
