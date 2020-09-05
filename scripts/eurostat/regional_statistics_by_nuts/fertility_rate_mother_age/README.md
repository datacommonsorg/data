# Importing EuroStat Education Attainment Into Data Commons
Author: eftekhari-mhs

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

[TSV] file is available for [download](https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/demo_r_find3.tsv.gz).

[Data explorer](https://appsso.eurostat.ec.europa.eu/nui/show.do?dataset=demo_r_find3&lang=en)

### Overview

This dataset has the fertility rate, median and mean age of mother at childbirth for European Union (EU) countries to their NUTS3 geos over [2013-2018]. Codes used in the dataset: 

- TOTFERRT – Total fertility rate.
- AGEMOTH – Mean age of women at childbirth.
- MEDAGEMOTH – Median age of women at childbirth.


The original dataset is broken up into 3 major families of variables:
1. Date: Years from 2013 to 2018 with some holes in time series marked with note "b" in the original dataset
2. indic_de,unit,geo: e.g. AGEMOTH,YR,AL	 (Mean age of women at childbirth, Years, nuts/AL)

indic_de,unit,geo is further broken down into:
1. indic_de: 'TOTFERRT', 'AGEMOTH', 'MEDAGEMOTH'
2. unit: 'YR' (age), 'NR' (fertility rate)
3. geo: NUTS3 codes for regions of Europe

The cleaned csv is broken up into the following major families of variables:
1. Date: Subset of years from 2000 to 2019 with values in the original dataset
2. GeoID: NUTS3 codes
3. MeanMothersAge_BirthEvent: float values 
4. MedianMothersAge_BirthEvent: float values 
5. FertilityRate_Person_Female: float values 


### Notes and Caveats

- There are breaks in the time series of the original dataset. Note =”b”, value=":"

### License

Eurostat has a policy of encouraging free re-use of its data, both for non-commercial and commercial purposes. 

The license is [available](https://ec.europa.eu/eurostat/about/policies/copyright).

### Dataset Documentation and Relevant Links 

- Documentation: <https://ec.europa.eu/eurostat/cache/metadata/en/demo_r_gind3_esms.htm>

## About the Import

### Artifacts

#### Cleaned Data
[Eurostats_NUTS3_FRate_Age.csv](./Eurostats_NUTS3_FRate_Age.csv)

#### Template MCFs
[Eurostats_NUTS3_FRate_Age.tmcf](./Eurostats_NUTS3_FRate_Age.tmcf)

#### StatisticalVariable Instance MCF
[Eurostats_NUTS3_FRate_Age.mcf](./Eurostats_NUTS3_FRate_Age.mcf)

#### Scripts
[fertility_rate_preprocess_gen_tmcf.py](./fertility_rate_preprocess_gen_tmcf.py)

#### Pre-Processing Validation

Automated validation:
1. In the processing script (next section), assert to check numerical values are correctly formatted.

#### Processing Steps

`Eurostats_NUTS3_FRate_Age.mcf` was handwritten.

To generate `Eurostats_NUTS3_FRate_Age.tmcf` and `Eurostats_NUTS3_FRate_Age.csv`, run:

```bash
python3 fertility_rate_preprocess_gen_tmcf.py
```

#### Post-Processing Validation

- Wrote and ran
  [csv_template_mcf_compatibility_checker.py](./csv_template_mcf_compatibility_checker.py)
  to validate that the resulting CSV and Template MCF artifacts are
  compatible.
