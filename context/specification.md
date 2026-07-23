Absolutely. The Version 1 specification below is designed as a build-ready functional specification for an R Shiny application. It uses the current practice, GP and weekly practice data, while explicitly treating GP postcode data as an additional input required for the geographic module.

# Landmark Tricorder Eko Utilisation Dashboard

## Version 1 Functional Specification

**Document status:** Draft for development  
**Application type:** Interactive Python Shiny dashboard  
**Primary purpose:** Monitor adoption, utilisation, recording quality and diagnostic flags associated with Eko stethoscope use across practices and registered GPs  
**Data period:** 2023 to 2026, subject to the dates present in each data refresh  
**Primary users:** Landmark study team, programme managers, clinical leads and authorised analysts

***

## 1. Background

The Landmark tricorder study used Eko stethoscopes to support the detection of cardiostructural disease. A key implementation limitation was under-utilisation of the equipment and the absence of a consistent framework for incorporating the devices into general practice workflows.

The available data now permits analysis at three connected levels:

1. **Practice-level aggregate utilisation**
2. **GP-level aggregate utilisation linked to practice**
3. **Weekly practice-level utilisation**

The dashboard will provide an interactive way to identify:

* High- and low-utilising practices
* High-utilising GPs within each practice
* Practices dependent on a single champion GP
* Registered GPs who have not used the equipment
* Changes in practice-level utilisation over time
* Geographic patterns in utilisation
* Recording quality and abnormal detection patterns

***

# 2. Version 1 Objectives

The Version 1 application must:

1. Provide a clear overview of Eko utilisation.
2. Allow users to select one or more practices for comparison.
3. Allow users to identify and compare GPs within a selected practice.
4. Display practice-level utilisation over time.
5. Identify champion, engaged, low-use and inactive users.
6. Measure how concentrated utilisation is within each practice.
7. Display geographic utilisation using GP or practice postcodes.
8. Allow filtered tables and charts to be downloaded.
9. distinguish labelled patients, total recordings and assigned recordings.
10. Present data-quality limitations transparently.

***

# 3. Scope

## 3.1 Included in Version 1

Version 1 will include six application sections:

1. **Overview**
2. **Practice Explorer**
3. **GP Explorer**
4. **Adoption and Outliers**
5. **Geographic Map**
6. **Data Quality and Definitions**

The application will support:

* Practice selection
* GP selection
* Multiple-practice comparison
* Date-range filtering for weekly practice utilisation
* Utilisation segmentation
* Practice champion-dependency metrics
* Diagnostic flag rates
* Poor-signal rates
* Interactive charts and tables
* CSV downloads
* Image downloads for principal charts, where technically practical
* Interactive mapping based on postcode coordinates

***

## 3.2 Not Included in Version 1

The following are outside Version 1:

* Patient-level analysis
* Patient-identifiable information
* Clinical decision support
* Prediction of disease
* Automated clinical recommendations
* User-level weekly trends, unless a GP-by-week dataset becomes available
* Causal analysis of why a practice adopted or stopped using the device
* Automated email alerts
* GP network diagrams
* Formal statistical modelling
* Automated postcode geocoding during every user session
* Direct write-back to source systems
* Role-specific views beyond basic access control

These may be considered for Version 2.

***

# 4. Important Data Constraint

The current data supports:

* GP-level cumulative utilisation
* GP-to-practice linkage
* Practice-level weekly utilisation

It does **not currently support GP-level utilisation over time**.

Therefore:

* The map can show **practice-level utilisation changing over time**.
* GP locations can be displayed using GP postcodes.
* GP markers can show cumulative GP utilisation.
* The app cannot accurately animate each individual GP’s activity over time unless a GP-week dataset is supplied.

For Version 1, the time-enabled map should therefore use one of these two approaches:

### Preferred approach

Use the practice postcode as the geographic location and animate the weekly practice utilisation directly.

### Alternative approach

Place GP markers at GP postcode locations but assign each GP the weekly utilisation of their associated practice. This must be labelled clearly as:

> “Practice-level weekly utilisation displayed at GP-associated locations.”

The preferred approach is analytically cleaner and avoids implying that a specific GP completed the recordings shown in a particular week.

***

# 5. User Groups

## 5.1 Programme Manager

Needs to:

* Assess overall adoption
* Identify non-adopting practices
* Monitor changes in utilisation
* Identify practices that may require implementation support

## 5.2 Clinical Lead

Needs to:

* Compare diagnostic flag rates
* Examine recording quality
* Identify high-utilising GPs and practices
* Explore whether high activity is distributed across the practice

## 5.3 Analyst or Researcher

Needs to:

* Apply filters
* Review definitions
* Download data
* Investigate outliers
* Reproduce summary figures

## 5.4 Application Administrator

Needs to:

* Replace or refresh source data
* Review validation warnings
* Manage postcode and coordinate lookup tables
* monitor failed joins and duplicate records

***

# 6. Navigation and Global Layout

## 6.1 Header

The header will contain:

* Application title
* Data refresh date
* Current date range
* Reset filters button
* Download menu
* Information/help button

## 6.2 Main Navigation

The left navigation panel will contain:

1. Overview
2. Practice Explorer
3. GP Explorer
4. Adoption and Outliers
5. Geographic Map
6. Data Quality and Definitions

## 6.3 Global Filters

The following filters should apply where relevant:

* Date range
* Practice
* GP identifier
* Utilisation category
* Active/inactive status
* Minimum recording count
* Diagnostic metric
* Assigned-only toggle

Not every filter will be visible on every tab. Filters should be context-sensitive.

## 6.4 Filter Behaviour

* The default practice selection is “All practices”.
* The default date range is the full available period.
* Empty values must not be silently dropped.
* A reset button must restore all default selections.
* Selected filters must be visible above or beside the results.
* Downloads must reflect the active filter state.
* Any chart based on fewer than a configurable minimum number of observations should display a low-volume warning.

***

# 7. Core Measures and Definitions

## 7.1 Activity Measures

### Total recordings

The value contained in `rec_count`.

This represents total recordings and may include multiple recordings for one patient.

### Labelled patients

The value contained in `patient_count`.

This represents patients whose examination was labelled or associated with a patient record.

### Assigned recordings

The value contained in `assigned_rec_count`.

This represents recordings assigned to patients and capable of being followed in the associated clinical system.

### Recordings per labelled patient

$$
\text{Recordings per patient}
=
\frac{\text{Total recordings}}{\text{Labelled patients}}
$$

If the labelled patient count is zero, the measure must return “Not calculable”, not zero.

### Assignment rate

$$
\text{Assignment rate}
=
\frac{\text{Assigned recordings}}{\text{Total recordings}}
\times 100
$$

### Active GP

A GP with:

$$
\text{rec\_count} > 0
$$

### Inactive GP

A registered GP with:

$$
\text{rec\_count} = 0
$$

### Active practice

A practice with:

$$
\text{rec\_count} > 0
$$

***

## 7.2 Recording Quality Measures

### Poor PCG rate

$$
\frac{\text{poor PCG recordings}}{\text{recordings}}
\times 100
$$

### Poor ECG rate

$$
\frac{\text{poor ECG recordings}}{\text{recordings}}
\times 100
$$

The dashboard must not describe these records as formal test failures unless that terminology is confirmed by the study team. The interface should use:

* Poor PCG signal
* Poor ECG signal
* Unanalysable recording, where supported by the agreed data dictionary

***

## 7.3 Diagnostic Flag Measures

The three available abnormal flag measures are:

* Murmur flag
* Low ejection fraction flag
* Atrial fibrillation flag

The working variable mapping is:

* `emas_rec_count` → murmur flag
* `eleft_rec_count` → low EF flag
* `afib_rec_count` → AF flag

These mappings must be confirmed before development sign-off.

### Flag rate

$$
\text{Flag rate}
=
\frac{\text{Flag count}}{\text{Total recordings}}
\times 100
$$

The application must refer to these values as **algorithmic flags** or **positive flags**, not confirmed diagnoses.

### Multiple classifications

A recording may contribute to more than one disease classification. Therefore, the three flag counts must not be summed and interpreted as a count of unique abnormal recordings.

***

## 7.4 Practice Adoption Measures

### Registered GP count

Number of GP identifiers linked to the practice.

### Active GP count

Number of GP identifiers linked to the practice with at least one recording.

### Active GP rate

$$
\frac{\text{Active GPs}}{\text{Registered GPs}}
\times 100
$$

### Champion-dependency score

$$
\text{Champion dependency}
=
\frac{\text{Recordings by highest-volume GP}}
{\text{Total GP-level recordings associated with the practice}}
\times 100
$$

Suggested categorisation:

* **Low dependency:** less than 40%
* **Moderate dependency:** 40% to less than 70%
* **High dependency:** 70% or above

These thresholds must be configurable rather than embedded permanently in application code.

### Important denominator decision

The champion-dependency score should use the sum of GP-level recording counts as its denominator, not the separate practice-level total, because practice and GP aggregates may not reconcile exactly.

The reconciliation difference must be displayed separately.

***

# 8. Utilisation Segmentation

## 8.1 GP Segmentation

GPs will be classified according to the following default rules:

### Inactive

No recordings.

### Very low use

1 to 9 recordings.

### Low use

10 to 49 recordings.

### Moderate use

50 to 199 recordings.

### High use

200 or more recordings.

### Champion

A GP meeting both of the following:

* In the top 10% of active GPs by recording count
* At least 200 recordings

This prevents low counts from being classified as champions in a sparse dataset.

The development team should make these thresholds configurable through a settings file.

***

## 8.2 Practice Segmentation

Practice categories should use both cumulative and recent activity.

### Never active

No recordings across the complete period.

### Low adoption

Practice has recorded activity, but:

* fewer than 50 cumulative recordings, or
* fewer than 10% of registered GPs are active

### Intermittent

Activity is present but concentrated in a minority of observed weeks.

### Engaged

Above-median cumulative activity and activity in the recent period.

### Champion practice

Meets all of the following:

* Top 10% of practices by recording volume
* At least two active GPs
* Activity in the most recent 12-week period

### Dormant

Previously active but no activity during the most recent 12 complete weeks.

A practice may be both high-volume historically and dormant currently. Therefore, cumulative adoption category and current activity status should be stored as separate fields.

***

# 9. Tab 1: Executive Overview

## 9.1 Purpose

Provide a concise summary of overall programme utilisation and adoption.

## 9.2 KPI Cards

Display:

* Practices enrolled
* Active practices
* Total registered GPs
* Active GPs
* Active GP rate
* Labelled patients
* Total recordings
* Assigned recordings
* Assignment rate
* Recordings per labelled patient

Each KPI should have:

* A concise title
* Formatted value
* Information tooltip
* Plain-language definition

## 9.3 Adoption Funnel

The funnel should contain:

1. Practices enrolled
2. Practices active
3. GPs registered
4. GPs active
5. Labelled patients
6. Assigned recordings
7. Total recordings

Because these are not necessarily sequential cohorts, the visual should be called an **adoption and activity funnel** rather than a patient conversion funnel.

## 9.4 Practice Activity Distribution

Interactive histogram or density-style distribution showing total recordings by practice.

Controls:

* Linear/logarithmic scale
* Include/exclude zero-use practices
* Metric selector:
  * Recordings
  * Patients
  * Assigned recordings
  * Active GP rate

## 9.5 GP Activity Distribution

Interactive distribution of recording counts across all registered GPs.

The zero-use group must be visible and selectable.

## 9.6 Concentration Chart

A cumulative concentration curve showing the proportion of total recordings generated by the highest-utilising GPs.

It should answer:

> What percentage of recordings is generated by the top 1%, 5%, 10% and 20% of GPs?

## 9.7 Top Practice and GP Panels

Two tables:

* Top 10 practices
* Top 10 GPs

The GP table should include practice name.

## 9.8 Weekly Programme Trend

Line chart showing weekly total practice utilisation across the selected date range.

Options:

* Weekly recordings
* Four-week rolling mean
* Cumulative recordings
* Number of active practices per week

***

# 10. Tab 2: Practice Explorer

## 10.1 Purpose

Allow detailed investigation of an individual practice and comparison with other practices.

## 10.2 Practice Selector

Searchable dropdown containing all practice names.

The selected practice must update all components on the tab.

## 10.3 Practice Summary

Display:

* Practice name
* Adoption category
* Current activity status
* Total recordings
* Labelled patients
* Assigned recordings
* Registered GP count
* Active GP count
* Active GP rate
* Champion-dependency score
* Most recent active week
* Weeks since last activity

## 10.4 Weekly Utilisation Chart

Display weekly practice activity.

Available overlays:

* Raw weekly counts
* Four-week rolling average
* Cumulative activity
* Programme median or selected peer comparator

The chart should support:

* Hover values
* Zoom
* Date-range selection
* Download as PNG
* Download of underlying CSV

## 10.5 GP Contribution Chart

Horizontal bar chart ranking all GPs linked to the selected practice.

Display:

* GP identifier
* Recording count
* Percentage of known GP-level practice activity
* Active/inactive category

Default sorting is descending by recordings.

Inactive users should be retained and shown when the “Include inactive GPs” option is enabled.

## 10.6 Practice Dependency Panel

Display:

* Top GP contribution
* Top three GP contribution
* Number of active GPs
* Champion-dependency category

Suggested interpretation:

* Green: distributed use
* Amber: moderate dependency
* Red: high dependency

Colour must not be the only means of conveying status.

## 10.7 Clinical Flags Panel

Display counts and rates for:

* Murmur
* Low EF
* AF

Provide a toggle between:

* All recordings
* Assigned recordings only

The display must state that flags are not mutually exclusive.

## 10.8 Recording Quality Panel

Display:

* Poor PCG count and rate
* Poor ECG count and rate
* Assigned poor PCG count and rate
* Assigned poor ECG count and rate

## 10.9 Peer Comparison

Compare the selected practice with:

* All-practice median
* All-practice interquartile range
* Selected practices
* Practices in the same utilisation band

Metrics:

* Recordings
* Recordings per active GP
* Active GP rate
* Assignment rate
* Poor PCG rate
* Poor ECG rate
* Each diagnostic flag rate

## 10.10 Practice Comparison Mode

Users may select up to 10 practices for a comparison chart.

If more than 10 are selected, the application should display a clear limit message.

***

# 11. Tab 3: GP Explorer

## 11.1 Purpose

Identify high- and low-utilising GPs and understand their contribution within their associated practice.

## 11.2 GP Selector

Searchable selector showing:

* GP identifier
* Practice name

The application must not disclose names or email addresses unless explicitly authorised and appropriately governed.

## 11.3 GP Summary

Display:

* GP identifier
* Practice
* Utilisation category
* Total recordings
* Labelled patients
* Assigned recordings
* Recordings per labelled patient
* Assignment rate
* Poor PCG rate
* Poor ECG rate
* Murmur flag rate
* Low EF flag rate
* AF flag rate

## 11.4 GP Ranking

Display:

* Rank among all registered GPs
* Rank among active GPs
* Rank within practice
* National percentile
* Percentage contribution to practice GP-level activity

Percentile rankings must state whether zero-use users are included.

The default should rank among active GPs, with an option to include all registered users.

## 11.5 GP-to-Practice Comparison

Visual comparison between:

* Selected GP
* Practice average per registered GP
* Practice average per active GP
* All-active-GP median

This should focus on activity metrics, not infer clinical performance.

## 11.6 GP Diagnostic and Quality Profile

Grouped display of:

* Recording-quality rates
* Diagnostic flag rates
* Assigned-only equivalents

Low denominators must trigger a warning.

## 11.7 Relevant Limitation

The GP Explorer will not contain a weekly GP chart in Version 1 because the supplied data contains GP-level cumulative totals rather than GP-level weekly activity.

Instead, it may show the selected GP’s cumulative utilisation alongside the weekly trend for their associated practice, clearly labelled as two different levels of analysis.

***

# 12. Tab 4: Adoption and Outliers

## 12.1 Purpose

Help programme teams identify where support, investigation or recognition may be required.

## 12.2 Champion GP Table

Columns:

* GP identifier
* Practice
* Total recordings
* Labelled patients
* Assigned recordings
* GP utilisation category
* GP rank
* Contribution to practice activity

## 12.3 Inactive GP Table

Columns:

* GP identifier
* Practice
* Registered status, if available
* Total recordings
* Practice activity category

This enables identification of inactive GPs located in otherwise active practices.

## 12.4 Practice Adoption Matrix

Scatter plot:

* X-axis: active GP rate
* Y-axis: total recordings
* Point size: number of registered GPs
* Point colour: current activity status

This helps distinguish:

* Broadly adopted, high-volume practices
* Single-champion practices
* Low-volume but distributed practices
* Inactive practices

## 12.5 Champion Dependency Plot

Plot practices according to:

* Total recordings
* Champion-dependency score

This highlights high-volume practices vulnerable to one GP leaving or stopping use.

## 12.6 Outlier Tables

Separate tables for:

* High volume
* High poor-PCG rate
* High poor-ECG rate
* Low assignment rate
* High recordings-per-patient ratio
* Large practice-to-GP reconciliation difference
* Previously active but now dormant

## 12.7 Outlier Interpretation

Outliers must not automatically be described as errors or poor performance.

Use neutral language such as:

* “Requires review”
* “Unusual relative to peers”
* “High observed rate”
* “Low denominator”
* “Possible data-recording difference”

***

# 13. Tab 5: Geographic Map

## 13.1 Purpose

Display the geographic distribution of adoption and show how practice-level utilisation changes over time.

## 13.2 Required Geographic Dataset

A postcode lookup table must be provided containing, at minimum:

* GP identifier
* Practice name
* GP postcode or practice postcode
* Latitude
* Longitude
* Location type
* Geocoding date
* Geocoding status

Recommended additional fields:

* Borough
* ICB
* PCN
* LSOA
* Ward
* Region

## 13.3 Privacy Position

Using personal residential GP postcodes is not recommended.

The preferred geographic field is:

* GP practice postcode, or
* professional work location postcode

If a GP postcode represents a personal address, it should not be displayed as an exact point. It should instead be:

* excluded,
* aggregated to a broader geography, or
* spatially perturbed according to an approved information-governance method.

## 13.4 Map Modes

### Practice location mode

One marker per practice.

This is the default and preferred mode.

### GP-associated location mode

One marker per GP or professional work location.

This mode should be available only when the supplied postcode data is approved for display.

### Heatmap mode

Display spatial intensity based on the selected metric.

Heatmaps must be interpreted as utilisation density, not population-adjusted prevalence.

## 13.5 Map Metrics

Users may colour or size markers by:

* Weekly recordings
* Cumulative recordings
* Labelled patients
* Active GP count
* Active GP rate
* Assignment rate
* Murmur flag count
* Low EF flag count
* AF flag count
* Practice adoption category

## 13.6 Time Controls

The map must include:

* Start week
* End week
* Single-week selector
* Play/pause control
* Playback speed
* Reset timeline button

For a selected week, the marker should show:

* Recordings in that week
* Cumulative recordings up to that week
* Current activity status
* Practice name
* Active GP information, where available

## 13.7 Animation Behaviour

When playback is enabled:

1. The selected week advances automatically.
2. Practice marker size updates according to weekly utilisation.
3. Marker colour updates according to the selected metric or activity band.
4. The week label updates prominently.
5. The map position and zoom remain stable.

## 13.8 Map Filters

* Date or week
* Practice
* GP utilisation category
* Practice adoption category
* Active/inactive
* Borough or region, if available
* Minimum recording volume
* Map layer

## 13.9 Map Pop-up

The practice pop-up should display:

* Practice name
* Postcode
* Weekly recordings
* Cumulative recordings
* Registered GPs
* Active GPs
* Active GP rate
* Adoption category
* Link to open the practice in Practice Explorer

## 13.10 Missing Coordinates

Practices or GPs without valid coordinates must:

* Remain in dashboard counts
* Be excluded only from the map
* Be included in a downloadable missing-geography table
* Trigger a visible map coverage indicator

Example:

> “Map displays 89 of 96 practices with valid geographic coordinates.”

***

# 14. Tab 6: Data Quality and Definitions

## 14.1 Purpose

Provide transparency and prevent misinterpretation.

## 14.2 Data Dictionary

Include definitions for:

* Practice
* GP identifier
* Labelled patient
* Recording
* Assigned recording
* Poor PCG
* Poor ECG
* Murmur flag
* Low EF flag
* AF flag
* Active user
* Dormant practice
* Champion-dependency score

## 14.3 Validation Summary

Display:

* Number of practices
* Number of GP records
* Number of unique GP identifiers
* Duplicate GP identifiers
* Missing practice names
* GP records with unmatched practices
* Practices with no linked GPs
* Missing postcodes
* Invalid postcodes
* Missing coordinates
* Negative count values
* Practice and GP total reconciliation differences

## 14.4 Known Issues Log

The dashboard should document known issues, including:

* Possible duplicate GP identifiers
* Similar practice names that may represent duplicate or separate organisations
* Practice-level and GP-level totals that may not reconcile
* Activity recorded without labelled patients
* Assigned recordings that may exceed labelled patient counts
* Disease flags that are not mutually exclusive
* Lack of GP-level weekly utilisation

***

# 15. Data Model

## 15.1 Practice Table

One row per practice.

Required fields:

* `practice_id`
* `practice_name`
* `patient_count`
* `rec_count`
* `poor_pcg_count`
* `poor_ecg_count`
* `murmur_flag_count`
* `low_ef_flag_count`
* `af_flag_count`
* `assigned_rec_count`
* Assigned quality and flag counts

A stable `practice_id` should be introduced. Practice name alone should not be the long-term key.

## 15.2 GP Table

One row per GP identifier and practice association.

Required fields:

* `gp_id`
* `practice_id`
* `practice_name`
* All aggregate activity fields
* Utilisation category
* Active status
* Rank and percentile fields

## 15.3 Weekly Practice Table

The current wide-format sheet should be transformed into long format:

* `practice_id`
* `practice_name`
* `week_start`
* `weekly_recordings`

The numeric Excel date headings must be converted to valid dates.

## 15.4 Geography Table

* `location_id`
* `gp_id`, where applicable
* `practice_id`
* `postcode`
* `latitude`
* `longitude`
* `location_type`
* `geocoding_status`
* Optional administrative geographies

## 15.5 Configuration Table

Store configurable rules such as:

* Utilisation cut-offs
* Champion percentile
* Dormancy period
* Rolling-average period
* Minimum denominator for rate display
* Maximum number of practices on comparison charts

***

# 16. Data Processing Requirements

At each refresh, the application pipeline must:

1. Import all expected sheets.
2. Validate sheet and column names.
3. Standardise practice names.
4. Convert count fields to numeric.
5. Convert weekly date headers to dates.
6. Transform weekly data from wide to long format.
7. Join GP records to practices.
8. Join geographic data.
9. Identify duplicate GP identifiers.
10. Calculate derived metrics.
11. Assign utilisation categories.
12. Generate validation and reconciliation outputs.
13. Stop publication if critical validation rules fail.

***

# 17. Practice Name Standardisation

The source data contains names that may be similar but not identical. For example, spelling variations may represent distinct practices or inconsistent labels.

Version 1 should use a controlled lookup:

* `source_practice_name`
* `standard_practice_name`
* `practice_id`
*
