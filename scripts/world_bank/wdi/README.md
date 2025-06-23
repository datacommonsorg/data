# Importing World Bank's World Development Indicators into Data Commons

Authors: @IanCostello, @tjann

This is Data Common's main source of international, country-level data.

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

The World Development Indicators (WDI) dataset contains hundreds of variables
available across hundred of countries. Oftentimes a variable will come from different
sources for different countries, but are standardized by the World Bank.

Data Commons imports several dozens of these variables into our knowledge graph.

### Notes and Caveats

Data Commons has some legacy code not in GitHub that processes 13 WDI variables.
They are:

1. CO2 emissions (metric tons per capita)
1. Electric power consumption (kWh per capita)
1. Energy use (kg of oil equivalent per capita)
1. GDP (current US$)
1. GDP growth (annual %)
1. GDP per capita (current US$)
1. GNI, PPP (current international $)
1. GNI per capita, PPP (current international $)
1. Individuals using the Internet (% of population)
1. Life expectancy at birth, total (years)
1. Fertility rate, total (births per woman)
1. Population, total
1. Population growth (annual %)

Secondly, we did not consistently indicate when variables were estimated or standardized across data sources. E.g. observations of
`MortalityRate_Person_Upto4Years_AsFractionOf_Count_BirthEvent_LiveBirth`
[do not indicate](https://datacommons.org/browser/dc/p/mbwqq551rch16) that it was
[estimated by the UN Inter-agency Group for Child Mortality Estimation](https://data.worldbank.org/indicator/SH.DYN.MORT),
while observations of
`MortalityRate_Person_Upto4Years_AsFractionOf_Count_BirthEvent_LiveBirth`
[do indicate so](https://datacommons.org/browser/dc/p/6jq9n69ezf2k6).

### License

WDI data is available under a Creative Commons Attribution 4.0 International License, with additional terms. Please see the World Bank Summary Terms of Use at <https://data.worldbank.org/summary-terms-of-use>.

The full license is available at <https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets>.

### Dataset Documentation and Relevant Links

- Documentation: <https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information>
- Homepage: <https://datatopics.worldbank.org/world-development-indicators/>

## About the Import

This import automatically generates StatisticalVariable MCF and
StatVarObservation TMCF for specified World Bank World Development Indicators,
downloads the data for all countries and all years,
outputs this information into the required import artifacts for
ingesting into Data Commons.

This is achieved through a schema-config CSV. You can read more about it
and learn how to import new variables in [schema_csv/README.md](schema_csv/README.md).

### Artifacts

#### Schema CSVs

- [`schema_csvs/WorldBankIndicators_*.csv`](schema_csvs): manually curated CSVs
  with particular columns helping to describe the StatVar and StatVarObs
  properties of WDI variables. This encodes the final schema for the import.
  The script [worldbank.py](worldbank.py) uses a Schema CSV
  to write the output artifacts below.

Note: we keep the CSVs separate to help record which variables were imported when,
as WDI has many variables and we've been importing them in waves. If you simply
want to regenerate the same variables with new year's data, you should use
[schema_csvs/WorldBankIndicators_prod.csv](schema_csvs/WorldBankIndicators_prod.csv).

#### Scripts

- [worldbank.py](worldbank.py): Downloads and preprocesses the CSVs from World Bank, then creates the StatVars, StatVarObs, and Final CSV using the Preprocessed Source CSVs and Schema CSV.

#### StatisticalVariable Instance MCF

- [output/WorldBank_StatisticalVariables.mcf](output/WorldBank_StatisticalVariables.mcf)

#### Template MCFs

- [output/WorldBank.tmcf](output/WorldBank.tmcf)

#### Preprocessed Source CSVs

- [`preprocessed_source_csv/*.csv`](preprocessed_source_csv): CSVs downloaded
  from World Bank's API, and then preprocessed.
  This is done in [worldbank.py](worldbank.py).

  These files differ from the Final CSV as they have ALL the data. These files
  are saved as cached files, so that we don't need to refetch from worldbank.org
  until the next year's data is released.

#### Final CSV

- Contains the data for all specified indicators and all countries in a single CSV, where the columns are `StatisticalVariable`, `ISO3166Alpha3`, `Year`, and some number of `Value[0-9]+` columns. The `Value[0-9]+` columns correspond to combinatorial StatVarObs templates based on the presense or absence of optional properties of StatVarObs.

#### Notes

1. When putting the output artifacts into the Data Commons Importer, make sure to opt to ignore CSV value errors. This is because each StatisticalVariable will only have one non-null value among all the `Value[0-9]+` columns.

### Import Procedure

#### Creating the Schema CSV

See [schema_csv/README.md](schema_csv/README.md).

#### Processing Steps

To generate `output/WorldBank_StatisticalVariables.mcf`,
`output/WorldBank.tmcf`, and `output/WorldBank.csv`, run:

```bash
python3 worldbank.py --indicatorSchemaFile=<DESIRED INDICATOR CSV FILE> --fetchFromSource=<true TO RE-FETCH FROM WDI WEBSITE INSTEAD OF USING CHECKED-IN PREPROCESSED CSVS ELSE false>
```

#### Processing Steps for Refreshing Data

To generate `output/WorldBank_StatisticalVariables.mcf`,
`output/WorldBank.tmcf`, and `output/WorldBank.csv`, run:

```bash
python3 worldbank.py
```

If you want to perform "only process", run the below command:
```bash
python3 worldbank.py --mode=process
```

If you want to perform "only download", run the below command:
```bash
python3 worldbank.py --mode=download
```

We highly recommend the use of the import validation tool for this import which
you can find in
https://github.com/datacommonsorg/tools/tree/master/import-validation-helper.
