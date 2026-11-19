# Dartmouth Atlas Medicare (`Dartmouth_Atlas_Medicare`)

Automated Data Commons import for Medicare enrollee counts, price-adjusted
reimbursements per enrollee, Part B enrollees, and diabetic enrollee counts
from the [Dartmouth Atlas of Health Care](https://data.dartmouthatlas.org/).

## Source & Coverage

- **Source Portal**: <https://data.dartmouthatlas.org/>
- **Provenance DCID**: `dc/base/Dartmouth_Atlas_Medicare`
- **Upstream Archives**:
  - `research_files/county_stdprices_2003_2010.csv.zip` (2003–2010 county enrollees & price-adjusted reimbursements)
  - `research_files/county_stdprices_ffs.csv.zip` (2011–2019 county enrollees & price-adjusted reimbursements)
  - `research_files/state_stdprices_2003_2010.csv.zip` (2003–2010 state & USA enrollees & price-adjusted reimbursements)
  - `research_files/state_stdprices_ffs.csv.zip` (2011–2019 state & USA enrollees & price-adjusted reimbursements)
  - `research_files/county_hedis_6575ffs.csv.zip` (2008–2019 county Part B & diabetic enrollees by race)
  - `research_files/state_hedis_6575ffs.csv.zip` (2008–2019 state & USA Part B & diabetic enrollees by race)
  - `tables/state_mortality_2019.csv.zip` (2019 state & USA Medicare enrollees)
- **Geographic Levels**: Country (`country/USA`), States (`geoId/XX`), and Counties (`geoId/XXXXX`).
- **Temporal Granularity**: Annual (`P1Y`), `2003–2019` (with `2008–2019` for primary care Part B and diabetic cohorts).

## Directory Layout

- `download.py`: Downloads raw ZIP archives into `input_files/raw/`, skips `__MACOSX/` metadata entries, handles UTF-8 BOM and case variations, filters `NaN`/suppressed cells (`b/152544134`), zero-pads FIPS codes (`geoId/01001`, `geoId/01`, `country/USA`), and writes normalized CSV rows to `input_files/cleaned/dartmouth_atlas_medicare.csv`.
- `dartmouth_atlas_medicare_pvmap.csv`: PVMap for `stat_var_processor.py`.
- `dartmouth_atlas_medicare_metadata.csv`: Processor config (`observationPeriod: P1Y`).
- `dartmouth_statvar_remap.csv`: Maps generated StatVar DCIDs to existing KG DCIDs (including `dc/rn90czcrqcv06`).
- `manifest.json`: Import automation specification (`cron_schedule`, `import_inputs`, `source_files`, `validation_config_file`).
- `validation_config.json`: SQL and range validation rules for `summary_report.csv`.
- `download_test.py` & `test_data/`: Unit tests and `stat_var_processor` test fixtures.

## Running Locally

From the repository root (`data/`):

```bash
# 1. Run unit tests
./run_tests.sh -p statvar_imports/dartmouth_atlas_medicare

# 2. Download and preprocess
python3 statvar_imports/dartmouth_atlas_medicare/download.py

# 3. Run stat_var_processor
cd statvar_imports/dartmouth_atlas_medicare
../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/cleaned/*.csv \
  --pv_map=dartmouth_atlas_medicare_pvmap.csv \
  --config_file=dartmouth_atlas_medicare_metadata.csv \
  --statvar_dcid_remap_csv=dartmouth_statvar_remap.csv \
  --output_path=output_files/dartmouth_atlas_medicare_output \
  --output_counters=counters/dartmouth_atlas_medicare_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```
