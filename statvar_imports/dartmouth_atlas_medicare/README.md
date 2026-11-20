# Dartmouth Atlas Medicare (`Dartmouth_Atlas_Medicare`)

Automated Data Commons import (`b/579416962`) for Medicare enrollee counts,
price-adjusted reimbursements per enrollee, Medicare Part A/B enrollees, and
diabetic enrollee counts from the
[Dartmouth Atlas of Health Care](https://data.dartmouthatlas.org/).

## 1. Overview & Coverage

- **Import Name**: `Dartmouth_Atlas_Medicare`
- **Source Portal**: <https://data.dartmouthatlas.org/>
- **Provenance DCID**: `dc/base/Dartmouth_Atlas_Medicare`
- **Release Frequency / Refresh Schedule**: Weekly check (`0 5 * * 1`, `P1Y`
  annual observations)
- **Active StatVars (`10` total — 100% parity with live KG)**:
  - `Count_MedicareEnrollee` (`1999–2019+`)
  - `dc/rn90czcrqcv06` (*Mean Price Of Medicare Enrollee*, Total
    `priceAgeSexRace`, `2003–2019+`)
  - `Count_MedicareEnrollee_MedicareA`,
    `Count_MedicareEnrollee_MedicareA_Black`,
    `Count_MedicareEnrollee_MedicareA_NonBlack` (`2007–2014` historical)
  - `Count_MedicareEnrollee_MedicareB`,
    `Count_MedicareEnrollee_MedicareB_Black`,
    `Count_MedicareEnrollee_MedicareB_NonBlack` (`2007–2019+`)
  - `Count_MedicareEnrollee_ConditionDiabetic_Black`,
    `Count_MedicareEnrollee_ConditionDiabetic_NonBlack` (`2007–2019+`)
- **Geographic Levels**: Country (`country/USA`), States (`geoId/XX`), Counties
  (`geoId/XXXXX`, including retired Alaska county FIPS preserved in historical
  data), and HRR/HSA Cities/Towns/Villages/Neighborhoods (`1999–2015`
  historical `Count_MedicareEnrollee`).
- **Temporal Granularity**: Annual (`observationPeriod: P1Y`).

## 2. Datasets & Architecture

This import combines a consolidated historical baseline (`1999–2016`) staged in
GCS with live Dartmouth Atlas longitudinal ZIP archives (`2003–2019+`) so
subsequent automated iterations preserve 100% of historical series (`0%`
deletions) while ingesting new upstream years automatically:

1. **Consolidated Historical Baseline in GCS (`1999–2016`)**:
   - `gs://unresolved_mcf/dartmouth_atlas_medicare/historical/dartmouth_atlas_medicare_historical_1999_2016.csv`
   - Built once via `consolidate_historical.py` from the 6 active resolved CNS
     tables under `/cns/jv-d/home/datcom/v3_resolved_mcf/dartmouth_atlas/stat_pop/`
     (`dartmouth_reim_count`, `dartmouth_reim`, `dartmouth_num_overall`,
     `dartmouth_num_enrollees`, `dartmouth_num_diabetics`,
     `dartmouth_mortality_count`; `cl/954587569`, `b/527799466`).
   - Preserves all 10 production StatVars (including `MedicareA*` `2007–2014`,
     year `2007` for Part B & Diabetic, `1999–2002` + ~3,300 resolved HRR/HSA
     City/Town/Village places for `Count_MedicareEnrollee`, and retired Alaska
     FIPS `geoId/02201`, `geoId/02270`).
   - Copied automatically by `download.py` into `output_files/` along with
     `output_files/common_tmcf.tmcf` on every run.
2. **Live Upstream Archives (`https://data.dartmouthatlas.org/downloads/`)**:
   - `research_files/county_stdprices_2003_2010.csv.zip` (`2003–2010` county
     enrollees & Total price-adjusted reimbursements)
   - `research_files/county_stdprices_ffs.csv.zip` (`2011–2019+` county
     enrollees & Total price-adjusted reimbursements)
   - `research_files/state_stdprices_2003_2010.csv.zip` (`2003–2010` state &
     USA enrollees & Total price-adjusted reimbursements)
   - `research_files/state_stdprices_ffs.csv.zip` (`2011–2019+` state & USA
     enrollees & Total price-adjusted reimbursements)
   - `research_files/county_hedis_6575ffs.csv.zip` (`2008–2019+` county Part B
     & diabetic enrollees by race)
   - `research_files/state_hedis_6575ffs.csv.zip` (`2008–2019+` state & USA
     Part B & diabetic enrollees by race)
   - On every run, `download.py` deduplicates live observations against keys
     already present in the historical CSV so only net-new `(date, place,
     stat_var)` observations are passed to `stat_var_processor.py`.

## 3. Directory Layout

- `consolidate_historical.py`: One-time consolidation script reading the 6
  active CNS `stat_pop/` resolved MCF tables into
  `dartmouth_atlas_medicare_historical_1999_2016.csv`, `common_tmcf.tmcf`, and
  deduplicated `dartmouth_atlas_medicare_historical_1999_2016.mcf`.
- `download.py`: Copies the consolidated historical CSV from GCS into
  `output_files/`, writes `output_files/common_tmcf.tmcf`, downloads raw ZIP
  archives into `input_files/raw/`, skips `__MACOSX/` metadata entries, handles
  UTF-8 BOM and header casing variations, filters `NaN`/suppressed/`-88888`/
  `-99999` values (`b/152544134`), maps CMS/SSA state codes (`01`–`53`) to US
  Census FIPS DCIDs (`geoId/01`–`geoId/56`), maps national codes (`99`/`99999`)
  to `country/USA`, drops residual non-FIPS county codes (`99003`, `999999`),
  deduplicates against historical keys, and writes net-new rows to
  `input_files/cleaned/dartmouth_atlas_medicare.csv`.
- `dartmouth_atlas_medicare_pvmap.csv`: PVMap for `stat_var_processor.py`.
- `dartmouth_atlas_medicare_metadata.csv`: Processor config
  (`observationPeriod: P1Y`).
- `dartmouth_statvar_remap.csv`: Maps generated StatVar DCIDs to existing KG
  DCIDs (including `dc/rn90czcrqcv06` and `DAD_Black`/`DAD_NonBlack` remaps).
- `manifest.json`: Import automation specification (`cron_schedule`, combined
  historical + fresh `import_inputs`, `source_files`, `validation_config_file`).
- `validation_config.json`: SQL and range validation rules across all 10
  StatVars.
- `download_test.py` & `test_data/`: Unit tests (for `download.py` and
  `consolidate_historical.py`) and `stat_var_processor.py` test fixtures.

## 4. One-Time Historical Staging (Prerequisites)

Run once from `statvar_imports/dartmouth_atlas_medicare/` on a gLinux machine
with valid `gcert` credentials:

```bash
# 1. Consolidate the 6 active CNS tables (1999-2016)
python3 consolidate_historical.py \
  --cns_dir=/cns/jv-d/home/datcom/v3_resolved_mcf/dartmouth_atlas/stat_pop \
  --output_dir=historical

# 2. Upload consolidated historical CSV to GCS for automated runs
gcloud storage cp \
  historical/dartmouth_atlas_medicare_historical_1999_2016.csv \
  gs://unresolved_mcf/dartmouth_atlas_medicare/historical/

# 3. (Optional) Stage deduplicated baseline MCF in datcom-import-test for differ
gcloud storage cp \
  historical/dartmouth_atlas_medicare_historical_1999_2016.mcf \
  gs://datcom-import-test/statvar_imports/dartmouth_atlas_medicare/Dartmouth_Atlas_Medicare/2026_07_21_prod_baseline/input0/genmcf/
printf "%s" "2026_07_21_prod_baseline" | gcloud storage cp - \
  gs://datcom-import-test/statvar_imports/dartmouth_atlas_medicare/Dartmouth_Atlas_Medicare/latest_version.txt
```

## 5. Running Locally & Testing

From the repository root (`data/`):

```bash
# 1. Run unit tests
./run_tests.sh -p statvar_imports/dartmouth_atlas_medicare

# 2. Download historical baseline + live upstream archives
cd statvar_imports/dartmouth_atlas_medicare
python3 download.py \
  --output_dir=input_files \
  --historical_output_dir=output_files

# 3. Process net-new live observations with stat_var_processor.py
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/cleaned/*.csv \
  --pv_map=dartmouth_atlas_medicare_pvmap.csv \
  --config_file=dartmouth_atlas_medicare_metadata.csv \
  --statvar_dcid_remap_csv=dartmouth_statvar_remap.csv \
  --output_path=output_files/dartmouth_atlas_medicare_output \
  --output_counters=counters/dartmouth_atlas_medicare_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

*(For local runs without GCS access to `gs://unresolved_mcf`, pass
`--historical_gcs_dir=historical` to `download.py` and omit
`--existing_statvar_mcf` from `stat_var_processor.py`.)*

## 6. Post-PR Piper Cutover Checklist

After PR merge and the first successful production run under
`gs://datcom-prod-imports/statvar_imports/dartmouth_atlas_medicare/Dartmouth_Atlas_Medicare/`,
submit a google3 CL updating:

- `//depot/google3/datacommons/import/mcf/manifest/us_stats/Dartmouth_Atlas_Medicare.textproto`
  (`end_date_in_kg: "2019"`, `provenance_url` / `data_download_url: "https://data.dartmouthatlas.org/"`, `automated_mcf_generation_by`, and `/bigstore/datcom-prod-imports/...` paths)
- `//depot/google3/datacommons/import/mcf/resolved_mcf/import/Dartmouth_Atlas_Medicare.mcf`
  (`lastDataRefreshDate`, `sourceDataUrl`, `automaticRefreshType`, `automatedRefreshFrequency`)
- `//depot/google3/datacommons/import/mcf/encode_mcfs.textproto`
