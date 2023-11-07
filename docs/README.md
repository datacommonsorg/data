# Adding a Dataset to Data Commons

This document summarizes the steps involved in adding a dataset to Data Commons (DC).

## Prerequisites

* Ensure that the Data Commons team has approved the addition of the dataset. Please [suggest a dataset here](https://docs.google.com/forms/d/e/1FAIpQLSf_kZ13bmzXvgEbim0OXeAVsTQYsIhN8_o9ekdbjKoeFjfvRA/viewform).
* Review the following documents to get a background on the data model, format and workflow:
  * [Summary of data model](https://schema.org/docs/datamodel.html) (DC inherits schema from schema.org)
  * [How statistics is represented in DC](representing_statistics.md)
  * [MCF Format](mcf_format.md)
  * [Life of a dataset](life_of_a_dataset.md)

## Design location and schema mapping

Data Commons is a single graph that reconciles references to the same entities and concepts across datasets. This linking happens at the time of importing datasets. To get started:

* Identify how the locations/places/entities and variables/properties in the dataset will get mapped.
* For locations/places, use the following (in preferred order): global identifiers (like FIPS), geo info (lat/lng, geo boundary), qualified names.
* For variables, find already existing schema in Data Commons (from existing statistical variables [here](https://datacommons.org/tools/statvar)), or add new StatisticalVariable nodes along with core schema (new Class, Property, Enumeration nodes) as necessary.

This process typically happens in collaboration with the DC core team, and we recommend that you put together a short import document ([Template](https://docs.google.com/document/d/1RUOD3VLZFBmyjZzBnwQBKB9TxNE7NhD4g9WX6gUZCQU/), [Example1](https://docs.google.com/document/d/e/2PACX-1vScfoVm36L7x1p4Bqh82JmDmsumhqiPz_w6zX7wzy0nX8kDLxMJw44hOBgB6CDd2o0kYKekdgNWIR1f/pub), [Example2](https://docs.google.com/document/d/e/2PACX-1vS9R0eZO-AhQ19jQcLyOyYODn3dF8wGjytro0nFTjp4MsoFvsAgD7mayppcseLvNSCO6Ac4-8b2SXe4/pub))

### Schema-less imports
For datasets with complex schema or ones that we want to import quickly, we can start with a schema-less import, and iteratively add schema. The “schema-less” part of this framework means that the statistical variables are not yet fully defined. This lets us get the dataset into Data Commons without blocking on schema definition. To learn more, please review the following links:
  * [Schema-less Import Guide](https://docs.datacommons.org/import_dataset/schema_less_guide.html)
  * [Schema-less import document template](https://docs.google.com/document/d/1GC7DTpxXo_3zreDRt7wFuURBfA1T275p-qx1N-VIdGM/)
  * [Example](https://docs.google.com/document/d/e/2PACX-1vS6ItxH7T_XvYuz4-xeO9LKoYlrXr-YkrwiclRWcdtYm11J8OQHUwDw4E66uaTQA7yTdwLXfrNBdKgz/pub)

## Preparing artifacts

Once the entity and schema mapping have been finalized, you can now prepare the artifacts. This includes:
  * StatisticalVariable MCF nodes (if any) checked into [schema repo](https://github.com/datacommonsorg/schema/tree/main/stat_vars)
  * Template MCF and corresponding cleaned tabular files (typically CSV).
  * Data cleaning code (along with README) checked into [data repo](https://github.com/datacommonsorg/data)
  * Validation results for the artifacts (from running [`dc-import`](https://github.com/datacommonsorg/import#using-import-tool) tool)

Note: you may also use the [DC Import Wizard](https://datacommons.org/import) to help generate artifacts for common dataset structures

## Review by DC team

When all the artifacts are ready, please get it reviewed by the DC core team via github Pull Requests made to the [data repo](https://github.com/datacommonsorg/data). 
