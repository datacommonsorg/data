# Importing EuroStat Regional Statistics by NUTS Into Data Commons

> This README is a template of what an import's README might look like.

Author: eftekhari-mhs

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

[TSV] file is available for download from <https://ec.europa.eu/eurostat/data/database> under 'Data navigation tree > Database by themes > General and regional statistics > Regional statistics by NUTS classification (reg)'.

### Overview
> The metadata for each dataset is available online at '<https://ec.europa.eu/eurostat/cache/metadata/en/<dataset name>_esms.htm>'

NUTS (Nomenclature of Territorial Units for Statistics) is a hierarchical classification for dividing regions of Europe. 

Useful links: [NUTS Background](https://ec.europa.eu/eurostat/web/nuts/background), 
[NUTS Map](https://ec.europa.eu/eurostat/web/nuts/nuts-maps)

##### Imported datasets (P0): 

- Population density (by NUTS3)
- Birth, deaths, and migrations (by NUTS3)
- Life expectancy by age and gender (by NUTS2)

##### Imported datasets (P1): 

- Moratality rate by cause (NUTS2)
- Fertility rate, median and mean age of mothers at childbirth (by NUTS3)
- Various measures of GDP (by NUTS3)
- Education enrollment by gender (by NUTS2)
- Education Attainment by gender (by NUTS2)
- Employed per sector (by NUTS3)

### License

Eurostat has a policy of encouraging free re-use of its data, both for non-commercial and commercial purposes. 

The license is available online at [here](https://ec.europa.eu/eurostat/about/policies/copyright).



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
