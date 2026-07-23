"""
tab_data_quality.py
-------------------
Tab 6: Data Quality and Definitions (Sección 14 de la especificación).

Diccionario de datos, resumen de validación, log de problemas conocidos
y descarga del informe de validación.
"""

import pandas as pd
from shiny import module, reactive, render, ui

from src.ui.common import download_button_styled, panel_card
from src.utils import df_to_csv_bytes
from src.validators import validation_report_to_df


# ---------------------------------------------------------------
# Diccionario de datos (Sección 14.2)
# ---------------------------------------------------------------

DATA_DICTIONARY = [
    ("Practice", "An enrolled healthcare practice participating in the Landmark tricorder study."),
    ("GP identifier", "Anonymised code representing a registered GP. Displayed as GP-001, GP-002, etc."),
    ("Labelled patient", "A patient whose examination was labelled or associated with a patient record (patient_count)."),
    ("Recording", "A single stethoscope recording session. Multiple recordings may exist per patient (rec_count)."),
    ("Assigned recording", "A recording assigned to a patient record and trackable in the clinical system (assigned_rec_count)."),
    ("Poor PCG", "A recording flagged as having poor heart sounds / PCG signal (unanalysable)."),
    ("Poor ECG", "A recording flagged as having poor ECG signal trace (unanalysable)."),
    ("Murmur flag", "An algorithmic flag indicating a positive result for a low murmur (emas_rec_count). Not a confirmed diagnosis."),
    ("Low EF flag", "An algorithmic flag indicating a positive result for low ejection fraction (eleft_rec_count). Not a confirmed diagnosis."),
    ("AF flag", "An algorithmic flag indicating a positive result for atrial fibrillation (afib_rec_count). Not a confirmed diagnosis."),
    ("Active user", "A GP with at least one recording (rec_count > 0)."),
    ("Dormant practice", "A previously active practice with no recordings in the most recent 12 complete weeks."),
    ("Champion-dependency score", "Percentage of a practice's GP-level recordings contributed by its highest-volume GP."),
]

# ---------------------------------------------------------------
# Problemas conocidos (Sección 14.4)
# ---------------------------------------------------------------

KNOWN_ISSUES = [
    "Possible duplicate GP identifiers may exist where the same person is registered under more than one code.",
    "Similar practice names may represent distinct organisations or inconsistent labelling of the same practice.",
    "Practice-level and GP-level recording totals may not always reconcile exactly.",
    "Some activity may be recorded without a corresponding labelled patient.",
    "Assigned recording counts may occasionally exceed labelled patient counts.",
    "Disease flags (murmur, low EF, AF) are not mutually exclusive — a recording may contribute to more than one flag.",
    "GP-level weekly utilisation data is not currently available; only practice-level weekly data is supplied.",
]


@module.ui
def data_quality_ui():
    return ui.div(
        # --- Diccionario de datos ---
        panel_card(
            "Data Dictionary",
            ui.output_data_frame("data_dict_table"),
        ),

        # --- Resumen de validación ---
        panel_card(
            "Validation Summary",
            ui.output_data_frame("validation_table"),
            download_button_styled("download_validation"),
        ),

        # --- Problemas conocidos ---
        panel_card(
            "Known Issues",
            ui.tags.ul(
                *[ui.tags.li(issue) for issue in KNOWN_ISSUES],
                style="color: var(--color-text-secondary); line-height: 1.8;",
            ),
        ),
    )


@module.server
def data_quality_server(input, output, session, data):

    @render.data_frame
    def data_dict_table():
        df = pd.DataFrame(DATA_DICTIONARY, columns=["Term", "Definition"])
        return render.DataGrid(df, row_selection_mode="none")

    @render.data_frame
    def validation_table():
        d = data()
        df = validation_report_to_df(d.validation_report)
        return render.DataGrid(df, row_selection_mode="none")

    @render.download(filename="validation_report.csv")
    def download_validation():
        d = data()
        df = validation_report_to_df(d.validation_report)
        yield df_to_csv_bytes(df)
