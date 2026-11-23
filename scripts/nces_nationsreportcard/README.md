# NCES Nation's Report Card (NAEP) Import

## Overview

This directory contains the automated ingestion pipeline for the **NCES_NationsReportCard** Data Commons import, sourcing student educational performance statistics from the U.S. Department of Education's National Center for Education Statistics (NCES) **National Assessment of Educational Progress (NAEP)** — *The Nation's Report Card*.

- **Source Website**: https://nces.ed.gov/nationsreportcard/
- **API Endpoint**: `https://www.nationsreportcard.gov/Dataservice/GetAdhocData.aspx`
- **License**: Public Domain (`https://ies.ed.gov/about/privacy-security`)

## Dataset Coverage

- **Input Files (`16` CSVs)**:
  - **12 National datasets** (`naep_national_<subject>.csv`): Civics (`CIV`), Economics (`ECN`), Geography (`GEO`), U.S. History (`HIS`), Mathematics (`MAT`), Music (`MUS`), Reading (`RED`), Science (`SCI`), Technology and Engineering Literacy (`TEL`), Visual Arts (`VIS`), Vocabulary (`VOC`), and Writing (`WRI`).
  - **4 State datasets** (`naep_state_<subject>.csv`): Mathematics (`MAT`), Reading (`RED`), Science (`SCI`), and Writing (`WRI`).
- **Grades**: Grades 4, 8, and 12 (depending on subject availability).
- **Reporting Sample & Temporal Coverage**: Standard reporting sample (`R3`) across all available assessment cycles (new assessment years are discovered automatically when omitting `Year` or via dynamic descending-year probes).
- **Geographic Coverage**: National (`country/USA` across overall `NT`, public `NP`, and private `NR` sectors) plus U.S. states, District of Columbia (`DC`), American Samoa (`AS`), Guam (`GU`), Puerto Rico (`PR`), and U.S. Virgin Islands (`VI`).
- **Metrics (`stattype`) & Subgroups (`variable`)**:
  - Scale score mean (`MN:MN`), standard deviation (`SD:SD`), and percentiles (`PC:P1`, `PC:P2`, `PC:P5`, `PC:P7`, `PC:P9`) across composite scales and content subscales.
  - Discrete (`ALD:BA`, `ALD:PR`, `ALD:AD`) and cumulative (`ALC:BB`, `ALC:AB`, `ALC:AP`, `ALC:AD`) NAEP achievement-level student percentages (composite scales).
  - Student subgroup population share (`RP:RP`).
  - Disaggregations by sex (`GENDER`), race/ethnicity (`SRACE10`), National School Lunch Program eligibility (`SLUNCH3`), school type/management (`SCHTYPE`), charter status (`CHRTRPT`), urban-centric locale (`UTOL4`), disability status (`IEP`), and English learner status (`LEP`).

## Prerequisites & Working Directory

Run commands from the repository root (`data/`) or from `scripts/nces_nationsreportcard/` using the repository Python virtual environment (`.env`, initialized via `./run_tests.sh -r`). All script paths resolve relative to `scripts/nces_nationsreportcard/` (`MODULE_DIR`).

## Pipeline Steps

### 1. Download Raw Input Files (`download_input_files.py`)

```bash
python3 scripts/nces_nationsreportcard/download_input_files.py
```

Optional flags:
- `--output_dir`: Target directory for downloaded CSVs (defaults to `scripts/nces_nationsreportcard/input_files`).
- `--files`: Comma-separated subset of CSV filenames to download (defaults to all 16 files).
- `--max_workers`: Concurrent HTTP worker threads (default: `8`).
- `--read_timeout`: Per-request read timeout in seconds (default: `120`).

Key download behaviors:
- Queries all available `R3` assessment years automatically without hardcoded year cutoffs.
- Uses warm-gated concurrency per content subscale to avoid cold-cache timeouts on NCES's SQL backend, 15-state pilot fallback for Grade 12 state Reading, 7-batch state fallback if any 55-state composite query stalls, and explicit descending-year retries when a subscale triggers NCES's `GetDependentInfo` HTTP 400 bug on legacy `R2` cycles.
- Writes each CSV atomically via temporary file + `os.replace` so partial downloads are never exposed, leaving raw API values unmodified on disk.

### 2. Process & Generate Clean CSV / TMCF / StatVar MCF (`process.py`)

```bash
python3 scripts/nces_nationsreportcard/process.py \
  --input_data=scripts/nces_nationsreportcard/input_files/*.csv \
  --pv_map=scripts/nces_nationsreportcard/config/pv_map.py,jurisdiction:scripts/nces_nationsreportcard/config/jurisdiction_map.py \
  --config_file=scripts/nces_nationsreportcard/config/naep_conf.py \
  --output_path=scripts/nces_nationsreportcard/output/naep_performance \
  --output_counters=scripts/nces_nationsreportcard/counters/naep_performance_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

Key custom transformations in `NaepEduPerformance` (`process.py`):
- **Suppressed Cell Filtering**: Drops NCES sentinel values (`999`, `999.0`, empty) and rows with `isStatDisplayable == 0` at runtime without mutating `input_files/*.csv`.
- **Redundant Cross-Product Filtering (`is_redundant_naep_row`)**: Excludes three mathematically redundant/tautological combinations:
  1. `NP`/`NR`/`NL` × `SCHTYPE` (double-tags `schoolType` and `schoolManagement`).
  2. `NR`/`NL` × `CHRTRPT` (tautological private school × non-charter status, identical to `NR` + `TOTAL`).
  3. `TOTAL` × `RP:RP` (constant `100%` "All students" row percentage).
- **Denominator StatVar Registration**: Automatically synthesizes and links `dcid:Count_Student_*` `measurementDenominator` StatisticalVariables for all `educationalAchievementLevel` (`ALC:*` and `ALD:*`) observations.
- **Memoized Fast Path**: Caches resolved StatVar templates per `(CohortLabel, stattype, subject, scale, sector_jurisdiction, varValueLabel)` across states and years while preserving full floating-point precision.

## Important Files

- `manifest.json`: Cloud Batch / Cloud Run auto-refresh import specification (`NCES_NationsReportCard`).
- `download_input_files.py` & `download_input_files_test.py`: Concurrent NAEP Data Service downloader and offline unit tests.
- `process.py` & `process_test.py`: `NaepEduPerformance` custom processor subclass and unit tests.
- `config/pv_map.py`: Property-value mappings for `stattype`, `subject`, `CohortLabel`, `scale`, `varValueLabel`, and `value`.
- `config/jurisdiction_map.py`: National (`NT`, `NP`, `NR`, `NL`) and state/territory (`geoId/*`) mappings.
- `config/naep_conf.py` & `config/conf.py`: Processor configuration and denominator property exclusion list.
- `test_data/`: Paired sample input (`naep_input.csv`) and expected processor outputs (`naep_output.csv`, `naep_output.tmcf`).

## Testing

From the repository root (`data/`), run the unit tests with:

```bash
./run_tests.sh -p scripts/nces_nationsreportcard
```

## Refresh Procedure

This import is configured for automated Cloud Run / Cloud Batch execution via `manifest.json` on schedule `"0 07 * * 3"` (weekly on Wednesdays at 07:00 UTC), executing `download_input_files.py` followed by `process.py` and emitting `output/naep_performance.csv`, `output/naep_performance.tmcf`, and `output/*.mcf`.
