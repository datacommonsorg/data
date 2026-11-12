# Copernicus ECMWF ERA5 Monthly Import

## 1. Overview

This directory contains the automated Data Commons import package for
`Copernicus_ECMWF_ERA5_Monthly` (`google3/datacommons/import/mcf/manifest/ipcc/Copernicus_ECMWF_ERA5_Monthly.textproto`
and `google3/datacommons/import/mcf/resolved_mcf/import/Copernicus_ECMWF_ERA5_Monthly.mcf`),
providing Copernicus Climate Change Service / ECMWF ERA5 and ERA5-Land monthly
climate reanalysis aggregates for `AdministrativeArea1` and `AdministrativeArea2`
places worldwide.

- **Source URL**: https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels
- **Earth Engine Catalog**:
  - Historical baseline (`1979-01` to `2020-06`): `ECMWF/ERA5/MONTHLY` (cached in
    `gs://datacommons_public/unresolved_mcf/copernicus_ecmwf/era5_monthly/` and
    synced locally into `history_files/`)
  - Ongoing monthly updates (`2020-07` to latest): `ECMWF/ERA5_LAND/MONTHLY_AGGR`
    (fetched and converted locally into `input_files/`)
- **Place Coverage**: Global `AdministrativeArea1` (states/NUTS1/NUTS2) and
  `AdministrativeArea2` (counties/NUTS3) places with GeoJSON polygons.
- **Temporal Coverage**: Monthly (`P1M`) from `1979-01` to present.

### Mapped StatisticalVariables

All 7 active variables preserve exact production schema parity with
`measurementMethod: dcAggregate/ERA5Monthly` and `observationPeriod: P1M`:

| Canonical Column | `ECMWF/ERA5_LAND/MONTHLY_AGGR` Band | `variableMeasured` | `unit` |
|---|---|---|---|
| `minimum_2m_air_temperature` | `temperature_2m_min` | `Min_Temperature` | `Celsius` |
| `maximum_2m_air_temperature` | `temperature_2m_max` | `Max_Temperature` | `Celsius` |
| `mean_2m_air_temperature` | `temperature_2m` | `Mean_Temperature` | `Celsius` |
| `dewpoint_2m_temperature` | `dewpoint_temperature_2m` | `DewPointTemperature_SurfaceLevel` | `Millimeter` |
| `surface_pressure` | `surface_pressure` | `AtmosphericPressure_SurfaceLevel` | `Pascal` |
| `u_component_of_wind_10m` | `u_component_of_wind_10m` | `WindSpeed_UComponent_Height10Meters` | `MetersPerSecond` |
| `v_component_of_wind_10m` | `v_component_of_wind_10m` | `WindSpeed_VComponent_Height10Meters` | `MetersPerSecond` |

*Notes*:
- **Why `measurementMethod` is `dcAggregate/ERA5Monthly`**:
  In the legacy production TMCF (`/cns/jv-d/home/datcom/v3_mcf/copernicus_ecmwf/era5_monthly/era5.tmcf`)
  and resolved MCF (`/cns/jv-d/home/datcom/v3_resolved_mcf/copernicus_ecmwf/era5_monthly/nodes.mcf@499`),
  observations are ingested with `measurementMethod: dcid:dcAggregate/ERA5Monthly`
  because gridded ERA5 pixel values are spatially aggregated over place polygons
  by Data Commons. At serving time, Data Commons's `DisaggregateMeasurementMethod`
  (`google3/datacommons/prophet/util/util.cc`) strips the `dcAggregate/` prefix,
  sets `isDcAggregate = true`, and exposes `measurementMethod: ERA5Monthly`
  (defined in `google3/third_party/datacommons/schema/core/measurement_methods.mcf`)
  in the UI and API.
- `total_precipitation` (`total_precipitation_sum`) is omitted from
  `copernicus_ecmwf_era5_monthly_pvmap.csv` and `DewPointTemperature_SurfaceLevel`
  retains `unit: Millimeter` to match production `Copernicus_ECMWF_ERA5_Monthly`.

### Why `1979-01..2020-06` Is Synced into a Separate `history_files/` Folder

1. **Upstream Earth Engine Asset Deprecation (`ECMWF/ERA5/MONTHLY` stopped at `2020-06`)**:
   The historical `1979-01..2020-06` series in `Copernicus_ECMWF_ERA5_Monthly`
   was computed from `ECMWF/ERA5/MONTHLY` (0.25° global atmospheric reanalysis),
   which ended at `2020-06`. Ongoing monthly updates (`2020-07+`) come from
   `ECMWF/ERA5_LAND/MONTHLY_AGGR`.
2. **0% Historical Deletion in Import Differ**:
   Production `/cns/jv-d/home/datcom/v3_resolved_mcf/copernicus_ecmwf/era5_monthly/nodes.mcf@499`
   was generated from the 499 `1979-01..2020-06` `.celsius.csv` files cached in
   `gs://datacommons_public/unresolved_mcf/copernicus_ecmwf/era5_monthly/`.
   Syncing those historical baseline files into `history_files/` while keeping
   newly fetched `2020-07+` files in `input_files/` keeps historical data
   cleanly separated from new `source_files` while guaranteeing 0% deleted
   historical records in `Copernicus_ECMWF_ERA5_Monthly`.

## 2. Important Files

- `download_and_process.py`: Download and preprocessing script:
  1. Syncs historical `.celsius.csv` files (`1979-01..2020-06`) from
     `gs://datacommons_public/unresolved_mcf/copernicus_ecmwf/era5_monthly/`
     into `history_files/` using `util/download_util_script.py` and
     `util/file_util.py`.
  2. Queries `ECMWF/ERA5_LAND/MONTHLY_AGGR` in Google Earth Engine for
     `2020-07..latest`, renaming bands to canonical ERA5 column names and
     converting Kelvin temperatures to Celsius (`%.6g`, matching
     `kelvin2celsius.sh`) into `input_files/`.
- `copernicus_ecmwf_era5_monthly_pvmap.csv`: Property-value mapping file for
  `tools/statvar_importer/stat_var_processor.py`.
- `copernicus_ecmwf_era5_monthly_metadata.csv`: Configuration parameters for
  `tools/statvar_importer/stat_var_processor.py`.
- `manifest.json`: Import automation specification running `download_and_process.py`
  followed by `../../tools/statvar_importer/stat_var_processor.py`.
- `validation_config.json`: Import-specific validation rules
  (`MAX_DATE_CONSISTENT`, `SQL_VALIDATOR` freshness check,
  `NUM_PLACES_CONSISTENT`), merged with the default base validation rules.
- `download_and_process_test.py` and `test_data/`: Unit and E2E tests and
  fixtures.

## 3. Running Locally and Refresh Procedure

From the repository root:

```bash
# Step 1: Download historical baseline into history_files/ and fetch/convert new EE months into input_files/
python3 statvar_imports/copernicus_ecmwf_era5_monthly/download_and_process.py

# Step 2: Run StatVarProcessor
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/copernicus_ecmwf_era5_monthly/history_files/*.celsius.csv,statvar_imports/copernicus_ecmwf_era5_monthly/input_files/*.celsius.csv \
  --pv_map=statvar_imports/copernicus_ecmwf_era5_monthly/copernicus_ecmwf_era5_monthly_pvmap.csv \
  --config_file=statvar_imports/copernicus_ecmwf_era5_monthly/copernicus_ecmwf_era5_monthly_metadata.csv \
  --output_path=statvar_imports/copernicus_ecmwf_era5_monthly/output/era5_monthly \
  --output_counters=statvar_imports/copernicus_ecmwf_era5_monthly/counters/era5_monthly_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## 4. Testing

Run the unit and end-to-end test suite from the repository root:

```bash
./run_tests.sh -p statvar_imports/copernicus_ecmwf_era5_monthly
```
