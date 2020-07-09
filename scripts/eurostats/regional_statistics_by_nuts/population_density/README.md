# Importing EuroStat Population Density Into Data Commons
Author: eftekhari-mhs

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

[TSV] file is available for download from [here](https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/demo_r_d3dens.tsv.gz).

### Overview
The metadata is available online at [here](https://ec.europa.eu/eurostat/cache/metadata/en/demo_r_gind3_esms.htm)

NUTS (Nomenclature of Territorial Units for Statistics) is a hierarchical classification for dividing regions of Europe. NUTSi, starting at NUTS1, is the ith classification which is more detailed than the NUTS(i-1). We’re importing population density for regions in the NUTS3 classification.
Having NUTS1 as the first layer of classification which subdivides countries into 92 regions. The NUTS3 is the third layer of this classification subdividing more (total of 1215 regions). The format of each region’s NUTS3 GEO is two letters continued by 0,1,2, or 3 numbers. 
Example: BE, BE1, BE21, BE254 

This dataset has the population density (per square kilometer) for the regions of NUTS3 according to the (NUTS2013-NUTS2016) classification. It has population density for the years of [1990-2018] with some breaks in time series for some regions. (Mentioned in the original dataset with note “b”= “breaks in the time series”)


The original dataset is broken up into 3 major families of variables:
1. Date: Years from 1990 to 2018 with some holes in time seris marked with note "b" in the original dataset
2. unit,geo: e.g. PER_KM2,AL	
3. value: population density which is person count per square kilometer, some with note "e"="estimated"

unit,geo is further broken down into:
1. unit: person per KM2
2. geo: NUTS3 codes for regions of Europe

The cleraned csv is broken up into 3 major families of variables:
1. Date: Subset of years from 1990 to 2018 with values in the original dataset
2. GeoID: NUTS3 codes
3. Count_Person_AsAFractionOfArea: float values 

### Notes and Caveats

- There are breaks in the time series of the original dataset. Note =”b”, value=":"
- There are estimated values in the original dataset. Note =”e”
- Downloading csv from the browser includes the data for years 2014-2018. To get full access to all data points for years between 1990 and 2018 one must download the tsv file instead.


### License

Eurostat has a policy of encouraging free re-use of its data, both for non-commercial and commercial purposes. 

The license is available online at [here](https://ec.europa.eu/eurostat/about/policies/copyright).

### Dataset Documentation and Relevant Links 

- Documentation: <documentation_url>
- Data Visualization UI: <some_other_url>

## About the Import

### Artifacts

#### Raw Data
[demo_r_d3dens.tsv](./demo_r_d3dens.tsv)

#### Cleaned Data
[PopulationDensity_Eurostat_NUTS3.csv](./PopulationDensity_Eurostat_NUTS3.csv)

#### Template MCFs
[PopulationDensity_Eurostat_NUTS3.tmcf](./PopulationDensity_Eurostat_NUTS3.tmcf)

#### StatisticalVariable Instance MCF
[PopulationDensity_Eurostat_NUTS3.mcf](./PopulationDensity_Eurostat_NUTS3.mcf)

#### Scripts
[PopulationDensity_preprocess_gen_tmcf.py](./PopulationDensity_preprocess_gen_tmcf.py)

### Import Procedure

#### Pre-Processing Validation

Manual validation:
1. Examined the raw CSV and did not find identify any
  ill-formed values. 

Automated validation:
1. In the processing script (next section), there is an assert to check that
  all expected columns exist in the CSV.

#### Processing Steps

> Include any commands for running your scripts. This is especially relevant if
  your code relies on command line options. Also note that you may have
  kept the data download and cleaning in separate scripts. Here's an example:

`PopulationDensity_Eurostat_NUTS3.mcf` was handwritten.

To generate `PopulationDensity_Eurostat_NUTS3.tmcf` and `PopulationDensity_Eurostat_NUTS3.csv`, run:

```bash
python3 PopulationDensity_preprocess_gen_tmcf.py
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
