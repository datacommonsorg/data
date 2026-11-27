# Copernicus ECMWF ERA5 Monthly Import

## 1. Overview

This directory contains the automated Data Commons custom script import for
`Copernicus_ECMWF_ERA5_Monthly`, providing Copernicus Climate Change Service /
ECMWF ERA5-Land monthly climate reanalysis aggregates for Data Commons
`AdministrativeArea1` and `AdministrativeArea2` places worldwide.

- **Source Catalog**:
  [Copernicus Climate Data Store — ERA5](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels)
- **Earth Engine Dataset**:
  [ECMWF/ERA5_LAND/MONTHLY_AGGR](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_MONTHLY_AGGR)
  (`2020-07` to present; written as CSVs in `input_files/` and mapped to
  StatVarObservation MCF via `era5_monthly.tmcf`)
- **Pre-2020-07 Historical Coverage (`1979-01..2020-06`)**: Stored as validated
  MCF files in the import automation GCS `historic/` folder and merged
  automatically into each version during import execution.
- **Place Coverage**: Global `AdministrativeArea1` (states/provinces/NUTS1–2)
  and `AdministrativeArea2` (counties/districts/NUTS3) places with GeoJSON
  polygons.
- **Temporal Coverage**: Monthly (`P1M`) observations.

### Mapped StatisticalVariables

`era5_monthly.tmcf` maps 7 active climate variables with
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
- Raw ERA5-Land temperature bands are reported in Kelvin and converted to
  Celsius (`val - 273.15`, `%.6g`) by `download_and_process.py`.
- `total_precipitation` (`total_precipitation_sum`) is extracted in CSV outputs
  but intentionally omitted from `era5_monthly.tmcf`.
- `DewPointTemperature_SurfaceLevel` retains `unit: Millimeter` and
  `measurementMethod: dcAggregate/ERA5Monthly` to match existing series schema
  continuity in Data Commons.

## 2. Spatial Aggregation & Place Boundaries

### How Gridded Lat/Long Pixels Map to Data Commons Places

`ECMWF/ERA5_LAND/MONTHLY_AGGR` provides regular global `0.1°` (~`11.1 km`)
latitude/longitude raster images for each calendar month. To convert gridded
pixel values into place-level Data Commons `StatVarObservation`s:

1. `download_and_process.py` filters the monthly `ImageCollection` and runs
   Earth Engine spatial `reduceRegion` reductions over two pre-ingested
   `FeatureCollection` boundary assets:
   - `all_administrativearea1` (`State`, `AdministrativeArea1`, `EurostatNUTS1`,
     `EurostatNUTS2`)
   - `all_administrativearea2` (`County`, `AdministrativeArea2`,
     `AdministrativeArea3`, `EurostatNUTS3`)
2. Each feature carries a `dcid` property and Polygon/MultiPolygon boundary, so
   reduced pixel values emit directly keyed by Data Commons place `dcid` and
   `YYYY-MM` date without intermediate lat/long point resolution.
3. Reducers applied:
   - `temperature_2m_min` -> `ee.Reducer.min()`
   - `temperature_2m_max` -> `ee.Reducer.max()`
   - Remaining bands -> `ee.Reducer.mean().unweighted()`

### Boundary & Aggregation Caveats

- **Land-only ERA5-Land mask**: `ECMWF/ERA5_LAND/MONTHLY_AGGR` masks out ocean
  pixels. Small coastal or island polygons that contain no land pixel center
  yield null band values and are skipped when converting to MCF.
- **Unweighted mean parity**: Using `ee.Reducer.mean().unweighted()` ensures
  pixel-center selection matches unweighted `min`/`max` reducers so all 7
  variables cover the exact same set of places per month.
- **Adaptive reduction scale**: Places larger than `100 km²` (`1e8 m²`) are
  reduced at `10,000 m` (matching ERA5-Land native `~11.1 km` resolution) to
  avoid unnecessary pixel sampling timeouts; smaller places use
  `--reduce_region_scale` (default `1,000 m`).
- **Inverted/unbounded geometry guard**: Any polygon whose spherical area
  evaluates to `<= 0` or `> 1.0e14 m²` (such as malformed clockwise rings) is
  skipped cleanly instead of failing the Earth Engine request.
- **Boundary drift**: Because Earth Engine reads snapshot `FeatureCollection`
  table assets, upstream place additions, renames, splits/merges, or geometry
  fixes in Data Commons do **not** take effect automatically until those EE
  boundary assets are regenerated and re-uploaded. Re-uploading updated
  boundaries may change reduced values for modified places and should be
  reviewed via the import differ before promotion.

### Creating & Updating Boundary Assets in Earth Engine

Place boundary geometries are sourced from the Data Commons knowledge graph
BigQuery **`Edge`** and **`Node`** tables:

1. **Extract boundaries from `Edge` + `Node`**: Join `Edge` rows where
   `predicate = 'geoJsonCoordinates'` (and type membership via
   `predicate = 'typeOf'` into AA1 vs AA2 groups) to `Node.subject_id` to
   retrieve the compressed GeoJSON payload stored in `Node.bytes` (and
   decompress to GeoJSON strings alongside `subject_id AS dcid`).
2. **Normalize geometries for geodesic ingestion**: Strip any 3D Z-coordinates
   and validate/orient polygons to 2D RFC-7946 counter-clockwise windings
   (for example using BigQuery
   `ST_ASGEOJSON(SAFE.ST_GEOGFROMGEOJSON(..., make_valid => TRUE))`) so Earth
   Engine geodesic ingestion does not invert polygons into Earth complements.
3. **Upload CSV tables to Earth Engine**: Stage `<dcid>,<geo_json_coordinates>`
   CSVs to GCS and ingest with explicit geodesic + geometry column flags,
   granting read ACLs to the runner service account:
   ```bash
   earthengine upload table \
     --asset_id=projects/<PROJECT_ID>/assets/all_administrativearea1 \
     --geodesic --primary_geometry_column=geo_json_coordinates \
     gs://<BUCKET>/all_administrativearea1.geojson.csv

   earthengine upload table \
     --asset_id=projects/<PROJECT_ID>/assets/all_administrativearea2 \
     --geodesic --primary_geometry_column=geo_json_coordinates \
     gs://<BUCKET>/all_administrativearea2.geojson.csv
   ```
4. **Verify after boundary refresh**: Re-run the import in dev with
   `--ee_project=<PROJECT_ID>` and inspect differ/validation reports before
   updating production EE assets.

## 3. Important Files

- `download_and_process.py`: Queries `ECMWF/ERA5_LAND/MONTHLY_AGGR` in Earth
  Engine for `2020-07..latest`, renames bands to canonical ERA5 column names,
  and converts Kelvin temperatures to Celsius (`%.6g`) into `input_files/`.
- `era5_monthly.tmcf`: Template MCF mapping CSV rows to 7 Data Commons
  `StatVarObservation` entities.
- `manifest.json`: Import automation specification running
  `download_and_process.py --strict_ee=true` and converting
  `input_files/*.celsius.csv` with `era5_monthly.tmcf`.
- `validation_config.json`: Validation rules (`MAX_DATE_CONSISTENT` and
  `SQL_VALIDATOR` checks for `2020-07` start coverage, 3-month freshness SLA,
  and 7-StatVar place consistency across `>= 14,350` places), merged with the
  base import validation config.
- `download_and_process_test.py` and `test_data/`: Hermetic unit tests and
  CSV conversion fixtures.

## 4. Prerequisites (Earth Engine Setup)

1. Install Python dependencies from `requirements.txt` (`earthengine-api`).
2. Enable `earthengine.googleapis.com` on the target GCP project (default:
   `datcom-import-automation-prod`, or override via `--ee_project` /
   `EE_PROJECT`) and register the project at
   https://console.cloud.google.com/earth-engine/configuration.
3. For local runs, authenticate ADC with Earth Engine scopes:
   `gcloud auth application-default login --scopes="https://www.googleapis.com/auth/earthengine,https://www.googleapis.com/auth/cloud-platform"`
   (Cloud Batch workers use their attached service account ADC).
4. Ensure `projects/<PROJECT_ID>/assets/all_administrativearea1` and
   `projects/<PROJECT_ID>/assets/all_administrativearea2` exist with read ACLs
   for the runner service account.

## 5. Running Locally and Testing

From the repository root:

```bash
# 1. Fetch and convert ERA5-Land monthly CSVs (2020-07..latest) into input_files/
python3 scripts/copernicus_ecmwf_era5_monthly/download_and_process.py \
  --strict_ee=true \
  --ee_project=<PROJECT_ID>

# 2. Convert CSVs to resolved MCF via Data Commons import tool
dc-import genmcf \
  scripts/copernicus_ecmwf_era5_monthly/era5_monthly.tmcf \
  scripts/copernicus_ecmwf_era5_monthly/input_files/*.celsius.csv \
  -o=scripts/copernicus_ecmwf_era5_monthly/output

# 3. Run unit tests
./run_tests.sh -p scripts/copernicus_ecmwf_era5_monthly
```
