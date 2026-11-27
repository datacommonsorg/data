# India Water Resources Information System (WRIS) Water Quality Import

## 1. Overview & Dataset Coverage

- **Import Name**: `IndiaWRISWaterQuality`
- **Source**: [India Water Resources Information System (WRIS)](https://indiawris.gov.in/wris/#/DataDownload)
- **Publisher**: National Water Informatics Centre (NWIC), Ministry of Jal Shakti (aggregating Central Ground Water Board (CGWB) and Central Water Commission (CWC) monitoring stations)
- **Import Mode**: **Semi-Automated** (`cron_schedule: "0 4 * * 1"` — weekly Monday 04:00 UTC). Because `indiawris.gov.in` is geo-fenced to Indian IP addresses and gated by interactive CAPTCHA and email export (`b/579716190`), raw source CSVs are manually staged to `gs://unresolved_mcf/india_wris/water_quality/input_files/` and downloaded unchanged by `download.py`.
- **Processing**: Exclusively via `tools/statvar_importer/stat_var_processor.py` (no custom Python transformation scripts).
- **Datasets & Observation Coverage**:
  - **Ground Water Quality (`groundWater.csv`)**: `2000-05` to `2023-04` (`P1Y` observation period across 27 chemical and trace-element parameters).
  - **Ground Water Quality Retained (`India_WRIS_Ground_Prod_Retained.csv`)**: `2000` to `2018` (`P1Y` observation period retaining historical station series dropped from newer upstream exports).
  - **Surface Water Quality (`surfaceWater.csv`)**: `2001-01` to `2020-03` (`P1M` observation period across 27 chemical and trace-element parameters).
- **Place / Entity Resolution**:
  - Monitoring station entities (`typeOf: dcs:WaterQualitySite`) use DCIDs of the form `indiaWris/<LGD_DistrictCode>_<StationName>`, resolved through `india_wris_districts_pvmap.csv` and `#Eval` expressions inside the PV maps, and emitted alongside `StatVarObservation` nodes via `output_tmcf`.

## 2. Directory Layout & Important Files

| File / Directory | Purpose |
| :--- | :--- |
| `manifest.json` | Import specification declaring `download.py`, 3 `stat_var_processor.py` commands, `import_inputs`, `source_files`, `cron_schedule`, and `validation_config.json`. |
| `download.py` | Atomically copies manually staged CSV files from `gs://unresolved_mcf/india_wris/water_quality/input_files/` into `input_files/` unchanged. |
| `download_test.py` | Hermetic unit tests for `download.py` and `test_data/` fixture size/row bounds. |
| `india_wris_districts_pvmap.csv` | Shared District Name -> LGD District Code PV map (including historical district spelling normalizations) reused by Ground and Surface Water runs. |
| `ground_water_pvmap.csv` | Property-value mappings for the 27 Ground Water Quality parameters, station/date columns, and state/station overrides (`BijapurCode`, `Kodarma` -> `Koderma`). |
| `ground_water_statvar_processor_config.json` | StatVar Processor config for Ground Water (`mapped_columns`, `aggregate_duplicate_svobs='last'`, and `WaterQualitySite` `output_tmcf`). |
| `ground_water_retained_pvmap.csv` | Property-value mappings for the 21 retained historical Ground Water StatVars. |
| `ground_water_retained_statvar_processor_config.json` | StatVar Processor config for the retained Ground Water CSV. |
| `surface_water_pvmap.csv` | Property-value mappings for the 27 Surface Water Quality parameters, station/date columns, and state/station overrides (`BijapurCode`, `Kodarma` -> `Koderma`). |
| `surface_water_statvar_processor_config.json` | StatVar Processor config for Surface Water (`mapped_columns`, `aggregate_duplicate_svobs='last'`, and `WaterQualitySite` `output_tmcf`). |
| `statvar_remap.csv` | Remaps 44 generated StatVar DCIDs to canonical KG DCIDs: 43 `Concentration_BodyOfWater_<Contaminant>_*` -> `Concentration_<Contaminant>_BodyOfWater_*` mappings (including `Dioxosilane` -> `SiliconDioxide` and `ZincElement` -> `Zinc`) plus `Concentration_BodyOfWater_Oxygen_Water_SurfaceWater` -> `DissolvedOxygen_BodyOfWater_SurfaceWater`. |
| `validation_config.json` | Scoped `SQL_VALIDATOR` date-freshness and completeness rules plus `DELETED_ENTITY_COUNT`. |
| `test_data/` | Representative `< 100 KB`, `< 100` row sample inputs and expected `.csv`/`.tmcf` outputs for all 3 processor runs. |

## 3. Refresh Procedure (Manual Staging + Automated Pipeline)

1. From an Indian IP, open `https://indiawris.gov.in/wris/#/DataDownload`, select **Env & Water Quality** -> **Ground Water Quality** (Agency: `CGWB`) or **Surface Water Quality** (Agency: `CWC`), complete the CAPTCHA, and export the `.zip` archive.
2. Prepare and validate the staged CSV files against their expected column schemas (`manifest.json` reads only the fixed filenames `groundWater.csv`, `India_WRIS_Ground_Prod_Retained.csv`, and `surfaceWater.csv` — overwrite them in place; do not stage dated copies):
   - **`groundWater.csv`** (raw WRIS Ground Water export schema): expects raw WRIS headers (`State Name`, `District Name`, `Station Name`, `Date Collection` in `YYYY-MM`, and the 27 spaced parameter headers such as `Calcium (mg/L)`, `Mercury (mg/L)`, `Total Hardness (mg/L)`). Verify every row has the expected column count — raw WRIS exports have occasionally included unescaped commas in station names that shift columns (`b/579716190`); fix or quote any malformed commas before staging.
   - **`surfaceWater.csv`** (compact/preprocessed Surface Water schema, matching legacy CNS `India_WRIS_Surface.csv`): expects spaceless headers consumed by `manifest.json` (`DistrictName:india_wris_districts_pvmap.csv`) and `surface_water_pvmap.csv`:
     - Metadata columns: `StateName`, `DistrictName`, `Month` (`YYYY-MM`), `StationName`.
     - Parameter columns (27): `Aluminium(Al)`, `Arsenic(As)`, `cyanides(CN)`, `Carbonate(CO3)`, `Calcium(Ca)`, `Chloride(Cl)`, `Fluorine(F)`, `Iron(Fe)`, `Hydrogencarbonate(HCO3)`, `Mercury(Hg)`, `Potassium(K)`, `Magnesium(Mg)`, `ammonia(NH3)`, `Nitrate(NO3)`, `Lead(Pb)`, `Silver(Ag)`, `Sulfate(SO4)`, `Silicondioxide(SiO2)`, `Zinc(Zn)`, `DisolvedOxygen(DO)`, `ElectricalConductivity`, `HardnessTotal`, `AlkalinityTotal`, `ResidualSodiumCarbonate`, `Sodiumabsorptionratio(SAR)`, `TotalDissolvedSolids`, `PotentialofHydrogen(pH)`.
     - If refreshing `surfaceWater.csv` from a raw WRIS export with spaced headers (e.g., `District Name`, `Station Name`, `Hardness Total`, `Aluminium (Al)`), strip spaces from the header row and populate `Month` (`YYYY-MM`) to match the schema above before uploading.
   - **`India_WRIS_Ground_Prod_Retained.csv`** (frozen historical Ground Water 2000–2018 baseline): long-format columns (`variable_measured`, `observation_about`, `observation_date`, `observation_period`, `measurement_method`, `unit`, `value`); leave unchanged during routine refreshes.
3. Upload the refreshed files to the staging bucket:
   ```bash
   gcloud storage cp groundWater.csv surfaceWater.csv \
     gs://unresolved_mcf/india_wris/water_quality/input_files/
   ```
4. The scheduled pipeline (`0 4 * * 1`) automatically runs `download.py`, processes all three CSVs with `stat_var_processor.py`, validates against `validation_config.json`, and publishes the refreshed import version.

## 4. Running Locally & Testing

### Prerequisites
From the `data` repository root, set up `.env`:
```bash
./run_tests.sh -r
```

### Run Download & Processing Locally
From `statvar_imports/india_wris/water_quality/`:
```bash
../../../.env/bin/python download.py

../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/groundWater.csv \
  --pv_map='District Name:india_wris_districts_pvmap.csv,ground_water_pvmap.csv' \
  --config_file=ground_water_statvar_processor_config.json \
  --statvar_dcid_remap_csv=statvar_remap.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output/ground/india_wris_ground \
  --output_counters=counters/india_wris_ground_counters.csv

../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/India_WRIS_Ground_Prod_Retained.csv \
  --pv_map=ground_water_retained_pvmap.csv \
  --config_file=ground_water_retained_statvar_processor_config.json \
  --statvar_dcid_remap_csv=statvar_remap.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output/retained/india_wris_ground_retained \
  --output_counters=counters/india_wris_ground_retained_counters.csv

../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/surfaceWater.csv \
  --pv_map=DistrictName:india_wris_districts_pvmap.csv,surface_water_pvmap.csv \
  --config_file=surface_water_statvar_processor_config.json \
  --statvar_dcid_remap_csv=statvar_remap.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output/surface/india_wris_surface \
  --output_counters=counters/india_wris_surface_counters.csv
```

### Regenerate `test_data/` Fixtures & Run Unit Tests
From `statvar_imports/india_wris/water_quality/`:
```bash
../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=test_data/ground_water_input.csv \
  --pv_map='District Name:india_wris_districts_pvmap.csv,ground_water_pvmap.csv' \
  --config_file=ground_water_statvar_processor_config.json \
  --statvar_dcid_remap_csv=statvar_remap.csv \
  --output_path=test_data/india_wris_ground \
  --output_counters=/tmp/gw_test_counters.csv

../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=test_data/ground_water_retained_input.csv \
  --pv_map=ground_water_retained_pvmap.csv \
  --config_file=ground_water_retained_statvar_processor_config.json \
  --statvar_dcid_remap_csv=statvar_remap.csv \
  --output_path=test_data/india_wris_ground_retained \
  --output_counters=/tmp/gwr_test_counters.csv

../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=test_data/surface_water_input.csv \
  --pv_map=DistrictName:india_wris_districts_pvmap.csv,surface_water_pvmap.csv \
  --config_file=surface_water_statvar_processor_config.json \
  --statvar_dcid_remap_csv=statvar_remap.csv \
  --output_path=test_data/india_wris_surface \
  --output_counters=/tmp/sw_test_counters.csv
```

From the repository root, run unit tests and lint:
```bash
./run_tests.sh -p statvar_imports/india_wris
./run_tests.sh -l
```
