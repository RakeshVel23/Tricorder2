# Landmark Tricorder Eko Utilisation Dashboard — Implementation Plan

## Goal

Build an interactive Python Shiny dashboard (Shiny for Python) that monitors adoption, utilisation, recording quality, and diagnostic flags for Eko stethoscope use across 96 GP practices and ~1,003 GPs, as defined in the [specification](file:///e:/VSC/Tricorder2/context/specification.md).

## Data Summary (from inspection)

| Sheet | Rows | Cols | Key |
|---|---|---|---|
| `site_level` | 96 practices | 14 numeric columns | `site_name` |
| `user_level` | 1,003 GPs | 15 cols (row 0 = variable names, row 1+ = data) | `Email address identifier` (anonymised integer), `site_name` |
| `site_weekly` | 94 practices | 138 cols (`site_name` + 137 weekly datetime columns) | `site_name` × `week_start` |

**Key findings:**
- `user_level` row 0 contains the actual variable names (matching `site_level`); row 1+ is data. Must parse with `header=1`.
- GP identifier column is `Email address identifier` — anonymised to integer codes.
- Site-level and GP-level `rec_count` totals reconcile perfectly (28,363 = 28,363).
- Weekly columns are `datetime` objects (not Excel serial numbers), ranging from 2023-10-08 to 2026-06-07.
- All numeric columns are already `int64` with zero nulls in `site_level` and `user_level`.

---

## User Review Required

> [!IMPORTANT]
> **Authentication Layer:** You requested a basic authentication layer for Posit Connect Cloud deployment. By default, Posit Connect Cloud can enforce its own access controls (requiring viewers to log in with their Posit accounts). However, if you need a shared app-level password for external users, I can implement a simple login screen inside the Shiny app itself that prompts for a password before displaying the dashboard.
> **Question:** Do you want me to build an app-level password login screen, or will you rely on Posit Connect's built-in access controls? (I will plan for a simple app-level password for now, which can be configured via an environment variable).

---

## Decisions Made (from feedback)

1. **Deployment Target:** We will deploy this to **Posit Connect Cloud** and include a basic authentication layer.
2. **Geographic Map:** We will build the map logic and use a placeholder until you supply the postcode data.
3. **GP identifier display:** Anonymized integer codes will be formatted as `GP-001`, `GP-002`, etc.
4. **Charting library:** Plotly (via `shinywidgets`) will be used.
5. **Map library:** ipyleaflet (via `shinywidgets`) or Folium will be used.
6. **Data refresh mechanism:** Data will be loaded only once on app startup.
7. **Missing weekly practices:** The 2 practices missing from `site_weekly` will be omitted from time-series views. Any gaps in weekly data for other practices will remain as gaps in the line charts.
8. **Python Shiny flavour:** We will use **Shiny Core** due to the modular 6-tab complexity.

---

## Proposed Changes

### Project Structure

```
e:\VSC\Tricorder2\
├── app.py                      # Main Shiny app entry point (with Auth wrapper)
├── requirements.txt            # Python dependencies
├── rsconnect-python.json       # (Generated later) Deployment config for Posit Connect
├── config/
│   ├── thresholds.yaml         # Configurable thresholds (Section 15.5)
│   └── column_mapping.yaml     # Source → standard column name mapping
├── data/
│   └── tricorder_enrollment_20260503 anonymised with identifier codes.xlsx
├── context/
│   └── specification.md
├── src/
│   ├── __init__.py
│   ├── auth.py                 # Basic authentication layer (Login UI & Server logic)
│   ├── data_loader.py          # Excel ingestion, validation, transforms
│   ├── data_models.py          # Dataclass / typed dict definitions
│   ├── metrics.py              # All derived metric calculations
│   ├── segmentation.py         # GP and practice segmentation logic
│   ├── validators.py           # Data quality checks and reconciliation
│   ├── utils.py                # Formatting, download helpers
│   └── ui/
│       ├── __init__.py
│       ├── common.py           # Shared UI components (KPI cards, filter panels)
│       ├── tab_overview.py     # Tab 1: Executive Overview
│       ├── tab_practice.py     # Tab 2: Practice Explorer
│       ├── tab_gp.py           # Tab 3: GP Explorer
│       ├── tab_adoption.py     # Tab 4: Adoption and Outliers
│       ├── tab_map.py          # Tab 5: Geographic Map
│       └── tab_data_quality.py # Tab 6: Data Quality and Definitions
├── static/
│   └── styles.css              # Custom CSS
└── tests/
    ├── test_data_loader.py
    ├── test_metrics.py
    └── test_segmentation.py
```

---

### Phase 1 — Data Pipeline (`src/`)

#### [NEW] [config/thresholds.yaml](file:///e:/VSC/Tricorder2/config/thresholds.yaml)
Configurable thresholds from spec Sections 7.4 and 8:
- GP utilisation bands: inactive (0), very low (1–9), low (10–49), moderate (50–199), high (200+)
- Champion: top 10% AND ≥200 recordings
- Champion-dependency: low (<40%), moderate (40–70%), high (≥70%)
- Practice dormancy: 12 weeks
- Rolling average: 4 weeks
- Min denominator for rate display
- Max practices on comparison charts: 10

#### [NEW] [config/column_mapping.yaml](file:///e:/VSC/Tricorder2/config/column_mapping.yaml)
Maps raw Excel column headers to standardised internal names. Handles the `user_level` sheet's descriptive headers and the `site_level` clean headers.

#### [NEW] [src/data_loader.py](file:///e:/VSC/Tricorder2/src/data_loader.py)
Responsibilities (per spec Section 16):
1. Import all 3 sheets from the Excel file on startup.
2. Parse `user_level` with `header=1` to skip the descriptive row
3. Rename `Email address identifier` → `gp_id`; assign formatted labels (`GP-001` etc.)
4. Validate sheet names and column names exist
5. Standardise practice names (initially identity mapping; lookup table ready)
6. Ensure all count fields are numeric (already int64, but guard against future issues)
7. Pivot `site_weekly` from wide → long format: `(site_name, week_start, weekly_recordings)`
8. Omit missing practices and missing weeks (leaving them as gaps for time-series).
9. Join GP records to practices
10. Return typed dataframes for downstream use

#### [NEW] [src/metrics.py](file:///e:/VSC/Tricorder2/src/metrics.py)
All derived calculations from spec Section 7.

#### [NEW] [src/segmentation.py](file:///e:/VSC/Tricorder2/src/segmentation.py)
GP segmentation (spec Section 8.1) and Practice segmentation (spec Section 8.2).

#### [NEW] [src/validators.py](file:///e:/VSC/Tricorder2/src/validators.py)
Data quality checks (spec Section 14.3).

---

### Phase 2 — Authentication Layer & Global UI Shell

#### [NEW] [src/auth.py](file:///e:/VSC/Tricorder2/src/auth.py)
- **Login UI module**: A simple modal or full-screen page asking for a password.
- **Auth Server logic**: Validates the entered password against an environment variable (e.g., `APP_PASSWORD`).
- Secures the main UI so no data is rendered until the correct password is provided.

#### [NEW] [app.py](file:///e:/VSC/Tricorder2/app.py)
Main application entry point:
- Load data at startup using `data_loader`
- Wrap the main application UI inside the authentication layer.
- Set up Shiny Core app with `ui.navset_pill_list` or `ui.navset_tab` for 6 tabs
- Global header with app title, data refresh date, reset filters button
- CSS link to `static/styles.css`

#### [NEW] [static/styles.css](file:///e:/VSC/Tricorder2/static/styles.css)
Custom styling including clinical theme and UI constraints.

#### [NEW] [src/ui/common.py](file:///e:/VSC/Tricorder2/src/ui/common.py)
Reusable UI components (`kpi_card`, `filter_panel`, `download_button`, `low_volume_warning`).

---

### Phase 3 — Tab 1: Executive Overview

#### [NEW] [src/ui/tab_overview.py](file:///e:/VSC/Tricorder2/src/ui/tab_overview.py)
- **KPI cards**, **Adoption funnel**, **Practice activity distribution**, **GP activity distribution**, **Concentration curve**, **Top 10 practice and GP tables**, **Weekly programme trend**.

---

### Phase 4 — Tab 2: Practice Explorer

#### [NEW] [src/ui/tab_practice.py](file:///e:/VSC/Tricorder2/src/ui/tab_practice.py)
- **Practice selector**, **Practice summary panel**, **Weekly utilisation chart**, **GP contribution chart**, **Practice dependency panel**, **Clinical flags panel**, **Recording quality panel**, **Peer comparison**, **Comparison mode**.

---

### Phase 5 — Tab 3: GP Explorer

#### [NEW] [src/ui/tab_gp.py](file:///e:/VSC/Tricorder2/src/ui/tab_gp.py)
- **GP selector**, **GP summary**, **GP ranking**, **GP-to-practice comparison**, **Diagnostic and quality profile**, **Limitation note**.

---

### Phase 6 — Tab 4: Adoption and Outliers

#### [NEW] [src/ui/tab_adoption.py](file:///e:/VSC/Tricorder2/src/ui/tab_adoption.py)
- **Champion GP table**, **Inactive GP table**, **Practice adoption matrix**, **Champion dependency plot**, **7 outlier tables**, **Neutral language** descriptions.

---

### Phase 7 — Tab 5: Geographic Map

#### [NEW] [src/ui/tab_map.py](file:///e:/VSC/Tricorder2/src/ui/tab_map.py)
- **Placeholder UI** with explanation: "Geographic data (postcode lookup table) has not yet been supplied."
- **File upload slot** for a CSV/Excel postcode lookup (for testing before data is permanently added)
- **Ready-to-activate map logic** using ipyleaflet or Folium.

---

### Phase 8 — Tab 6: Data Quality and Definitions

#### [NEW] [src/ui/tab_data_quality.py](file:///e:/VSC/Tricorder2/src/ui/tab_data_quality.py)
- **Data dictionary**, **Validation summary**, **Known issues log**, **Download** validation report as CSV.

---

### Phase 9 — Polish & Posit Connect Deployment

- Wire up **CSV download** for every table and **PNG download** for principal charts.
- Install `rsconnect-python` to enable deployment to Posit Connect Cloud.
- Generate a `manifest.json` using `rsconnect write-manifest shiny .` so that Posit Connect can build the environment properly.

---

## Dependencies (`requirements.txt`)

```
shiny>=1.0.0
shinywidgets>=0.3.0
pandas>=2.0.0
openpyxl>=3.1.0
plotly>=5.18.0
pyyaml>=6.0
numpy>=1.24.0
htmltools>=0.5.0
ipyleaflet>=0.18.0    
rsconnect-python>=1.22.0 # for Posit Connect deployment
```

---

## Verification Plan

### Automated Tests
```bash
python -m pytest tests/ -v
```

### Manual Verification
- Run `shiny run app.py` and visually verify each of the 6 tabs.
- Test that the Basic Authentication screen blocks access until the correct password is provided.
- Verify filter interactions and CSV downloads.
- Confirm gaps in the weekly data for practices render as broken lines in the charts.
- Deploy to Posit Connect Cloud and verify the authentication layer works correctly in production.
