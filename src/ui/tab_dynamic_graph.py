"""
tab_dynamic_graph.py
--------------------
Dynamic GA-style graph plotting recordings over time for selected practices.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.ui.common import panel_card
from src.utils import format_number

@module.ui
def dynamic_graph_ui():
    return ui.div(
        panel_card(
            "Weekly Recordings Trend",
            output_widget("trend_chart"),
        ),
        panel_card(
            "Select Practices to Plot",
            ui.p(
                "Click on rows to select practices. Hold Shift and Ctrl/Cmd to select multiple. "
                "(Note: 'Active GPs' refers to registered GPs with at least 1 recording) "
                "Click on the headings of the table to sort by the specified variable",
                style="color: var(--color-text-secondary); font-size: 0.85rem;"
            ),
            ui.div(
                ui.input_action_button("plot_btn", "Plot Rows", class_="btn-primary"),
                style="margin-bottom: 12px;"
            ),
            ui.output_data_frame("practice_table"),
        )
    )

@module.server
def dynamic_graph_server(input, output, session, data):

    @reactive.calc
    def display_df():
        d = data()
        df = d.site_df[["site_name", "rec_count", "patient_count", "assigned_rec_count", "active_gp_count"]].copy()
        df.columns = ["Practice", "Total Recordings", "Patients", "Assigned", "Active GPs"]
        return df

    @render.data_frame
    def practice_table():
        return render.DataGrid(display_df(), selection_mode="rows")

    @render_widget
    @reactive.event(input.plot_btn, ignore_none=False, ignore_init=False)
    def trend_chart():
        d = data()
        weekly = d.weekly_df.copy()
        df_display = display_df()
        
        # Get selected rows from the DataGrid (isolated so it doesn't trigger on its own)
        with reactive.isolate():
            selected_indices = input.practice_table_selected_rows()
        
        if not selected_indices:
            # Plot Total
            total_weekly = weekly.groupby("week_start", as_index=False)["weekly_recordings"].sum()
            fig = px.line(
                total_weekly,
                x="week_start",
                y="weekly_recordings",
                title="Total Weekly Recordings (All Practices)",
                markers=True,
                color_discrete_sequence=["#3498db"]
            )
            fig.update_traces(fill='tozeroy', fillcolor="rgba(26, 115, 232, 0.1)")
        else:
            # Extract selected practice names
            # Ensure selected_indices is an iterable of integers
            selected_practices = df_display.iloc[list(selected_indices)]["Practice"].tolist()
            filtered_weekly = weekly[weekly["site_name"].isin(selected_practices)]
            
            if filtered_weekly.empty:
                fig = go.Figure()
                fig.update_layout(title="No data for selected practices")
            else:
                fig = px.line(
                    filtered_weekly,
                    x="week_start",
                    y="weekly_recordings",
                    color="site_name",
                    title="Weekly Recordings by Selected Practices",
                    markers=True
                )
        
        fig.update_traces(connectgaps=False)
        
        fig.update_layout(
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
