# Importing FAO Exchange Rate and Currency Into Data Commons (`FAO_Currency`)

Author: lucy-kind

## Table of Contents

1. [About the Dataset](#about-the-dataset)
2. [About the Import](#about-the-import)

## About the Dataset

### Download URL

CSV file is available for download from https://bulks-faostat.fao.org/production/Exchange_rate_E_All_Data_(Normalized).zip.
The dataset inside the archive is `Exchange_rate_E_All_Data_(Normalized).csv`.

### Overview

This import includes the exchange rate of currency broken down by country, currency standardization type (details below), and currency (using ISO 4217 Currency Code). Exchange rates are defined as the price of one country’s currency for another currency.

This dataset includes monthly and annual exchange rates for the currency of each country per USDollar (`dcs:ExchangeRate_Currency_Local`), standardized exchange rate per USDollar (`dcs:ExchangeRate_Currency_Standardized`), and country currency usage (`dcs:usesCurrency`).

For example, the "euro" is the standardized currency for Ireland from 1970 to present, as it is the currency used by Ireland in the most recent reference year, though the Irish Pound was the actual currency used from 1970 to 1998.

### Notes and Caveats

- In this dataset, there are inconsistent observation values for XCD currency from 1970-1975 depending on which country the exchange rate of XCD comes from, as well as a single datapoint of inconsistency from SUR in 1990 for the same reason. Assuming that these inconsistencies reflect real world differences in a time before the internet and consistency checking, this does not seem like an issue with the data.

## About the Import

### Artifacts

#### Raw Data & Scripts
- [download.sh](download.sh): Downloads `Exchange_rate_E_All_Data_(Normalized).zip` from FAOSTAT and extracts `input_data/Exchange_rate_E_All_Data_(Normalized).csv`.
- [CurrencyFAO.csv](CurrencyFAO.csv): Historical baseline CSV merged additively with newly downloaded upstream releases to prevent deletion of retired historical series.
- [preprocess.py](preprocess.py): Merges the historical baseline and latest downloaded CSV and generates `output/cleaned_output.csv`.
- [manifest.json](manifest.json): Import automation specification (`import_name: "FAO_Currency"`, scheduled weekly via `0 07 * * 4`).
- [validation_config.json](validation_config.json): Pre-submission validation rules (`DELETED_RECORDS_PERCENT <= 0.1%`, `MISSING_REFS_COUNT == 0`, `LINT_ERROR_COUNT == 0`).

#### Cleaned Data & Template MCFs
- [cleaned_output.csv](output/cleaned_output.csv)
- [CurrencyFAO.tmcf](output/CurrencyFAO.tmcf)

### Running the Pipeline

To download the latest data and generate `output/cleaned_output.csv`, run:

```bash
bash download.sh
python3 preprocess.py
```
