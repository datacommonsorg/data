# US_Urban_MathsAndScience_Course_Enrollment Import

This import ingests school-level enrollment counts in Advanced Mathematics, Algebra II, Biology, Calculus, Chemistry, Geometry, and Physics from the US Department of Education Civil Rights Data Collection at `https://civilrightsdata.ed.gov/data`.

## Dataset coverage and files

- **Survey years**: `2009-10`, `2011-12`, `2015-16`, `2017-18`, `2020-21`, `2021-22`, and `2023-24`, with automatic probing for newer CRDC survey releases.
- **Refresh mode**: Automated Cloud Batch refresh configured in `manifest.json`.
- **Key files**:
  - `download.py`: Streams CRDC ZIP archives, verifies ZIP integrity inside retry loops, adds `YEAR` and `ncesid` columns, and reuses existing files only when upstream `ETag` or `Last-Modified` HTTP headers match.
  - `run.sh`: Stages `stat_vars.mcf` locally once, checks that all required and discovered survey-year partitions exist, and runs `stat_var_processor.py` across all 9 output splits.
  - `maths_and_science_pvmap.csv` and `metadata.csv`: Property-value mappings and processor settings, including `JJ` and `SCH_JUST` institution-type mappings and `*_LEP_*` and `*_EL_*` English learner mappings.
  - `validation_config.json`: Enforces split-wide `MaxDate` consistency and freshness rules alongside the inherited `0.1%` deleted-records threshold.
  - `download_test.py`: Unit tests for downloads, manifest resolution, `run.sh` guards, PV map coverage, and validation rules.
  - `test_data/`: Sample input CSVs and expected `.csv`, `.tmcf`, and StatVar `.mcf` fixtures for verifying mappings directly with `stat_var_processor.py`.

## Prerequisites

Create and populate the repository Python environment from the repository root before running scripts locally:

```bash
./run_tests.sh -r
```

Run the commands below from `statvar_imports/us_urban_school/maths_and_science_enrollment` unless noted otherwise.

## Workflow

### Step 1: Download the source data

```bash
../../../.env/bin/python download.py
```

Pass `--force_download` to re-download and overwrite files in `input_files/` without checking upstream HTTP `ETag` or `Last-Modified` headers:

```bash
../../../.env/bin/python download.py --force_download
```

### Step 2: Process the files

#### Option A: Run `run.sh`

```bash
source ../../../.env/bin/activate
bash run.sh
```

Set `EXISTING_STATVAR_MCF=/path/to/stat_vars.mcf` to use a pre-staged local StatVar MCF file instead of downloading `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`.

#### Option B: Run `stat_var_processor.py` manually

From `tools/statvar_importer/`, run the nine split commands below after creating `output_files/` and `counters/` inside the import directory:

```bash
# 1. Process 2010 and 2012 XLSX files
../../.env/bin/python stat_var_processor.py \
  --input_data="../../statvar_imports/us_urban_school/maths_and_science_enrollment/input_files/2010_*.xlsx,../../statvar_imports/us_urban_school/maths_and_science_enrollment/input_files/2012_*.xlsx" \
  --pv_map="../../statvar_imports/us_urban_school/maths_and_science_enrollment/maths_and_science_pvmap.csv" \
  --config_file="../../statvar_imports/us_urban_school/maths_and_science_enrollment/metadata.csv" \
  --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" \
  --output_path="../../statvar_imports/us_urban_school/maths_and_science_enrollment/output_files/maths_and_science_2010_2012_output" \
  --output_counters="../../statvar_imports/us_urban_school/maths_and_science_enrollment/counters/maths_and_science_2010_2012_counters.csv" \
  --recon_property=variableMeasured

# 2. Process 2016 School_data CSV
../../.env/bin/python stat_var_processor.py \
  --input_data="../../statvar_imports/us_urban_school/maths_and_science_enrollment/input_files/2016_School_data.csv" \
  --pv_map="../../statvar_imports/us_urban_school/maths_and_science_enrollment/maths_and_science_pvmap.csv" \
  --config_file="../../statvar_imports/us_urban_school/maths_and_science_enrollment/metadata.csv" \
  --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" \
  --output_path="../../statvar_imports/us_urban_school/maths_and_science_enrollment/output_files/maths_and_science_2016_output" \
  --output_counters="../../statvar_imports/us_urban_school/maths_and_science_enrollment/counters/maths_and_science_2016_counters.csv" \
  --recon_property=variableMeasured

# 3. Process 2018 onwards CSVs per course
for spec in \
  "Advanced_Mathematics:advanced_mathematics_2018_onwards_output" \
  "Algebra_II:algebra2_2018_onwards_output" \
  "Biology:biology_2018_onwards_output" \
  "Calculus:calculus_2018_onwards_output" \
  "Chemistry:chemistry_2018_onwards_output" \
  "Geometry:geometry_2018_onwards_output" \
  "Physics:physics_2018_onwards_output"; do
  suffix="${spec%%:*}"
  out="${spec##*:}"
  ../../.env/bin/python stat_var_processor.py \
    --input_data="../../statvar_imports/us_urban_school/maths_and_science_enrollment/input_files/*_${suffix}.csv" \
    --pv_map="../../statvar_imports/us_urban_school/maths_and_science_enrollment/maths_and_science_pvmap.csv" \
    --config_file="../../statvar_imports/us_urban_school/maths_and_science_enrollment/metadata.csv" \
    --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" \
    --output_path="../../statvar_imports/us_urban_school/maths_and_science_enrollment/output_files/${out}" \
    --output_counters="../../statvar_imports/us_urban_school/maths_and_science_enrollment/counters/${out}_counters.csv" \
    --recon_property=variableMeasured
done
```

## Validation and testing

Run the unit tests from the repository root:

```bash
./run_tests.sh -p statvar_imports/us_urban_school/maths_and_science_enrollment
```

To verify `test_data/*_input.csv` against `test_data/maths_and_science_output.csv` and `test_data/maths_and_science_output.tmcf` directly with `stat_var_processor.py` from the repository root:

```bash
out_dir=$(mktemp -d)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/us_urban_school/maths_and_science_enrollment/test_data/*_input.csv" \
  --pv_map="statvar_imports/us_urban_school/maths_and_science_enrollment/maths_and_science_pvmap.csv" \
  --config_file="statvar_imports/us_urban_school/maths_and_science_enrollment/metadata.csv" \
  --existing_statvar_mcf="statvar_imports/us_urban_school/maths_and_science_enrollment/test_data/maths_and_science_output_stat_vars.mcf" \
  --output_path="${out_dir}/maths_and_science_output" \
  --recon_property=variableMeasured
diff -u statvar_imports/us_urban_school/maths_and_science_enrollment/test_data/maths_and_science_output.csv "${out_dir}/maths_and_science_output.csv"
diff -u statvar_imports/us_urban_school/maths_and_science_enrollment/test_data/maths_and_science_output.tmcf "${out_dir}/maths_and_science_output.tmcf"
rm -rf "${out_dir}"
```

To run the import validation rules locally against generated GenMCF and differ artifacts from the repository root:

```bash
.env/bin/python -m tools.import_validation.runner \
  --validation_config=statvar_imports/us_urban_school/maths_and_science_enrollment/validation_config.json \
  --stats_summary=<path_to_summary_report.csv> \
  --lint_report=<path_to_report.json> \
  --differ_output=<path_to_differ_dir> \
  --validation_output=<path_to_validation_output.csv>
```
