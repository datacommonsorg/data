# DataCommons World Bank Data Downloads

This file contains the code to automatically generate statistical variables for
the World Bank World Development Indicators, download these statistical
variables for all countries and all years, and to output this data into a
writtable format to the knowledge graph.

Statistical variables are defined in the WorldBankIndicators.csv. To add a new
statistical variable to this list, you must find the corresponding indicator
code, name, and source and manually fill out the corresponding properties such
as measurement method, population type, and the various constraints. You likely
will need to define new schema enums and objects which should be created
separately.

We highly recommend the use of the import validation tool for this import which
you can find in
https://github.com/datacommonsorg/tools/tree/master/import-validation-helper.

## Update statistical variables

To add a new statistical variable or to refresh the data for a new year, simply
create an output directory and then run worldbank.py after installing the
necessary requirements. This will output WorldBank_StatisticalVariables.mcf with
the MCF definitions for all new statistical variables. Then various groupings of
template MCFs and CSVs will be output depending on which unique statistical
observation properties are present in that group. Each of these CSV + TMCF
grouping can then be written to the knowledge graph along with the statistical
variables file.
