# Importing FAO Exchange Rate and Currency Into Data Commons

Author: lucy-kind

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [About the Import](#about-the-import)

## About the Dataset


### Download URL

CSV file is available for download from https://fenixservices.fao.org/faostat/static/bulkdownloads/Exchange_rate_E_All_Data_(Normalized).zip.
The dataset is called `Exchange_rate_E_All_Data_(Normalized).csv`.

### Overview

This import includes the exchange rate of currency broken down by country, currency standardization type (details below), and currency (using ISO 4217 Currency Code). Exchange rates are defined as the price of one country’s currency for another currency. 

This dataset includes monthly and annual exchange rates for the currency of each country per USDollar. For each year, this dataset also calculates a Standardized exchange rate which uses that country’s current currency and compares that to the USDollar.

For example, the "euro” is the standardized currency for Ireland from 1970 to 2021, as it was the currency used by Ireland in the most recent reference year (2021), though the Irish Pound was the actual currency used for 1970 to 1998.

In this dataset, each Country has an associated currency unit. To find the exchange rate, the value of that currency unit at a particular time is represented in comparison to the USDollar.

### Notes and Caveats

- In this dataset, there are inconsistent observation values for XCD currency from 1970-1975 depending on which country the exchange rate of XCD comes from, as well as a single datapoint of inconsistency from SUR in 1990 for the same reason. Assuming that these inconsistencies reflect real world differences in a time before the internet and consistency checking, this does not seem like an issue with the data.


## About the Import

### Artifacts

#### Raw Data
- [CurrencyFAO.csv](CurrencyFAO.csv)

#### Cleaned Data
- [cleaned_output.csv](output/cleaned_output.csv)

#### Template MCFs
- [CurrencyFAO.tmcf](output/CurrencyFAO.tmcf)

#### Scripts
- [preprocess.py](preprocess.py)


#### Generating Artifacts:

`CurrencyFAO.tmcf` was handwritten.

To generate `cleaned_output.csv`, run:

```bash
python3 preproccess.py
```

#### Post-Processing Validation

- Ran [dc-import tool]
  (https://github.com/datacommonsorg/import/blob/master/docs/usage.md)
  to validate that the resulting CSV and Template MCF artifacts are
  compatible.

  - [report.json](validation/report.json)
  - [summary_report.html](validation/summary_report.html)

  Results show only error is due to the inconsistency of exchange rate mentioned in notes/caveats, which reflects real world observational differences.
