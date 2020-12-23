# World Bank WDI Schema CSVs

This import uses the CSVs in this directory to build the artifacts for importing
into Data Commons (StatVarObs Template MCFs, StatVar MCFs, and the final CSV).

## Adding new variables to Data Commons

1. Make a copy of [schema_template.csv](schema_template.csv) with a meaningful
   name.

1. Fill out the columns for each variable you want to add
   to the best of your ability.

1. Request a Data Commons engineer for review.

1. Add a description for your file in the next section.

## Existing Schema CSVs

Productionized variables:

- [WorldBankIndicators_p0.csv](WorldBankIndicators_p0.csv): IanCostello's first WDI import done with the GitHub process.
- [WorldBankIndicators_p1.csv](WorldBankIndicators_p1.csv): IanCostello's second batch of WDI variables, finished by tjann.
- [WorldBankIndicators_placepg.csv](WorldBankIndicators_placepg.csv): tjann's first WDI import using this GitHub process. The variables were requested by rvguha just prior to the Data Commons launch.

In progress variables:

- [WorldBankIndicators_p1_modeling_issues.csv](WorldBankIndicators_p1_modeling_issues.csv): tjann found modeling issues with these variables from IanCostello's import and moved them out here.
- [WorldBankIndicators_p1_placeobs.csv](WorldBankIndicators_p1_placeobs.csv): tjann realized that IanCostello's code in GitHub does not support Observations directly on places and thus moved those variables here.
