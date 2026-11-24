# California School Performance (CAASPP) Data Commons Import

## Overview
This directory contains the automated Data Commons import pipeline for California public school academic performance data from the **California Assessment of Student Performance and Progress (CAASPP)** Smarter Balanced Summative Assessments.

The data covers student achievement in **English Language Arts/Literacy (ELA)** and **Mathematics** across California public schools, school districts, counties, and statewide aggregates from 2015 to the present.

- **Primary Source**: California Department of Education (CDE) / Educational Testing Service (ETS)
- **Research Portal**: [https://caaspp-elpac.ets.org/caaspp/ResearchFileListSB](https://caaspp-elpac.ets.org/caaspp/ResearchFileListSB)
- **Import Tier**: Custom Script StatVar Import (`scripts/us_education/california_school_performance/`)

---

## Directory Structure

```
california_school_performance/
├── config/
│   └── california_school_performance_pvmap.csv        # Property-Value mappings for subjects, grades, and student subgroups
├── test_data/                                         # Test fixtures for offline unit & E2E validation
│   ├── sample_input.txt                               # Sample raw CAASPP input records (State, County, District, School)
│   ├── sample_school_code_mapping.json                # Sample CDS-to-NCES/geoId mapping fixture for unit tests
│   ├── sample_state_output.csv                        # Expected sample CSV observations
│   └── sample_state_output.tmcf                       # Expected sample TMCF mapping
├── download_process_test.py                           # Unit tests for download, normalization, and processing
├── download.py                                        # Automated data fetch and stream normalization script
├── process.py                                         # High-throughput processor generating CSV, TMCF, and counters
├── manifest.json                                      # Data Commons import specification
├── README.md                                          # Documentation and usage guide
└── validation_config.json                             # Production import validation rules
```

> **External GCS Mapping File**: To avoid storing large static lookup files in GitHub, the full 13,713-entry California CDS-to-DCID mapping (`school_code_mapping.json`, ~614 KB) is hosted on GCS at `gs://unresolved_mcf/scripts/us_education/california_school_performance/config/school_code_mapping.json`.

---

## Statistical Variables (StatVars) & Geographic Coverage

The pipeline processes the full California CAASPP dataset across all geographic entities and demographic subgroups:

- **Geographic Coverage (`--keep_all_entities=True`, default)**:
  Includes California statewide (`geoId/06`), all 58 counties (`geoId/06001`–`geoId/06115`), ~1,000 school districts (`geoId/sch06...` and `nces/...`), and ~10,000+ public and charter schools (`nces/06...`), mapped via `school_code_mapping.json` on GCS.
- **Full Demographic Breakdown (`--data_mode=all_groups`, default)**:
  Expands across all 55 demographic subgroups, 8 grade levels (Grades 3–8, 11, and Grade 13 All Grades), 2 subjects, and 7 metrics, mapping to **5,966 canonical Google3 Statistical Variables**.

---

## Place Resolution & Unmapped School Handling (`CA-...` Fallback IDs)

### How California CDS Codes Resolve to Standard DCIDs
Every CAASPP research record identifies its reporting entity with a 14-digit California **County-District-School (CDS)** code triplet:
- `County Code` (2 digits, `00` for Statewide, `01`–`58` for Counties)
- `District Code` (5 digits, `00000` for State/County aggregates)
- `School Code` (7 digits, `0000000` for State/County/District aggregates)

`download.resolve_place_dcid()` zero-pads the CDS triplet into key `CA-{CountyCode}{DistrictCode}-{SchoolCode}` and resolves it against `school_code_mapping.json`:
1. **Statewide (`00`, `00000`, `0000000`)** $\rightarrow$ `geoId/06`
2. **Counties (`01`–`58`, `00000`, `0000000`)** $\rightarrow$ `geoId/06001`–`geoId/06115`
3. **Mapped School Districts & Schools** $\rightarrow$ standard NCES / Census DCIDs (`geoId/sch06...` and `nces/06...`)

### When `CA-...` Fallback Identifiers Arise & Source Metadata Available
When a newly opened California public/charter school or newly formed school district appears in an annual CDE CAASPP release before NCES assigns a 12-digit NCES ID (or before `school_code_mapping.json` is refreshed from NCES Common Core of Data), `resolve_place_dcid()` produces the fallback key `CA-{CountyCode}{DistrictCode}-{SchoolCode}` (for example, `CA-0109884-6987523`).

In the official CAASPP research release archive (`sb_ca<year>entities_csv.txt` distributed alongside `sb_ca<year>_all_csv_v*.txt` on [ResearchFileListSB](https://caaspp-elpac.ets.org/caaspp/ResearchFileListSB)), CDE provides entity metadata for every CDS code, including:
- `County Code`, `District Code`, `School Code`
- `Type ID` (`4` = State, `5` = County, `6` = District, `7` = Direct Funded Charter School, `9` = Locally Funded Charter School, `10` = Public School)
- `County Name`, `District Name`, `School Name`, and `Zip Code`

### Filtering Policy (`--drop_unmapped_places=True`)
Per Data Commons ingestion guidelines:
1. **Stats and Place definitions are kept in separate imports**—statistics imports must not emit new `School` or `SchoolDistrict` place nodes alongside `StatVarObservation` records, and school DCIDs should use standard `nces/` prefixes rather than provisional `CA-...` IDs.
2. **Default Behavior (`--drop_unmapped_places=True`)**: `process.py` filters out observations for unmapped `CA-...` entities (recording `dropped_unmapped_place_rows` and `dropped_unmapped_places` in `counters/california_school_performance_counters.csv`) until those schools/districts are onboarded with `nces/...` DCIDs in the NCES School Place import and `school_code_mapping.json`.
3. **Zero Impact on Aggregates**: CDE/ETS CAASPP research files provide **pre-aggregated** rows independently at the State (`Type ID=4`), County (`Type ID=5`), District (`Type ID=6`), and School (`Type ID=7/9/10`) levels. Neither `download.py` nor `process.py` performs cross-entity aggregation, so filtering unmapped `CA-...` school/district rows does **not** alter any District, County, or Statewide totals, mean scale scores, or proficiency percentages.
4. **Optional Diagnostic Mode (`--drop_unmapped_places=False`)**: For local debugging or entity audits, passing `--drop_unmapped_places=False` retains `CA-...` rows and writes their `School`/`SchoolDistrict` place definitions to a separate `*_places.mcf` file (never mixed with schema or `StatisticalVariable` MCFs).

---

## Schema Dimensions
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
  - English Learner & Fluency Status (`InitialFluentProficient`, `ReclassifiedFluentProficient`, `OnlyEnglish`, `CurrentLearner`, `EverLearned`, `Adult`, `ToBeDetermined`, duration `< 12 months`, duration `>= 12 months`)
  - Parent Education Level (`LessThanHighSchoolGraduate`, `HighSchoolGraduateIncludesEquivalency`, `HighSchoolGraduate`, `SomeCollegeNoDegree`, `CollegeGraduate`, `GraduateSchoolOrPostGraduate`, `CA_DeclinedToState`)
  - Special Student Populations (`Homeless`, `HavingHome`, `Foster`, `NotFoster`, `Migrant`, `NotMigrant`, `FamilyOfArmedForces`, `NotFamilyOfArmedForces`)
- **Metrics**:
  - `Total Students Tested` / `Students Tested`: Count of students (`measuredProperty: count`, `measurementMethod: CaliforniaAssessmentOfStudentPerformanceAndProgress`)
  - `Mean Scale Score`: Mean assessment score (`measuredProperty: assessmentScore`, `statType: meanValue`)
  - `Percentage Standard Exceeded` (`Percentage Advanced` in 2026+): Educational achievement level `CA_StandardExceeded` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Met` (`Percentage Proficient` in 2026+): Educational achievement level `CA_StandardMet` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Met and Above` (`Percentage Proficient and Above` / `Percentage Proficient and Advanced` in 2026+): Educational achievement level `CA_StandardMetAndAbove` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Nearly Met` (`Percentage Developing` in 2026+): Educational achievement level `CA_StandardNearlyMet` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Not Met` (`Percentage Minimal` in 2026+): Educational achievement level `CA_StandardNotMet` (`scalingFactor: 100`, `unit: Percent`)

---

## How to Run

> **Note**: Commands below should be run from `scripts/us_education/california_school_performance/`.

### 1. Download and Process Active Years (`2023–Present`, Default)
Historical data for `2015–2022` (`84.7M` observations) is retained in the `historic/` import folder. By default, `download.py` fetches and normalizes post-2022 years (`--years=2023-present`), automatically discovering new future annual releases (e.g. `2027+`) on the CAASPP portal:
```bash
# Step 1: Download and normalize post-2022 years (default: --years=2023-present)
python3 download.py \
  --school_code_mapping=gs://unresolved_mcf/scripts/us_education/california_school_performance/config/school_code_mapping.json

# Step 2: Generate CSV observations, TMCF, and counters (filtering out unmapped CA-... places)
python3 process.py \
  --input_data=input_files/sb_ca_all_years_normalized.txt \
  --pv_map=config/california_school_performance_pvmap.csv \
  --school_code_mapping=gs://unresolved_mcf/scripts/us_education/california_school_performance/config/school_code_mapping.json \
  --drop_unmapped_places=True \
  --output_path=output_files/california_school_performance_all_years_output \
  --output_counters=counters/california_school_performance_counters.csv
```

### 2. Download All Years (`2015–Present`) or Specific Years
```bash
# All available years (2015-present, skipping 2020)
python3 download.py --years=all

# Specific range
python3 download.py --years=2015-2024

# Specific single year
python3 download.py --years=2024
python3 process.py --input_data=input_files/sb_ca2024_normalized.txt
```

### 3. Quick Test Run
```bash
python3 download.py --test_mode
```

---

## Testing

Run unit tests from repository root:
```bash
./run_tests.sh -p scripts/us_education/california_school_performance
```
Or directly with `unittest`:
```bash
python3 -m unittest scripts/us_education/california_school_performance/download_process_test.py
```

---

## Output Files
The pipeline produces standard Data Commons import artifacts in `output_files/`:
- `california_school_performance_all_years_output.csv`: Complete multi-year `StatVarObservation` table (`geoId/...` and `nces/...` places)
- `california_school_performance_all_years_output.tmcf`: Template MCF linking CSV columns to Data Commons schema properties
- `california_school_performance_places.mcf` *(only emitted when `--drop_unmapped_places=False`)*: Dedicated Place MCF containing only unmapped `CA-...` `School` and `SchoolDistrict` nodes for offline entity audits.
