# California School Performance (CAASPP) Data Commons Import

## Overview
This directory contains the automated Data Commons import pipeline for California public school academic performance data from the **California Assessment of Student Performance and Progress (CAASPP)** Smarter Balanced Summative Assessments.

The data covers student achievement in **English Language Arts/Literacy (ELA)** and **Mathematics** across California public schools, school districts, counties, and statewide aggregates from 2015 to the present.

- **Primary Source**: California Department of Education (CDE) / Educational Testing Service (ETS)
- **Research Portal**: [https://caaspp-elpac.ets.org/caaspp/ResearchFileListSB](https://caaspp-elpac.ets.org/caaspp/ResearchFileListSB)
- **Import Tier**: Automated StatVar Import

---

## Directory Structure

```
california_school_performance/
├── config/
│   ├── california_school_performance_metadata.csv     # Processor configurations (delimiters, headers, output columns)
│   ├── california_school_performance_pvmap.csv        # Property-Value mappings for subjects, grades, demographics, and metrics
│   ├── california_school_performance_statvars.mcf     # Pre-defined StatisticalVariable MCF nodes (6,050 StatVars)
│   └── school_code_mapping.json                       # Mapping of California CDS school/district codes to NCES DCIDs
├── test_data/                                         # Test fixtures for E2E validation
│   ├── sample_input.txt                               # Sample raw CAASPP input records
│   ├── sample_state_output.csv                        # Expected sample CSV observations
│   └── sample_state_output.tmcf                       # Expected sample TMCF mapping
├── california_school_performance_test.py              # Unit tests for download, normalization, and processing
├── download.py                                        # Automated data fetch and extraction script
├── process.py                                         # High-throughput processor generating CSV, TMCF, MCF, and counters
├── manifest.json                                      # Data Commons import specification
├── README.md                                          # Documentation and usage guide
└── validation_config.json                             # Production import validation rules
```

---

## Statistical Variables (StatVars) & Geographic Coverage

The pipeline processes the full California CAASPP dataset across all geographic entities and demographic subgroups:

- **Geographic Coverage (`--keep_all_entities=True`, default)**:
  Includes California statewide (`geoId/06`), all 58 counties (`geoId/06001`–`geoId/06115`), ~1,000 school districts (`nces/...`), and ~10,000+ public and charter schools (`nces/...` and `CA-...` fallback identifiers), mapped via `config/school_code_mapping.json`.
- **Full Demographic Breakdown (`--data_mode=all_groups`, default)**:
  Expands across all 55 demographic subgroups, 8 grade levels (Grades 3–8, 11, and Grade 13 All Grades), 2 subjects, and 7 metrics, generating **6,050 Statistical Variables** (`5,966` legacy CNS StatVars + `84` Subgroup 243 Grade 3–8 StatVars).

### Schema Dimensions:
- **Population Type**: `Student`
- **School Subjects**:
  - `EnglishLanguageArts` (Test ID: 1)
  - `Mathematics` (Test ID: 2)
- **Grade Levels**:
  - Grades 3, 4, 5, 6, 7, 8, 11, 13 (`dcid:SchoolGrade3` – `dcid:SchoolGrade13`, where `SchoolGrade13` represents all grades combined)
- **Demographic Subgroups (55 groups)**:
  - All Students (Subgroup ID: 1)
  - Gender (`Male`, `Female`)
  - Race / Ethnicity (`White`, `BlackOrAfricanAmericanAlone`, `Asian`, `Filipino`, `HispanicOrLatino`, `AmericanIndianOrAlaskaNative`, `NativeHawaiianOrOtherPacificIslanderAlone`, `TwoOrMoreRaces`)
  - Socioeconomic Status (`EconomicallyDisadvantaged`, `NotEconomicallyDisadvantaged`)
  - Intersection of Race × Socioeconomic Status (16 groups)
  - Disability Status (`WithDisability`, `NoDisability`)
  - English Learner & Fluency Status (`InitialFluentProficient`, `ReclassifiedFluentProficient`, `OnlyEnglish`, `CurrentLearner`, `EverLearned`, `Adult`, `ToBeDetermined`, duration `< 12 months`, duration `>= 12 months`, `LTEL` 6+ years, `AR-LTEL` 4–5 years, `Never-EL`)
  - Parent Education Level (`LessThanHighSchoolGraduate`, `HighSchoolGraduateIncludesEquivalency`, `SomeCollegeNoDegree`, `ParentCollegeGraduate`, `GraduateSchoolOrPostGraduate`, `CA_DeclinedToState`)
  - Special Student Populations (`Homeless`, `HavingHome`, `Foster`, `NotFoster`, `Migrant`, `NotMigrant`, `FamilyOfArmedForces`, `NotFamilyOfArmedForces`)
- **Metrics**:
  - `Total Students Tested` / `Students Tested`: Count of students (`measuredProperty: count`, `measurementMethod: CaliforniaAssessmentOfStudentPerformanceAndProgress`)
  - `Mean Scale Score`: Mean assessment score (`measuredProperty: assessmentScore`, `statType: meanValue`)
  - `Percentage Standard Exceeded`: Educational achievement level `CA_StandardExceeded` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Met`: Educational achievement level `CA_StandardMet` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Met and Above`: Educational achievement level `CA_StandardMetAndAbove` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Nearly Met`: Educational achievement level `CA_StandardNearlyMet` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Not Met`: Educational achievement level `CA_StandardNotMet` (`scalingFactor: 100`, `unit: Percent`)

---

## How to Run

> **Note**: Commands below should be run from this directory: `statvar_imports/us_education/california_school_performance/`.

### 1. Download and Process Active Years (`2023–Present`, Default)
Historical data for `2015–2022` (`84.7M` observations) is stored in GCS under `historic/` (`gs://datcom-prod-imports/statvar_imports/us_education/california_school_performance/CaliforniaSchoolPerformance/historic/`) and automatically copied into `<version>/historic/genmcf/` on each run by the import executor. By default, `download.py` fetches and normalizes post-2022 years (`--years=2023-present`):
```bash
# Step 1: Download and normalize post-2022 years (default: --years=2023-present)
python3 download.py

# Step 2: Generate CSV observations, TMCF, MCF, and counters
python3 process.py \
  --input_data=input_files/sb_ca_all_years_normalized.txt \
  --pv_map=config/california_school_performance_pvmap.csv \
  --config_file=config/california_school_performance_metadata.csv \
  --existing_statvar_mcf=config/california_school_performance_statvars.mcf \
  --output_path=output_files/california_school_performance_all_years_output \
  --output_counters=counters/california_school_performance_counters.csv
```

### 2. Download All Years (`2015–Present`) or Specific Years
To fetch and normalize all years (`2015–present`, skipping 2020) or specific years:
```bash
# All available years (2015-present)
python3 download.py --years=all

# Specific range
python3 download.py --years=2015-2024

# Specific single year
python3 download.py --years=2024
```

### 3. Quick Test Run
To download a lightweight test sample and verify the pipeline:
```bash
python3 download.py --test_mode
```

---

## Testing

Run unit tests from repository root:
```bash
python3 -m unittest statvar_imports/us_education/california_school_performance/california_school_performance_test.py
```
Or directly from this directory:
```bash
python3 -m unittest california_school_performance_test.py
```

---

## Output Files
The pipeline produces standard Data Commons import artifacts in `output_files/`:
- `california_school_performance_output.csv`: Complete multi-year observations table
- `california_school_performance_output.tmcf`: Template MCF linking columns to Data Commons schema nodes
- `california_school_performance_output.mcf`: StatisticalVariable MCF definitions
