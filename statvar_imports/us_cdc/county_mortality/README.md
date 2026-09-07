### CDC WONDER County-Level Mortality Across All Causes (`CDC_Mortality_Count`)

This import acquires and processes county-level mortality statistics across all causes of death (ICD-10 113 Cause List) for all 50 US States and Washington D.C. from the CDC WONDER database.

- **Import Name**: `CDC_Mortality_Count`
- **Source Database**: CDC WONDER Underlying Cause of Death (Database D158)
- **Source URL**: `https://wonder.cdc.gov/ucd-icd10-expanded.html`
- **Geographic Granularity**: County level (all ~3,143 US counties across all states)
- **Temporal Coverage**: 2018 to 2024 (P1Y frequency)
- **Cause Coverage**: All diseases in the ICD-10 113 Cause List (e.g. Septicemia, Diabetes Mellitus, Major Cardiovascular Diseases, Alzheimer's, Malignant Neoplasms, Respiratory Diseases, etc.)

---

### Workflow

The import consists of two fully automated steps:

#### Step 1: Download Source Data
```bash
python3 download.py
```
or with specific flags:
```bash
python3 download.py --states=all --years=2018-2024 --output_dir=input_files
```
The download script automatically handles CDC WONDER sessions, agreements, rate-limiting backoffs, and query partitioning.

#### Step 2: Process Data into Cleaned SVObs and TMCF
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --input_data=input_files/*.csv \
  --pv_map=county_mortality_pvmap.csv \
  --config_file=county_mortality_metadata.csv \
  --output_path=output/underlyingcauseofdeath_county
```

#### Output Artifacts
* `output/underlyingcauseofdeath_county.csv`: Cleaned observations mapping FIPS (`geoId/{fips}`), year, StatVar (`Count_MortalityEvent_<Cause>`), and death count.
* `output/underlyingcauseofdeath_county.tmcf`: Template MCF mapping CSV columns to Data Commons Knowledge Graph entities.
