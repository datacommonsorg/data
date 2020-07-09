# Importing EuroStat XXX Into Data Commons

> This README is a template of what an import's README might look like.

Author: <github_handle>

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

[CSV | XLSX | TXT | etc.] file is available for download from <download_url>.

### Overview
> The metadata for Population change - Demographic balance and crude rates at regional level (NUTS 3) is available online at [here](https://ec.europa.eu/eurostat/cache/metadata/en/demo_r_gind3_esms.htm)

NUTS (Nomenclature of Territorial Units for Statistics) is a hierarchical classification for dividing regions of Europe. NUTSi, starting at NUTS1, is the ith classification which is more detailed than the NUTS(i-1).

The format of each region’s NUTS3 GEO is two letters continued by 0,1,2, or 3 digits. 
Example: BE, BE1, BE21, BE254 


NUTS2 and NUTS3 can be accessed by dcid: nuts/xxx, typeOf:EurostatNUTS2, typeOf:EurostatNUTS3 (respectively) 
> Explain as much as you need so that others can understand what the
dataset's variables are without digging into the data and documentation.
Here's an example skeleton you may find helpful:

This dataset is broken up into 3 major families of variables:
1. XXX: <description_of_XXX>
2. YYY: <description_of_YYY>
3. ZZZ: <description_of_ZZZ>

X is further broken down into:
1. a: <description_of_a>
2. b: <description_of_b>

Y is further broken down into:
1. aa: <description_of_aa>
2. bb: <description_of_bb>
3. cc: <description_of_cc>

Z is further broken down into:
1. aaa: <description_of_aaa>
2. bbb: <description_of_bbb>

### Notes and Caveats

> Some example notes/caveats:

- This dataset considers Honolulu County a city.
- This dataset is a best-effort and occasionally contains decreasing
  numbers for cumulative count statistics.
- This dataset's documentation warns users not to compare across years
  due to <some_statistical_reason>.

### License

> An example license summary:

Eurostat has a policy of encouraging free re-use of its data, both for non-commercial and commercial purposes. 

The license is available online at [here](https://ec.europa.eu/eurostat/about/policies/copyright).

### Dataset Documentation and Relevant Links 

- Documentation: <documentation_url>
- Data Visualization UI: <some_other_url>

## About the Import

### Artifacts

#### Raw Data
- <file_name_with_hyperlink>: <file_description>
- <file_name_with_hyperlink>: <file_description>

#### Cleaned Data
- <file_name_with_hyperlink>: <file_description_if_not_obvious_from_name>
- <file_name_with_hyperlink>: <file_description_if_not_obvious_from_name>

#### Template MCFs
- <file_name_with_hyperlink>: <file_description_if_not_obvious_from_name>
- <file_name_with_hyperlink>: <file_description_if_not_obvious_from_name>

#### StatisticalVariable Instance MCF
- <file_name_with_hyperlink>: <file_description_if_not_obvious_from_name>
- <file_name_with_hyperlink>: <file_description_if_not_obvious_from_name>

#### Scripts
- <file_name_with_hyperlink>: <file_description>
- <file_name_with_hyperlink>: <file_description>

#### Notes
>#### available flags:
- b	break in time series	
- c	confidential	
- d	definition differs, see metadata
- e	estimated	
- f	forecast	
- n	not significant
- p	provisional	
- r	revised	
- s	Eurostat estimate
- u	low reliability	
- z	not applicable 
- Special value: ":" not available

- Please use the tsv file instead of csv.

> Include any import related notes here. Here's an example:

New starting 2020-06-25, two new columns were added:

- abc
- def

These two variables have not been integrated into the import yet.

### Import Procedure

> For this section, imagine walking someone through the procedure of
regenerating all artifacts in sequential order.

#### Pre-Processing Validation

> Include any steps, checks, and scripts you used to validate the source data.
  If you perform checks inside the processing script, simply make a note here.
  Here is an example of what someone might have done while getting familiar
  with and validating the source data:

Manual validation:
1. Examined the raw CSV and did not find identify any
  ill-formed values. 
2. Plotted a few columns using matplotlib for visual inspection.
  ```
  python3 plot_samples.py
  ```

Automated validation:
1. In the processing script (next section), there is an assert to check that
  all expected columns exist in the CSV.

#### Processing Steps

> Include any commands for running your scripts. This is especially relevant if
  your code relies on command line options. Also note that you may have
  kept the data download and cleaning in separate scripts. Here's an example:

`statvar_filename.mcf` was handwritten.

To generate `template_filename.tmcf` and `data_filename.csv`, run:

```bash
python3 process_csv.py
```

To run the test file `process_csv_test.py`, run:

```bash
python3 -m unittest process_csv_test
```

#### Post-Processing Validation

> While writing script tests help make sure processing outputs are as expected,
  also describe any steps, checks, and scripts you used to validate the
  resulting artifacts. Here is an example of what someone might have done to
  validate the artifacts.

- Wrote and ran
  [csv_template_mcf_compatibility_checker.py](https://github.com/datacommonsorg/data/blob/master/scripts/istat/geos/csv_template_mcf_compatibility_checker.py)
  to validate that the resulting CSV and Template MCF artifacts are
  compatible.
