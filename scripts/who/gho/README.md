# GHO (WHO) - Data Imports

This directory stores all scripts used to import datasets from the GHO (WHO) into Data Commons.

## Base Class - GHOIndicatorProcessorBase
`who.gho.base_processor.GHOIndicatorProcessorBase` is the base class for all GHO data loaders. The base class has two abstract methods which need to be implemented by the subclasses: _retrieve_and_process_data() and _create_stats_vars(). Details for each of them are provided in the base_processor.GHOIndicatorProcessorBase.

Once the abstract functions are implemented, the process_all() method should process all the input and produce the mcf, tmcf and cleaned data csv files.

The base class has its own unit tests under who.gho.base_processor_test. In order to run these unit tests, navigate to the folder: /scripts/who/gho and then execute: $python3 base_processor_test


##immunization
This sub-directory processes all GHO (WHO) data for immunizations. For now, only aggregate_level (country-level) data without dimensions is processed. The data is described in the following section.

##aggregate_level
The data is processed at the country level for aggregated indicators. No other dimensions, e.g. gender, are provided in this data by the GHO. More information about the data is described next:

The Global Health Organization (GHO) is a World Health Organization(WHO) initialiative to share data and statistics about global health. GHO organizes their data by country and indicators. Often, they will group indicators by category, e.g. the immunization category has data about several vaccinations/immunizations, e.g. polio immunization coverage among one year olds (as a percentage).

Data about each indicator is available via the GHO data API and on their website directly. For instance, the Polio immunization coverage (indicator code: "WHS4_544") can be found on the website here. However, each table exposes a data download option which invokes the API. For example, the same data referenced earlier is available as a CSV download via the following url (https://apps.who.int/gho/athena/data/GHO/WHS4_544?filter=COUNTRY:*&x-sideaxis=COUNTRY&x-topaxis=GHO;YEAR&profile=verbose&format=csv). Note that the API for downloading data about all indicators remains the same with the indicator code is replaced by other indicator codes.

###Data retrieval expectations
See examples of the data returned by this API under /scripts/who/gho/immunization/aggregate_level/test_data/.

###Indicator Metadata
See /scripts/who/gho/immunization/aggregate_level/indicator_metadata.csv for an example of the indicator metadata required. This is where you can choose which indicators to process. The input csv expects the following fields:

immunizationName
ghoCode
description
immunizedAgainst
populationType
measuredProperty
age
ageUnit
statsVarNameSuffix
constraintProperties
hasDenominator


###Output
/scripts/who/gho/immunization/aggregate_level/processor.py processes the inputs and produces the .tcmf, .mcf and processed csv data under the following path: /scripts/who/gho/immunization/aggregate_level/output_files/. The indicator metadata file is processed to produced the .mcf file. The base processor (who.gho.base_processor.GHOIndicatorProcessorBase) produces the .tcmf file.

###Unit Tests 
/scripts/who/gho/immunization/aggregate_level/units_test.py contains the unit tests for the processor.