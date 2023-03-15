# Adding a Dataset to Data Commons

This document summarizes the steps involved in adding a dataset to Data Commons
(DC).  As a prerequisite, please ensure that the DC core team
(support@datacommons.org) has approved the addition of the dataset.

## Background

The following documents provide a background on the data model, format and workflow:

1. [Summary of data model](https://schema.org/docs/datamodel.html) (DC inherits schema from schema.org)
1. [How statistics is represented in DC](representing_statistics.md)
1. [MCF Format](mcf_format.md)
1. [Life of a dataset](life_of_a_dataset.md)

## Designing location and schema mapping

Data Commons is a single graph that reconciles references to the same entities
and concepts across datasets. This linking happens at the time of importing
datasets.

As part of the first step, we identify how the locations/places/entities and
variables/properties in the dataset will get mapped. 

* For locations/places, we can use the following (in preferred order):  global
identifiers (like FIPS), geo info (lat/lng, geo boundary), qualified names.
The approach we use depends on how the locations appear in the dataset.

* For variables, we either need to find already existing schema in Data Commons
(from existing statistical variables
[here](https://datacommons.org/tools/statvar)), or add new StatisticalVariable
nodes along with core schema (new `Class`, `Property`, `Enumeration` nodes) as
necessary.

This process typically happens in collaboration with the DC core team, and we
recommend that you put together a short import document.

Links:
* Suggested [import document template](https://docs.google.com/document/d/1RUOD3VLZFBmyjZzBnwQBKB9TxNE7NhD4g9WX6gUZCQU/)
* [Example1](https://docs.google.com/document/d/e/2PACX-1vScfoVm36L7x1p4Bqh82JmDmsumhqiPz_w6zX7wzy0nX8kDLxMJw44hOBgB6CDd2o0kYKekdgNWIR1f/pub)
* [Example2](https://docs.google.com/document/d/e/2PACX-1vS9R0eZO-AhQ19jQcLyOyYODn3dF8wGjytro0nFTjp4MsoFvsAgD7mayppcseLvNSCO6Ac4-8b2SXe4/pub)

## Schema-less imports

For datasets with complex schema or ones that we want to import quickly, we can start with a schema-less import, and iteratively add schema. The “schema-less” part of this framework means that the SV is not yet fully defined. This lets us get the dataset into Data Commons without blocking on schema definition.

Links:
* [Schema-less Import Guide](https://docs.datacommons.org/import_dataset/schema_less_guide.html)
* [Import document template](https://docs.google.com/document/d/1GC7DTpxXo_3zreDRt7wFuURBfA1T275p-qx1N-VIdGM/)
* [Example](https://docs.google.com/document/d/e/2PACX-1vS6ItxH7T_XvYuz4-xeO9LKoYlrXr-YkrwiclRWcdtYm11J8OQHUwDw4E66uaTQA7yTdwLXfrNBdKgz/pub)

## Preparing artifacts

Once the entity and schema mapping have been finalized, you prepare the artifacts.  This includes:

1. StatisticalVariable MCF nodes (if any) checked into [schema repo](https://github.com/datacommonsorg/schema/tree/main/stat_vars). These nodes may be written by hand when there are only a handful in number. Otherwise, these nodes can be generated via scripts.
2. Template MCF and corresponding cleaned tabular files (typically CSV). Like StatisticalVariable MCF nodes, the Template MCF nodes can also be hand-written or script-generated depending on number of nodes.
3. Data cleaning code (along with README) checked into [data repo](https://github.com/datacommonsorg/data)
4. Validation results for the artifacts (from running [`dc-import`](https://github.com/datacommonsorg/import#using-import-tool) tool)

When all the artifacts are ready, please get it reviewed by the DC core team
via github Pull Requests. More details on this step are in the [Life of a
Dataset](life_of_a_dataset.md) document.
