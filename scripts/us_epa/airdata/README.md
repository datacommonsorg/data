# Importing EPA AirData
This directory imports [Outdoor Air Quality Data](https://aqs.epa.gov/aqsweb/airdata/download_files.html) into Data Commons. This includes mean/max concentration and AQI for Ozone, SO2, CO, NO2, PM2.5, and PM10 measured at various monitors throughout the  US, Puerto Rico and US Virgin Islands. Source CSVs are downloaded directly from the pre-generated data files.

The scripts generate:
- `EPA_AirQuality.csv`
- `EPA_AirQuality.tmcf`
- `EPA_AirQuality_sites.mcf`
- `EPA_AQI.csv`
- `EPA_AQI.tmcf`

and relies on the following StatisticalVariables:
- Mean_Concentration_AirPollutant_Ozone
- Max_Concentration_AirPollutant_Ozone
- AirQualityIndex_AirPollutant_Ozone
- Mean_Concentration_AirPollutant_SO2
- Max_Concentration_AirPollutant_SO2
- AirQualityIndex_AirPollutant_SO2
- Mean_Concentration_AirPollutant_CO
- Max_Concentration_AirPollutant_CO
- AirQualityIndex_AirPollutant_CO
- Mean_Concentration_AirPollutant_NO2
- Max_Concentration_AirPollutant_NO2
- AirQualityIndex_AirPollutant_NO2
- Mean_Concentration_AirPollutant_PM2.5
- Max_Concentration_AirPollutant_PM2.5
- AirQualityIndex_AirPollutant_PM2.5
- Mean_Concentration_AirPollutant_PM10
- Max_Concentration_AirPollutant_PM10
- AirQualityIndex_AirPollutant_PM10
- AirQualityIndex_AirPollutant (only for county/CSBA)

## Notes on the Data
Pollutant-specific metrics are provided on the site monitor level. For simplicity in the place mapping, we select a single monitor per site and pollutant and provide the monitor id (POC) as airQualitySiteMonitor in the observation. So, a given observation is distinguished by observationDate, observationAbout (AirQualitySite), and measurementMethod (pollutant standard).

County/CBSA level AQI metrics include the defining site and pollutant, which are included in the StatVarObservation.

## Generating Artifacts

### OpenSSL Configuration
The EPA AQS web server (`aqs.epa.gov`) uses legacy TLS renegotiation that modern OpenSSL (v3+) disallows by default, causing connection errors (`SSL_ERROR_SSL: unsafe legacy renegotiation disabled`). The included `openssl.cnf` sets `Options = UnsafeLegacyRenegotiation` to enable compatibility. Run the scripts with `OPENSSL_CONF=openssl.cnf`.

### Monitor-Level Air Quality (`air_quality.py`)
To generate `EPA_AirQuality.csv`, `EPA_AirQuality.tmcf`, and `EPA_AirQuality_sites.mcf`, run:
```bash
OPENSSL_CONF=openssl.cnf python3 air_quality.py
```
This script generates:
- `EPA_AirQuality.csv`: Cleaned daily monitor observations.
- `EPA_AirQuality.tmcf`: Template MCF mapping observation rows to Data Commons StatVars.
- `EPA_AirQuality_sites.mcf`: Dynamically extracted `AirQualitySite` schema nodes for all unique monitor stations encountered during processing.

By default, the script processes data from 1980 up to the previous calendar year (`datetime.now().year - 1`). You can optionally specify `--data_start_year` and `--data_end_year` flags (or set `START_YEAR` and `END_YEAR` environment variables).

### County / CBSA Aggregates (`air_quality_aggregate.py`)
To generate `EPA_AQI.csv` and `EPA_AQI.tmcf`, run:
```bash
OPENSSL_CONF=openssl.cnf python3 air_quality_aggregate.py
```
By default, this processes aggregate AQI data from 1980 up to the previous calendar year (`datetime.now().year - 1`). You can optionally specify `--aggregate_start_year` and `--aggregate_end_year` flags (or set `START_YEAR` and `END_YEAR` environment variables).

### Running Tests
To run unit tests:
```bash
python3 -m unittest discover -v -s . -p "*_test.py"
```
