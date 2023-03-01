# Life of a dataset

> Note: this document assumes familiarity with how [statistics is represented in
> Data Commons](representing_statistics.md) and the [MCF format](mcf_format.md).

This tutorial walks through the process of structuring and inserting data into
the Data Commons graph.

As a prerequisite, you should understand the dataset, and have an idea of how
to map location entities in your dataset to Data Commons entities and measures
in your dataset to Data Commons statistical variables.

## Import Design Review

Begin by making sure you've completed the import document template (as per the 
[README.md](README.md)) and worked with the DC team to review your design. Once 
your schema mapping/statistical variable (SV) categories have been reviewed and 
finalized, proceed to the next section on how to define your SVs. 


## Define Statistical Variables

If you are adding new types of data to the knowledge graph, you might need to
define new [statistical variables](representing_statistics.md). You can browse
all existing variables in the [Statistical Variable
Explorer](https://datacommons.org/tools/statvar).

The statistical variable DCIDs should be human-readable, encapsulating the
meaning of its triples.  The naming rules are summarized in [this
doc](https://docs.google.com/document/d/1YtmQu_gOXENt4W2lmlK-8Mtnw_XB3kZlLBjSN-gT0oE/preview#bookmark=kix.bdksa8hbv3si).

You'll need approval from the Data Commons team on any new variables (see the 
"Defining location and schema mapping" section 
[here](https://github.com/datacommonsorg/data/blob/master/docs/README.md)). 

When the variables are finalized, they get checked into the [schema 
repo](https://github.com/datacommonsorg/schema/tree/main/stat_vars).

## Template MCF with tabular data (CSV)

Template MCF is essentially a mapping file that instructs how to convert the
data in a CSV into graph nodes for ingestion into Data Commons.  For additional
information, read [Template
MCF](https://github.com/datacommonsorg/data/blob/master/docs/mcf_format.md#template-mcf).

The raw CSV will often needs pre-processing before it can be imported.  An
example simple cleaning script is
[here](https://github.com/datacommonsorg/data/blob/master/scripts/covid_tracking_project/historic_state_data/preprocess_csv.py).

There are no restrictions on your approach for this step, but the only
requirement is that a property value in the TMCF maps to a single CSV column (as
illustrated in the examples in [MCF format](mcf_format.md)).

The general guidelines are:

1. A property in the Template MCF node should have a constant value (like `typeOf`), reference to another node (like `E:Dataset->E1`), or refer to a CSV column for its value (like `C:Dataset->col_name`).
1. Dates must be in [ISO 8601 format](https://www.w3.org/TR/NOTE-datetime): "YYYY-MM-DD", "YYYY-MM", etc.
1. References to existing nodes in the graph must be `dcid`s.
1. The cleaning script is reproducible and easy to run. Python or Golang is recommended.

There are a couple of ways to map the statistical variables with TMCF:

1. Each
   [`StatisticalVariable`](https://datacommons.org/browser/StatisticalVariable)
   has its own column for its observed value.  So, there are as many TMCF
   `StatVarObservation` nodes as variables. For an example, see [this
   TMCF](https://github.com/datacommonsorg/data/blob/master/scripts/covid_tracking_project/historic_state_data/test_expected_tmcf.tmcf)
   and the [corresponding CSV](https://github.com/datacommonsorg/data/blob/master/scripts/covid_tracking_project/historic_state_data/test_csv.csv).
1. The `StatisticalVariable` DCIDs are included in CSV values, such that there
   is a single TMCF `StatVarObservation` node that points to the variable
   column. For an example, see [this TMCF](https://github.com/datacommonsorg/data/blob/master/scripts/india_census/primary_census_abstract_data/IndiaCensus2011_Primary_Abstract_Data.tmcf)
   and the [corresponding CSV](https://github.com/datacommonsorg/data/blob/master/scripts/india_census/primary_census_abstract_data/IndiaCensus2011_Primary_Abstract_Data.csv).

TIP: To represent DC strings and repeated values in a CSV field, refer to these
[CSV Formatting Tips](formatting_tips.md).

## Validate the artifacts

Use the [`dc-import`](https://github.com/datacommonsorg/import#using-import-tool) tool to validate the artifacts. When you run it, it will generate `report.json` and `summary_report.html` with counters representing warnings/errors and summary statistics.

## Send Pull Requests

Create a Pull Request (PR) with the Template MCF file together with the cleaned CSV, its preprocessing script, and the README ([template](https://github.com/datacommonsorg/data/tree/master/scripts/example_provenance/example_dataset)) to [https://github.com/datacommonsorg/data](https://github.com/datacommonsorg/data) under the appropriate [`scripts/<provenance>/<dataset>` subdirectory](https://github.com/datacommonsorg/data/tree/master/scripts/india_census/primary_census_abstract_data). If you wrote a script to automate the generation of the TMCF, please also include that.

In the PR, please also include the validation results (`report.json` and `summary_report.html`).

If you introduced new statistical variables, please create a Pull Request for them in the [schema repo](https://github.com/datacommonsorg/schema).

## Manifesting Artifacts

After your PR is reviewed and approved, the Data Commons team will work with you to manifest (e.g. generate for inclusion in our model) the artifacts you've created in our internal system. Only after the artifacts are manifested will they be added to the Data Commons graph and be accessible.

## Alternate approach: Generate Instance MCF

In some cases, a dataset is so highly unstructured that it makes sense to skip
the Template MCF / CSV approach and directly generate the instance MCF. For
example, data from biological sources frequently needs to be directly formatted
as MCF.

In this case, the cleaning script should do more heavy-lifting to generate
instance MCFs.  Such an example script is
[here](https://github.com/datacommonsorg/data/tree/master/scripts/biomedical/proteinInteractionMINT).
