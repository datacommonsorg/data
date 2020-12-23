# Importing World Bank's World Development Indicators into Data Commons

Authors: @IanCostello, @tjann

This import automatically generates StatisticalVariables for
the World Bank World Development Indicators, downloads the data
for all countries and all years, and to output this data into a
writable format to the knowledge graph.

StatisticalVariables are defined in the WorldBankIndicators.csv. To add a new
StatisticalVariable to this list, you must find the corresponding indicator
code, name, and source and manually fill out the corresponding properties such
as measurement method, population type, and the various constraints. You likely
will need to define new schema enums and objects which should be created
separately.

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

Data Commons has some legacy code inside Google that processes 13 WDI variables.
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
1. Fertility rate, total (births per woman)Population, total
1. Population, total
1. Population growth (annual %)

Secondly, in our legacy work, we did not carefully indicate when variables were estimated or standardized across data sources by the WDI.

### License

WDI data is available under a Creative Commons Attribution 4.0 International License, with additional terms. Please see the World Bank Summary Terms of Use at <https://data.worldbank.org/summary-terms-of-use>.

The full license is available at <https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets>.

### Dataset Documentation and Relevant Links

- Documentation: <https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information>
- Homepage: <https://datatopics.worldbank.org/world-development-indicators/>

## About the Import

### Artifacts

#### Scripts

- [worldbank.py](worldbank.py): Downloads and preprocesses the CSVs from World Bank, then creates the StatVars, StatVarObs, and Final CSV using the Preprocessed Source CSVs and Schema CSV.

#### Preprocessed Source CSVs

- preprocessed_source_csv/\*.csv: CSVs downloaded from World Bank's API, and then preprocessed. This is done in [worldbank.py](worldbank.py).

#### Schema CSVs

- \*.csv: CSVs with particular columns helping to describe the StatVar and StatVarObs properties of WDI variables. This is where the "schema modeling" happens/is finalized for this import. The script [worldbank.py](worldbank.py) uses a Schema CSV to write the output artifacts below.

#### Template MCFs

- [output/WorldBank.tmcf](output/WorldBank.tmcf)

#### StatisticalVariable Instance MCF

- [output/WorldBank_StatisticalVariables.mcf](output/WorldBank_StatisticalVariables.mcf)

#### Final CSV

- Contains the data for all countries, all StatVars in a single CSV, where the columns are `StatisticalVariable`, `ISO3166Alpha3`, `Year`, and some number of `Value[0-9]+` columns. The `Value[0-9]+` columns correspond to combinatorial StatVarObs templates based on the presense or absence of optional properties of StatVarObs.

#### Notes

1. When putting the output artifacts into the Data Commons Importer, make sure to opt to ignore CSV value errors. This is because each StatisticalVariable will only have one non-null value among all the `Value[0-9]+` columns.

### Import Procedure

#### Creating the Schema CSV

Make a copy of [schema_template.csv](schema_template.csv) and fill out the columns
for your desired WDI variables. You may look at the other \*.csv files for reference.

#### Processing Steps

To generate `output/WorldBank_StatisticalVariables.mcf`,
`output/WorldBank.tmcf`, and `output/WorldBank.csv`, run:

```bash
python3 worldbank.py --indicatorSchemaFile=<DESIRED INDICATOR CSV FILE> --fetchFromSource=<WHETHER TO RE-FETCH FROM WDI WEBSITE INSTEAD OF USING CHECKED-IN CSVS>
```

We highly recommend the use of the import validation tool for this import which
you can find in
https://github.com/datacommonsorg/tools/tree/master/import-validation-helper.
