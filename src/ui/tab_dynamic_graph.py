"""
tab_dynamic_graph.py
--------------------
Dynamic GA-style graph plotting recordings over time for selected practices.
Includes statistical tests (Gini coefficient, Chi-squared).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.ui.common import panel_card
from src.utils import format_number
from src.metrics import compute_gini_coefficient, compute_chi_squared_tests

@module.ui
def dynamic_graph_ui():
    return ui.div(
        panel_card(
            "Weekly Recordings Trend",
            output_widget("trend_chart"),
        ),
        panel_card(
            "Select Practices to Plot & Analyze",
            ui.p(
                "Click on rows to select practices. Hold Shift and Ctrl/Cmd to select multiple. "
                "Click 'Plot Rows' to update the chart and statistics below.",
                style="color: var(--color-text-secondary); font-size: 0.85rem;"
            ),
            ui.div(
                ui.input_action_button("plot_btn", "Plot Rows", class_="btn-primary"),
                ui.input_action_button("select_all_btn", "Select All", class_="btn-outline-secondary ms-2"),
                ui.span(
                    ui.input_switch("show_total_switch", "Overlay Total", value=False),
                    style="display: inline-block; margin-left: 15px; vertical-align: middle; padding-top: 5px;"
                ),
                style="margin-bottom: 12px; display: flex; align-items: center;"
            ),
            ui.row(
                ui.column(
                    8,
                    ui.output_data_frame("practice_table")
                ),
                ui.column(
                    4,
                    ui.div(
                        ui.h5("Statistical Tests", class_="text-primary"),
                        ui.p("Note: Calculations use raw recording counts.", class_="text-muted", style="font-size: 0.8rem;"),
                        ui.output_ui("gini_ui"),
                        ui.hr(),
                        ui.h6("Chi-Squared Test (Bonferroni)"),
                        ui.input_radio_buttons(
                            "chi_filter", 
                            "Show Significant:", 
                            {"both": "Both", "over": "Over-performers", "under": "Under-performers"}, 
                            inline=True
                        ),
                        ui.output_ui("chi_squared_ui"),
                        style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #fcfcfc;"
                    )
                )
            )
        )
    )

@module.server
def dynamic_graph_server(input, output, session, data):
    
    selected_practices_state = reactive.value([])

    @reactive.calc
    def display_df():
        d = data()
        df = d.site_df[["site_name", "rec_count", "patient_count", "assigned_rec_count", "active_gp_count"]].copy()
        df.columns = ["Practice", "Total Recordings", "Patients", "Assigned", "Active GPs"]
        return df

    @render.data_frame
    def practice_table():
        return render.DataGrid(display_df(), selection_mode="rows")

    @reactive.effect
    @reactive.event(input.plot_btn)
    def update_selected_from_table():
        df_display = display_df()
        selected_indices = input.practice_table_selected_rows()
        if selected_indices:
            selected = df_display.iloc[list(selected_indices)]["Practice"].tolist()
            selected_practices_state.set(selected)
        else:
            selected_practices_state.set([])

    @reactive.effect
    @reactive.event(input.select_all_btn)
    def update_selected_all():
        df_display = display_df()
        selected = df_display["Practice"].tolist()
        selected_practices_state.set(selected)

    @render_widget
    def trend_chart():
        d = data()
        weekly = d.weekly_df.copy()
        selected_practices = selected_practices_state()
        show_total = input.show_total_switch()
        
        fig = go.Figure()
        
        # 1. Plot selected practices
        if selected_practices:
            filtered_weekly = weekly[weekly["site_name"].isin(selected_practices)]
            if not filtered_weekly.empty:
                fig_selected = px.line(
                    filtered_weekly,
                    x="week_start",
                    y="weekly_recordings",
                    color="site_name",
                    markers=True
                )
                for trace in fig_selected.data:
                    fig.add_trace(trace)
        
        # 2. Plot Total if requested OR if nothing is selected
        if show_total or not selected_practices:
            total_weekly = weekly.groupby("week_start", as_index=False)["weekly_recordings"].sum()
            
            if not selected_practices:
                fig.add_trace(go.Scatter(
                    x=total_weekly["week_start"],
                    y=total_weekly["weekly_recordings"],
                    mode="lines+markers",
                    name="Total (All Practices)",
                    line=dict(color="#3498db"),
                    fill='tozeroy', 
                    fillcolor="rgba(26, 115, 232, 0.1)"
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=total_weekly["week_start"],
                    y=total_weekly["weekly_recordings"],
                    mode="lines+markers",
                    name="Total (All Practices)",
                    line=dict(color="black", width=3, dash="dash")
                ))
        
        title = "Weekly Recordings Trend"
        if not selected_practices:
            title = "Total Weekly Recordings (All Practices)"
        elif show_total:
            title = "Weekly Recordings by Selected Practices (vs Total)"
        else:
            title = "Weekly Recordings by Selected Practices"
        
        fig.update_traces(connectgaps=False)
        
        fig.update_layout(
            title=title,
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=40, b=40),
            height=400,
            xaxis_title="",
            yaxis_title="Recordings",
            legend_title="Practice",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        return fig

    @render.ui
    def gini_ui():
        selected = selected_practices_state()
        if not selected:
            return ui.p("Waiting for selection...")
        d = data()
        subset = d.site_df[d.site_df["site_name"].isin(selected)]
        gini = compute_gini_coefficient(subset["rec_count"])
        return ui.div(
            ui.span("Gini Coefficient: ", class_="fw-bold"),
            ui.span(f"{gini:.3f}")
        )

    @render.ui
    def chi_squared_ui():
        selected = selected_practices_state()
        if not selected:
            return ui.p("")
        d = data()
        subset = d.site_df[d.site_df["site_name"].isin(selected)]
        df_chi = compute_chi_squared_tests(subset["site_name"].tolist(), subset["rec_count"].tolist())
        
        if df_chi.empty:
            return ui.p("No data for tests.")
            
        filter_val = input.chi_filter()
        if filter_val == "over":
            filtered_df = df_chi[(df_chi["is_significant"]) & (df_chi["Status"] == "Over-performer")]
        elif filter_val == "under":
            filtered_df = df_chi[(df_chi["is_significant"]) & (df_chi["Status"] == "Under-performer")]
        else:
            filtered_df = df_chi[df_chi["is_significant"]]
            
        if filtered_df.empty:
            return ui.p("No significant practices found.")
            
        # Create a list of practices
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
            ui.tags.ul(*items, style="padding-left: 20px; max-height: 300px; overflow-y: auto; margin-top: 10px;")
        )
