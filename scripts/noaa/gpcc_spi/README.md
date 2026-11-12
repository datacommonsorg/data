# GPCC SPI Import

## Overview
This pipeline downloads Global Precipitation Climatology Centre (GPCC) Standardized Precipitation Index (SPI) NetCDF datasets (Pearson Type III distribution across 6 time scales: 1, 3, 6, 9, 36, and 72 months) from NOAA NCEI (`https://www.ncei.noaa.gov/pub/data/nidis/gpcc/spi-pearson/`) and generates inputs for **5 Data Commons imports**:

1. **`NOAA_GPCC_StandardardizedPrecipitationIndex` (`input0`):**
   - **Template MCF:** `gpcc_spi.tmcf`
   - **Cleaned CSVs:** `output_files/gpcc_spi_pearson_{01,03,06,09,36,72}.csv`
   - **Description:** Monthly 1-degree grid (`grid_1/<lat>_<lon>`) SPI observations.
2. **`NOAA_GPCC_StandardardizedPrecipitationIndex_AggPlace` (`input1`):**
   - **Template MCF:** `gpcc_spi_aggregation.tmcf`
   - **Cleaned CSVs:** `output_files/aggregations/agg_gpcc_spi_pearson_{01,03,06,09,36,72}.csv`
   - **Description:** Area-weighted SPI aggregations for countries, continents, states, and counties.
3. **`NOAA_GPCC_StandardardizedPrecipitationIndex_Event_Places` (`input2`):**
   - **Template MCF:** `drought_spi_9m_polygon_place_svobs.tmcf`
   - **Cleaned CSV:** `output_files/events_spi_9m_polygon/place_svobs/drought_spi_9m_polygon_place_svobs.csv`
   - **Description:** Monthly and annual drought event counts (`Count_DroughtEvent`) and areas (`Area_DroughtEvent`) per grid place based on 9-month SPI (`<= -1.5`).
4. **`NOAA_GPCC_StandardardizedPrecipitationIndex_Event` (`input3`):**
   - **Template MCF:** `drought_spi_9m_polygon_events.tmcf`
   - **Cleaned CSV:** `output_files/events_spi_9m_polygon/events/drought_spi_9m_polygon_events.csv`
   - **Description:** `DroughtEvent` entities with GeoJSON polygons, affected 1-degree grid places, start locations (`GeoCoordinates`), and areas (`Quantity`).
5. **`NOAA_GPCC_StandardardizedPrecipitationIndex_Event_Observations` (`input4`):**
   - **Template MCF:** `drought_spi_9m_polygon_svobs.tmcf`
   - **Node MCF:** `output_files/events_spi_9m_polygon/event_svobs/drought_spi_9m_polygon_svobs_nodes.mcf`
   - **Cleaned CSV:** `output_files/events_spi_9m_polygon/event_svobs/drought_spi_9m_polygon_svobs.csv`
   - **Description:** `Area_DroughtEvent` and `standardizedPrecipitationIndex` observations linked to each `DroughtEvent`.

## Scripts

### `run.sh`
Main entrypoint executed by the automated import pipeline (`manifest.json`):
1. Runs `download.py` to download the live GPCC SPI Pearson NetCDF files (`gpcc_spi_pearson_{01,03,06,09,36,72}.nc`) from NOAA NCEI into `input_files/`.
2. Runs `preprocess_gpcc_spi.py` to convert the NetCDF files into 1-degree grid CSVs (`2010-12` onward) in `output_files/`.
3. Runs `gpcc_spi_aggregation.py` to compute area-weighted place aggregations in `output_files/aggregations/`.
4. Shards `output_files/gpcc_spi_pearson_09.csv` by year using `tools/pd_csv.sh` and runs `scripts/earthengine/process_events.py` (`events_drought_gpcc_spi_9m_polygon.py`) to generate 9-month SPI polygon drought events and observations under `output_files/events_spi_9m_polygon/`.
5. Generates the companion `node_mcf` file (`drought_spi_9m_polygon_svobs_nodes.mcf`) for `input4`.

### `download.py`
Downloads `gpcc-spi-pearson-{01,03,06,09,36,72}.nc` from `https://www.ncei.noaa.gov/pub/data/nidis/gpcc/spi-pearson/` into `input_files/`.

### `preprocess_gpcc_spi.py`
Reads `input_files/gpcc_spi_pearson_*.nc`, filters dates from `start_date` to `end_date` (current date), converts NetCDF grid coordinates to 1-degree `grid_1/<lat>_<lon>` place DCIDs, and outputs `output_files/gpcc_spi_pearson_*.csv`.

### `gpcc_spi_aggregation.py`
Joins 1-degree grid SPI values (`output_files/*.csv`) with place area ratios (`geojson_data/place_area_ratio.json`) to produce weighted SPI aggregations for administrative places in `output_files/aggregations/`.

## Running Tests

```bash
python3 -m unittest scripts/noaa/gpcc_spi/preprocess_gpcc_spi_test.py
python3 -m unittest scripts/noaa/gpcc_spi/gpcc_spi_aggregation_test.py
```

