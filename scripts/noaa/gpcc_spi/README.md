# GPCC SPI Import

## Overview
This pipeline downloads Global Precipitation Climatology Centre (GPCC) monthly precipitation data from Deutscher Wetterdienst (DWD), computes the Standardized Precipitation Index (SPI) using the Pearson Type III distribution across 6 time scales (1, 3, 6, 9, 36, and 72 months), and generates inputs for **5 Data Commons imports**:

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
   - **Node MCF:** `output_files/events_spi_9m_polygon/events/drought_spi_9m_polygon_events_nodes.mcf`
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
1. Runs `download.py` to download GPCC historical (`full_data_monthly_v2022`, `1891–2019`) and live monthly (`first_guess_monthly`, `2020–present`) NetCDF files into `source_data/` and merge them into `source_data/merged.nc`.
2. Runs `preprocess_gpcc_spi.py` to compute SPI via `climate-indices` (`process_climate_indices`), saving NetCDF files to `input_files/` and 1-degree grid CSVs (`2010-12` onward) to `output_files/`.
3. Runs `gpcc_spi_aggregation.py` to compute area-weighted place aggregations in `output_files/aggregations/`.
4. Shards `output_files/gpcc_spi_pearson_09.csv` by year using `csv_splitter.py` and runs `event_aggregator.py` (`events_spi_9m_polygon_config.py`) to generate 9-month SPI polygon drought events and observations under `output_files/events_spi_9m_polygon/`.
5. Reconciles overlapping drought event IDs against the previous production baseline (`latest_version.txt`) and generates companion `node_mcf` files (`drought_spi_9m_polygon_events_nodes.mcf` and `drought_spi_9m_polygon_svobs_nodes.mcf`).

### `download.py`
Downloads `.nc.gz` files from `https://opendata.dwd.de/climate_environment/GPCC/`, decompresses them, aligns coordinate grids, and outputs `merged.nc`.

### `preprocess_gpcc_spi.py`
Computes SPI using the Pearson distribution (`spi_pearson_01`, `03`, `06`, `09`, `36`, `72`) and converts NetCDF grid coordinates to 1-degree `grid_1/<lat>_<lon>` place DCIDs.

### `gpcc_spi_aggregation.py`
Joins 1-degree grid SPI values with containment ratios (`grid_1_contains.csv`) to produce weighted SPI aggregations for administrative places.

## Running Tests

```bash
python3 -m unittest scripts/noaa/gpcc_spi/preprocess_gpcc_spi_test.py
python3 -m unittest scripts/noaa/gpcc_spi/gpcc_spi_aggregation_test.py
```

