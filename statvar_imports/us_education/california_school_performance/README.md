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
│   └── california_school_performance_stat_vars.mcf    # Predefined StatisticalVariable nodes (5,966 variables)
├── download.py                                        # Automated data fetch and extraction script
├── run_download_process.sh                            # End-to-end download & stat_var_processor pipeline runner
├── manifest.json                                      # Data Commons import specification
├── README.md                                          # Documentation and usage guide
├── input_files/                                       # Raw downloaded files (sb_ca*.txt, StudentGroups.txt, etc.)
├── output_files/                                      # Generated CSV, TMCF, and MCF outputs
└── test_data/                                         # Test input samples and verified outputs
```

---

## Statistical Variables (StatVars)

The pipeline maps raw test records into **5,966 distinct Statistical Variables** conforming to the Data Commons education schema:

- **Population Type**: `Student`
- **School Subjects**:
  - `EnglishLanguageArts` (Test ID: 1)
  - `Mathematics` (Test ID: 2)
- **Grade Levels**:
  - Grades 3, 4, 5, 6, 7, 8, 11 (`dcid:SchoolGrade3` – `dcid:SchoolGrade11`)
  - Grade 13 representing "All Grades combined" (`dcid:SchoolGrade13`)
- **Demographic Subgroups (55 groups)**:
  - Gender (`Male`, `Female`)
  - Race / Ethnicity (`White`, `BlackOrAfricanAmericanAlone`, `Asian`, `Filipino`, `HispanicOrLatino`, `AmericanIndianOrAlaskaNative`, `NativeHawaiianOrOtherPacificIslanderAlone`, `TwoOrMoreRaces`)
  - Socioeconomic Status (`EconomicallyDisadvantaged`, `NotEconomicallyDisadvantaged`)
  - Intersection of Race × Socioeconomic Status (16 groups)
  - Disability Status (`WithDisability`, `NoDisability`)
  - English Learner & Fluency Status (`InitialFluentProficient`, `ReclassifiedFluentProficient`, `OnlyEnglish`, `CurrentLearner`, `EverLearned`, `Adult`, `ToBeDetermined`, duration `< 12 months`, duration `>= 12 months`)
  - Parent Education Level (`LessThanHighSchoolGraduate`, `HighSchoolGraduateIncludesEquivalency`, `SomeCollegeNoDegree`, `CollegeGraduate`, `GraduateSchoolOrPostGraduate`, `CA_DeclinedToState`)
  - Special Student Populations (`Homeless`, `HavingHome`, `Foster`, `NotFoster`, `Migrant`, `NotMigrant`, `FamilyOfArmedForces`, `NotFamilyOfArmedForces`)
- **Metrics**:
  - `Total Students Tested with Scores`: Count of students (`measuredProperty: count`)
  - `Mean Scale Score`: Mean assessment score (`measuredProperty: assessmentScore`, `statType: meanValue`)
  - `Percentage Standard Exceeded`: Educational achievement level `CA_StandardExceeded` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Met`: Educational achievement level `CA_StandardMet` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Met and Above`: Educational achievement level `CA_StandardMetAndAbove` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Nearly Met`: Educational achievement level `CA_StandardNearlyMet` (`scalingFactor: 100`, `unit: Percent`)
  - `Percentage Standard Not Met`: Educational achievement level `CA_StandardNotMet` (`scalingFactor: 100`, `unit: Percent`)

---

## How to Run

### 1. Download and Process the Entire Dataset (All Available Years: 2015–2025)
To download and process all years present at source (skipping 2020 when CAASPP was cancelled statewide due to COVID-19):
```bash
./run_download_process.sh --years=all
```
This automatically fetches each year, normalizes differences across formats, and runs `stat_var_processor.py` over the consolidated multi-year dataset (`sb_ca_all_years_normalized.txt`), generating **64,000+ observations** across all 10 years.

### 2. Download and Process Specific Years
To fetch and process specific years:
```bash
# Specific range
./run_download_process.sh --years=2015-2024

# Specific single year
./run_download_process.sh --years=2024
```

### 3. Quick Test Run
To download a lightweight test sample and verify the pipeline:
```bash
./run_download_process.sh --test_mode
```

---

## Output Files
The pipeline produces standard Data Commons import artifacts in `output_files/`:
- `california_school_performance_all_years_output.csv`: Complete multi-year observations table (~64,000 rows across 2015–2025)
- `california_school_performance_all_years_output.tmcf`: Template MCF linking columns to Data Commons schema nodes
- `california_school_performance_{YEAR}_output.csv`: Per-year individual observation tables

