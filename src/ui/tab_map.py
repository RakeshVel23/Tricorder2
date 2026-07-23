"""
tab_map.py
----------
Tab 5: Geographic Map (Sección 13 de la especificación).

Mapa dinámico con controles de tiempo (slider animable),
selector de métrica (semanal vs acumulada), y toggle de modo
heatmap vs bubble. Los marcadores se actualizan reactivamente
sin re-renderizar el mapa completo.
"""

import math
import pandas as pd
from shiny import ui, render, module, reactive
from shinywidgets import render_widget, output_widget
import ipyleaflet as L
from ipywidgets import HTML as IpyHTML

from src.ui.common import panel_card


# -----------------------------------------------------------------
# Constantes de diseño
# -----------------------------------------------------------------

# Tamaño mínimo y máximo del radio de los CircleMarkers (px)
MIN_RADIUS = 4
MAX_RADIUS = 25

# Centro por defecto (North West London)
DEFAULT_CENTER = (51.55, -0.3)
DEFAULT_ZOOM = 10


# -----------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------

def _scale_radius(value: float, max_value: float) -> float:
    """Escala un valor numérico a un radio de marcador proporcional."""
    if max_value == 0 or pd.isna(value):
        return MIN_RADIUS
    # Escala raíz cuadrada para que el *área* sea proporcional al valor
    ratio = math.sqrt(value / max_value)
    return MIN_RADIUS + ratio * (MAX_RADIUS - MIN_RADIUS)


def _build_popup_html(
    site_name: str,
    weekly_rec: float,
    cumulative_rec: float,
    week_label: str,
) -> str:
    """Genera el HTML del popup de cada marcador."""
    weekly_display = int(weekly_rec) if pd.notna(weekly_rec) else "—"
    cumulative_display = int(cumulative_rec) if pd.notna(cumulative_rec) else "—"

    return f"""
        <div style="font-family: 'Roboto', sans-serif; min-width: 180px; font-size: 13px;">
            <strong style="display: block; border-bottom: 1px solid #e0e0e0;
                           padding-bottom: 4px; margin-bottom: 6px; color: #1a73e8;">
                {site_name}
            </strong>
            <div style="color: #5f6368;"><b>Week:</b> {week_label}</div>
            <div><b>This week:</b> {weekly_display}</div>
            <div><b>Cumulative:</b> {cumulative_display}</div>
        </div>
    """


# -----------------------------------------------------------------
# UI
# -----------------------------------------------------------------

@module.ui
def map_ui():
    return ui.div(
        panel_card(
            "Geographic Distribution — Practice Utilisation Over Time",
            ui.layout_sidebar(
                # --- Sidebar con controles ---
                ui.sidebar(
                    ui.h6("Time Controls", class_="fw-bold mb-2"),

                    # El slider se renderiza desde el server (necesita datos
                    # para conocer el rango de semanas disponible)
                    ui.output_ui("week_slider_ui"),

                    ui.hr(),
                    ui.h6("Display Options", class_="fw-bold mb-2"),

                    ui.input_select(
                        "metric",
                        "Size markers by",
                        choices={
                            "weekly_recordings": "Weekly Recordings",
                            "cumulative_recordings": "Cumulative Recordings",
                        },
                        selected="weekly_recordings",
                    ),

                    ui.input_switch(
                        "heatmap_mode",
                        "Heatmap mode",
                        value=False,
                    ),

                    width=280,
                    open="open",
                ),

                # --- Mapa ---
                ui.div(
                    output_widget("practice_map"),
                    style="height: 600px; width: 100%;",
                ),
            ),
        ),
    )


# -----------------------------------------------------------------
# Server
# -----------------------------------------------------------------

@module.server
def map_server(input, output, session, data):

    # ---- Datos derivados (solo se calculan una vez) ----

    @reactive.calc
    def geo_weekly_df():
        """Cruza weekly_data con site_data para obtener coordenadas."""
        d = data()
        weekly = d.weekly_df.copy()
        sites = d.site_df[["site_name", "latitude", "longitude"]].copy()

        merged = weekly.merge(sites, on="site_name", how="inner")
        # Descartar prácticas sin coordenadas
        merged = merged.dropna(subset=["latitude", "longitude"])
        return merged

    @reactive.calc
    def sorted_weeks():
        """Lista ordenada de todas las semanas disponibles."""
        return sorted(geo_weekly_df()["week_start"].unique())

    # ---- Slider dinámico ----

    @render.ui
    def week_slider_ui():
        weeks = sorted_weeks()
        if not weeks:
            return ui.p("No weekly data available.", class_="text-muted")

        return ui.input_slider(
            "selected_week",
            "Select week",
            min=0,
            max=len(weeks) - 1,
            value=len(weeks) - 1,
            step=1,
            animate=ui.AnimationOptions(interval=600, loop=True),
            # Mostrar la fecha como etiqueta
            post=f"  ({weeks[-1]})",
        )

    # ---- Datos filtrados por semana ----

    @reactive.calc
    def week_data():
        """Datos del mapa para la semana seleccionada."""
        weeks = sorted_weeks()
        idx = input.selected_week()

        if idx is None or not weeks:
            return pd.DataFrame()

        selected_week = weeks[int(idx)]
        df = geo_weekly_df()
        return df[df["week_start"] == selected_week].copy()

    # ---- Mapa base (se renderiza una sola vez) ----

    @render_widget
    def practice_map():
        m = L.Map(
            center=DEFAULT_CENTER,
            zoom=DEFAULT_ZOOM,
            scroll_wheel_zoom=True,
        )
        tile = L.TileLayer(
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        )
        m.add_layer(tile)
        return m

    # ---- Estado reactivo de las capas ----
    # Almacenar la referencia a la capa actual para poder removerla
    current_layer = reactive.value(None)

    @reactive.effect
    @reactive.event(input.selected_week, input.metric, input.heatmap_mode)
    def _update_map_layers():
        """Actualiza solo las capas del mapa, sin re-renderizar el widget."""
        wk = week_data()
        if wk.empty:
            return

        map_widget = practice_map.widget

        # Eliminar la capa anterior si existe
        prev = current_layer()
        if prev is not None:
            try:
                map_widget.remove_layer(prev)
            except Exception:
                pass

        is_heatmap = input.heatmap_mode()
        metric_col = input.metric()
        weeks = sorted_weeks()
        idx = int(input.selected_week())
        week_label = weeks[idx] if idx < len(weeks) else "—"

        if is_heatmap:
            # --- Modo Heatmap ---
            locations = []
            for _, row in wk.iterrows():
                value = row.get(metric_col, 0)
                if pd.notna(value) and value > 0:
                    locations.append([row["latitude"], row["longitude"], float(value)])

            if locations:
                heatmap = L.Heatmap(
                    locations=locations,
                    radius=25,
                    blur=15,
                    max_zoom=18,
                )
                map_widget.add_layer(heatmap)
                current_layer.set(heatmap)
            else:
                current_layer.set(None)
        else:
            # --- Modo Bubble ---
            max_val = wk[metric_col].max() if metric_col in wk.columns else 0
            if pd.isna(max_val):
                max_val = 0

            layer_group = L.LayerGroup()

            for _, row in wk.iterrows():
                lat = row["latitude"]
                lon = row["longitude"]
                site_name = row["site_name"]
                metric_value = row.get(metric_col, 0)
                weekly_rec = row.get("weekly_recordings", 0)
                cumulative_rec = row.get("cumulative_recordings", 0)

                radius = _scale_radius(metric_value, max_val)

                # Color basado en actividad semanal
                has_activity = pd.notna(weekly_rec) and weekly_rec > 0
                fill_color = "#1a73e8" if has_activity else "#dadce0"

                marker = L.CircleMarker(
                    location=(lat, lon),
                    radius=int(radius),
                    color="white",
                    weight=1,
                    fill_color=fill_color,
                    fill_opacity=0.75,
                )

                popup_content = _build_popup_html(
                    site_name, weekly_rec, cumulative_rec, week_label,
                )
                marker.popup = IpyHTML(value=popup_content)

                layer_group.add_layer(marker)

            map_widget.add_layer(layer_group)
            current_layer.set(layer_group)
