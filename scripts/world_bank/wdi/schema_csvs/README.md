# World Bank WDI Schema CSVs

This import uses the CSVs in this directory to build the artifacts for importing
into Data Commons (StatVarObs Template MCFs, StatVar MCFs, and the final CSV).

## Adding new variables to Data Commons

To add new StatisticalVariables to Data Commons, for each indicator:

1. Find the corresponding indicator code, name, and source. [Here](https://data.worldbank.org/indicator?tab=all) is a way to see all the indicators. TODO(IanCostello): document how you dumped all the indicator metatdata into a CSV.

1. Add to or create a new schema CSV (copy [schema_template.csv](schema_template.csv) with a meaningful name).

1. Fill out the columns for each variable you want to add
   to the best of your ability.

   - There are some non-schema fields:
   - IndicatorCode: WDI's code for the indicator
   - ConvertToInt: whether to convert the value to an int. TODO(IanCostello): explain why this is necessary
   - ExistingStatVar: whether this variable corresponds to a StatVar that already exists in DC. The code will then use that StatVar instead of creating a new one.
   - IndicatorName: Name from WDI, useful for visual debugging.
   - SourceNote: Source note from WDI, useful for visual debugging.
   - Source: Original data source. Maybe useful down the road for better data citation.

1. Request a Data Commons engineer for review.

1. When your import is productionized:

   - Copy everything except the column headers
     into [WorldBankIndicators_prod.csv](WorldBankIndicators_prod.csv).

   - Add a description for your file in the next section.

## Existing Schema CSVs

Productionized variables (these are concatenated together into
[WorldBankIndicators_prod.csv](WorldBankIndicators_prod.csv)):

- [WorldBankIndicators_p0.csv](WorldBankIndicators_p0.csv): IanCostello's first WDI import done with the GitHub process.
- [WorldBankIndicators_p1.csv](WorldBankIndicators_p1.csv): IanCostello's second batch of WDI variables, finished by tjann.
- [WorldBankIndicators_placepg.csv](WorldBankIndicators_placepg.csv): tjann's first WDI import using this GitHub process. The variables were requested by rvguha just prior to the Data Commons launch.

IMPORTANT: Please help keep [WorldBankIndicators_prod.csv](WorldBankIndicators_prod.csv)
up to date. Copy your rows over when you see your import prod.

In progress variables:

- [WorldBankIndicators_p1_modeling_issues.csv](WorldBankIndicators_p1_modeling_issues.csv): tjann found modeling issues with these variables from IanCostello's import and moved them out here.
- [WorldBankIndicators_p1_placeobs.csv](WorldBankIndicators_p1_placeobs.csv): tjann realized that IanCostello's code in GitHub does not support Observations directly on places and thus moved those variables here.
