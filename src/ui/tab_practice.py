"""
tab_practice.py
---------------
Tab 2: Practice Explorer (Sección 10 de la especificación).

Selector de práctica, resumen, gráfica semanal, contribución de GPs,
panel de dependencia, flags clínicos, calidad de grabación,
comparación con pares y modo de comparación multi-práctica.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.ui.common import (
    dependency_badge,
    download_button_styled,
    panel_card,
    summary_table,
    warning_banner,
)
from src.utils import df_to_csv_bytes, format_number, format_rate, format_ratio


@module.ui
def practice_ui():
    return ui.div(
        # --- Selector ---
        ui.output_ui("practice_selector_ui"),

        # --- Practice Summary ---
        ui.output_ui("practice_summary"),

        # --- Weekly Graph ---
        panel_card(
            "Weekly Utilisation",
            ui.input_select(
                "weekly_overlay",
                "Overlay:",
                choices={
                    "raw": "Raw weekly counts",
                    "rolling": "4-week rolling average",
                    "cumulative": "Cumulative",
                    "with_median": "With programme median",
                },
            ),
            output_widget("weekly_chart"),
            download_button_styled("download_weekly_csv"),
        ),

        # --- GP Contribution ---
        ui.row(
            ui.column(
                7,
                panel_card(
                    "GP Contribution",
                    ui.input_switch("show_inactive_gps", "Include inactive GPs", value=False),
                    output_widget("gp_contribution_chart"),
                ),
                panel_card(
                    "GP Statistical Tests",
                    ui.p("Note: Calculations use raw recording counts. Based on the selected practice's GPs.", class_="text-muted", style="font-size: 0.8rem;"),
                    ui.output_ui("practice_gini_ui"),
                    ui.hr(),
                    ui.h6("Chi-Squared Test (Bonferroni)"),
                    ui.input_radio_buttons(
                        "practice_chi_filter", 
                        "Show Significant:", 
                        {"both": "Both", "over": "Over-performers", "under": "Under-performers"}, 
                        inline=True
                    ),
                    ui.output_ui("practice_chi_squared_ui"),
                ),
            ),
            ui.column(
                5,
                # --- Dependency Panel ---
                panel_card(
                    "Champion Dependency",
                    ui.output_ui("dependency_panel"),
                ),
                # --- Clinical Flags ---
                panel_card(
                    "Clinical Flags",
                    ui.input_switch("flags_assigned_only", "Assigned only", value=False),
                    ui.output_ui("clinical_flags_panel"),
                    ui.p(
                        "⚠ Flags are not mutually exclusive — a recording may "
                        "contribute to more than one flag.",
                        style="color: var(--color-text-muted); font-size: 0.8rem; margin-top: 0.5rem;",
                    ),
                ),
                # --- Recording Quality ---
                panel_card(
                    "Recording Quality",
                    ui.output_ui("quality_panel"),
                ),
            ),
        ),

        # --- Comparison with Peers ---
        panel_card(
            "Peer Comparison",
            ui.input_select(
                "peer_metric",
                "Metric:",
                choices={
                    "rec_count": "Recordings",
                    "recordings_per_patient": "Recordings per active GP",
                    "active_gp_rate": "Active GP rate",
                    "assignment_rate": "Assignment rate",
                    "poor_pcg_rate": "Poor PCG rate",
                    "poor_ecg_rate": "Poor ECG rate",
                    "murmur_flag_rate": "Murmur flag rate",
                },
            ),
            output_widget("peer_comparison_chart"),
        ),

        # --- Multi-practice Comparison Mode ---
        panel_card(
            "Practice Comparison Mode",
            ui.output_ui("comparison_practices_ui"),
            ui.output_ui("comparison_limit_warning"),
            output_widget("comparison_chart"),
        ),
    )


@module.server
def practice_server(input, output, session, data):

    # --- Populate Selectors dynamically ---
    @render.ui
    def practice_selector_ui():
        d = data()
        names = sorted(d.site_df["site_name"].unique().tolist())
        return ui.input_selectize(
            "practice_select",
            "Select practice:",
            choices=names,
            selected=names[0] if names else None,
            width="100%",
        )

    @render.ui
    def comparison_practices_ui():
        d = data()
        names = sorted(d.site_df["site_name"].unique().tolist())
        return ui.input_selectize(
            "comparison_practices",
            "Select up to 10 practices to compare:",
            choices=names,
            multiple=True,
        )

    # --- Filtered Data for Selected Practice ---
    @reactive.calc
    def selected_practice():
        d = data()
        name = input.practice_select()
        if not name:
            return None
        row = d.site_df[d.site_df["site_name"] == name]
        return row.iloc[0] if not row.empty else None

    @reactive.calc
    def selected_gps():
        d = data()
        name = input.practice_select()
        if not name:
            return pd.DataFrame()
        return d.gp_df[d.gp_df["site_name"] == name]

    @reactive.calc
    def selected_weekly():
        d = data()
        name = input.practice_select()
        if not name:
            return pd.DataFrame()
        return d.weekly_df[d.weekly_df["site_name"] == name]

    # --- Resumen de práctica ---
    @render.ui
    def practice_summary():
        p = selected_practice()
        if p is None:
            return ui.p("Select a practice to view details.")

        last_week = p.get("last_active_week", None)
        last_week_str = (
            last_week.strftime("%Y-%m-%d") if pd.notna(last_week) else "—"
        )
        weeks_since = p.get("weeks_since_last_activity", None)
        weeks_since_str = str(int(weeks_since)) if pd.notna(weeks_since) else "—"

        return ui.div(
            summary_table([
                ("Practice", str(p["site_name"]), ""),
                ("Total Recordings", format_number(p["rec_count"]), ""),
                ("Labelled Patients", format_number(p["patient_count"]), ""),
                ("Assigned Recordings", format_number(p["assigned_rec_count"]), ""),
                ("Registered GPs", format_number(p.get("registered_gp_count", 0)), ""),
                ("Active GPs", format_number(p.get("active_gp_count", 0)), "(Registered GPs with at least 1 recording)"),
                ("Active GP Rate", format_rate(p.get("active_gp_rate", 0)), "(Percentage of registered GPs with at least 1 recording)"),
                ("Last Active Week", last_week_str, ""),
                ("Weeks Since Activity", weeks_since_str, ""),
            ]),
        )

    # --- Gráfica semanal ---
    @render_widget
    def weekly_chart():
        wk = selected_weekly()
        if wk.empty:
            fig = go.Figure()
            fig.add_annotation(text="No weekly data for this practice", showarrow=False)
            fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", height=300)
            return fig

        overlay = input.weekly_overlay()
        fig = go.Figure()

        if overlay in ("raw", "with_median"):
            fig.add_trace(go.Scatter(
                x=wk["week_start"], y=wk["weekly_recordings"],
                mode="lines+markers", name="Weekly",
                line=dict(color="#1a73e8", width=2),
                marker=dict(size=4),
                connectgaps=False,
            ))
        if overlay == "rolling":
            fig.add_trace(go.Scatter(
                x=wk["week_start"], y=wk["rolling_avg_4w"],
                mode="lines", name="4-week rolling avg",
                line=dict(color="#34a853", width=2),
                connectgaps=False,
            ))
        if overlay == "cumulative":
            fig.add_trace(go.Scatter(
                x=wk["week_start"], y=wk["cumulative_recordings"],
                mode="lines", name="Cumulative",
                line=dict(color="#fbbc04", width=2),
                fill="tozeroy", fillcolor="rgba(251, 188, 4, 0.1)",
            ))
        if overlay == "with_median":
            # Programme weekly median
            d = data()
            prog_median = (
                d.weekly_df.groupby("week_start")["weekly_recordings"]
                .median()
                .reset_index()
            )
            fig.add_trace(go.Scatter(
                x=prog_median["week_start"], y=prog_median["weekly_recordings"],
                mode="lines", name="Programme median",
                line=dict(color="#dadce0", dash="dash", width=1),
            ))

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

    @render.download(filename="practice_weekly.csv")
    def download_weekly_csv():
        yield df_to_csv_bytes(selected_weekly())

    # --- Contribución de GPs ---
    @render_widget
    def gp_contribution_chart():
        gps = selected_gps()
        if gps.empty:
            fig = go.Figure()
            fig.add_annotation(text="No GP data", showarrow=False)
            fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", height=300)
            return fig

        df = gps.copy()
        if not input.show_inactive_gps():
            df = df[df["rec_count"] > 0]

        df = df.sort_values("rec_count", ascending=True)

        fig = px.bar(
            df,
            x="rec_count",
            y="gp_label",
            orientation="h",
            color="is_active",
            color_discrete_map={True: "#1a73e8", False: "#dadce0"},
            labels={"rec_count": "Recordings", "gp_label": "GP", "is_active": "Active"},
        )
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=80, r=20, t=20, b=40),
            height=max(300, len(df) * 28),
            showlegend=True,
        )
        return fig

    # --- Estadísticas de GPs (Gini, Chi-Squared) ---
    @render.ui
    def practice_gini_ui():
        gps = selected_gps()
        if gps.empty:
            return ui.p("—")
        if not input.show_inactive_gps():
            gps = gps[gps["rec_count"] > 0]
            
        from src.metrics import compute_gini_coefficient
        gini = compute_gini_coefficient(gps["rec_count"])
        return ui.div(
            ui.span("Gini Coefficient: ", class_="fw-bold"),
            ui.span(f"{gini:.3f}")
        )
        
    @render.ui
    def practice_chi_squared_ui():
        gps = selected_gps()
        if gps.empty:
            return ui.p("—")
        if not input.show_inactive_gps():
            gps = gps[gps["rec_count"] > 0]
            
        from src.metrics import compute_chi_squared_tests
        df_chi = compute_chi_squared_tests(gps["gp_label"].tolist(), gps["rec_count"].tolist())
        
        if df_chi.empty:
            return ui.p("No data for tests.")
            
        filter_val = input.practice_chi_filter()
        if filter_val == "over":
            filtered_df = df_chi[(df_chi["is_significant"]) & (df_chi["Status"] == "Over-performer")]
        elif filter_val == "under":
            filtered_df = df_chi[(df_chi["is_significant"]) & (df_chi["Status"] == "Under-performer")]
        else:
            filtered_df = df_chi[df_chi["is_significant"]]
            
        if filtered_df.empty:
            return ui.p("No significant GPs found.")
            
        items = []
        for _, row in filtered_df.iterrows():
            color = "green" if row["Status"] == "Over-performer" else "red"
            items.append(
                ui.tags.li(
                    ui.span(f"{row['Practice']}: ", class_="fw-bold"),
                    ui.span(f"{row['Observed']} (Expected {row['Expected']:.1f}) ", style=f"color: {color};"),
                    ui.span(f"[p={row['p_value']:.2e}]", style="font-size: 0.8rem; color: #666;")
                )
            )
        return ui.div(
            ui.tags.ul(*items, style="padding-left: 20px; max-height: 200px; overflow-y: auto; margin-top: 10px;")
        )

    # --- Panel de dependencia ---
    @render.ui
    def dependency_panel():
        p = selected_practice()
        if p is None:
            return ui.p("—")

        badge = dependency_badge(p.get("dependency_category", "N/A"))

        return ui.div(
            ui.tags.table(
                ui.tags.tr(
                    ui.tags.td("Top GP contribution:", style="padding-right: 1rem;"),
                    ui.tags.td(format_rate(p.get("champion_dependency_score", 0))),
                ),
                ui.tags.tr(
                    ui.tags.td("Top 3 GPs contribution:"),
                    ui.tags.td(format_rate(p.get("top3_dependency_score", 0))),
                ),
                ui.tags.tr(
                    ui.tags.td("Active GPs:"),
                    ui.tags.td(format_number(p.get("active_gp_count", 0))),
                ),
                ui.tags.tr(
                    ui.tags.td("Dependency category:"),
                    ui.tags.td(badge),
                ),
                class_="data-table",
            ),
        )

    # --- Flags clínicos ---
    @render.ui
    def clinical_flags_panel():
        p = selected_practice()
        if p is None:
            return ui.p("—")

        assigned = input.flags_assigned_only()
        prefix = "assigned_" if assigned else ""
        denom = p.get(f"{prefix}rec_count", p["rec_count"]) if assigned else p["rec_count"]

        def _flag_row(label, count_col, rate_label):
            count_val = p.get(f"{prefix}{count_col}", 0)
            rate_val = (count_val / denom * 100) if denom > 0 else 0
            return ui.tags.tr(
                ui.tags.td(label),
                ui.tags.td(format_number(count_val)),
                ui.tags.td(format_rate(rate_val)),
            )

        return ui.tags.table(
            ui.tags.tr(
                ui.tags.th("Flag"), ui.tags.th("Count"), ui.tags.th("Rate"),
            ),
            _flag_row("Murmur", "murmur_flag_count", "murmur_flag_rate"),
            _flag_row("Low EF", "low_ef_flag_count", "low_ef_flag_rate"),
            _flag_row("AF", "af_flag_count", "af_flag_rate"),
            class_="data-table",
        )

    # --- Calidad de grabación ---
    @render.ui
    def quality_panel():
        p = selected_practice()
        if p is None:
            return ui.p("—")

        denom = p["rec_count"]
        assigned_denom = p["assigned_rec_count"]

        def _rate(num, den):
            return format_rate(num / den * 100) if den > 0 else "—"

        return ui.tags.table(
            ui.tags.tr(
                ui.tags.th("Metric"), ui.tags.th("All"), ui.tags.th("Assigned"),
            ),
            ui.tags.tr(
                ui.tags.td("Poor PCG"),
                ui.tags.td(f"{format_number(p['poor_pcg_count'])} ({_rate(p['poor_pcg_count'], denom)})"),
                ui.tags.td(f"{format_number(p['assigned_poor_pcg_count'])} ({_rate(p['assigned_poor_pcg_count'], assigned_denom)})"),
            ),
            ui.tags.tr(
                ui.tags.td("Poor ECG"),
                ui.tags.td(f"{format_number(p['poor_ecg_count'])} ({_rate(p['poor_ecg_count'], denom)})"),
                ui.tags.td(f"{format_number(p['assigned_poor_ecg_count'])} ({_rate(p['assigned_poor_ecg_count'], assigned_denom)})"),
            ),
            class_="data-table",
        )

    # --- Peer comparison ---
    @render_widget
    def peer_comparison_chart():
        p = selected_practice()
        if p is None:
            fig = go.Figure()
            fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", height=300)
            return fig

        d = data()
        metric = input.peer_metric()
        site_df = d.site_df

        selected_val = p.get(metric, 0)
        all_vals = site_df[metric].dropna()
        median_val = all_vals.median()
        q25 = all_vals.quantile(0.25)
        q75 = all_vals.quantile(0.75)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Selected Practice", "Median", "Q25", "Q75"],
            y=[selected_val, median_val, q25, q75],
            marker_color=["#1a73e8", "#dadce0", "#dadce0", "#dadce0"],
        ))
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=20, b=40),
            height=300,
            yaxis_title=metric.replace("_", " ").title(),
        )
        return fig

    # --- Comparison mode ---
    @render.ui
    def comparison_limit_warning():
        selected = input.comparison_practices()
        if selected and len(selected) > 10:
            return warning_banner("Maximum 10 practices can be compared at once.")
        return ui.div()

    @render_widget
    def comparison_chart():
        selected = input.comparison_practices()
        if not selected:
            fig = go.Figure()
            fig.add_annotation(text="Select practices to compare", showarrow=False)
            fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", height=300)
            return fig

        d = data()
        names = list(selected)[:10]
        df = d.site_df[d.site_df["site_name"].isin(names)].copy()

        fig = px.bar(
            df,
            x="site_name",
            y="rec_count",
            color="site_name",
            labels={"site_name": "Practice", "rec_count": "Recordings"},
        )
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=20, b=80),
            height=350,
            showlegend=False,
            xaxis_tickangle=-45,
        )
        return fig
