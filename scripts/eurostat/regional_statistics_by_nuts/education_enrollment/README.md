# Importing EuroStat Education Enrollment (Participation Rate) Into Data Commons
Author: eftekhari-mhs

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

[TSV] file is available for download from [here](https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/trng_lfse_04.tsv.gz).

[Data explorer](https://appsso.eurostat.ec.europa.eu/nui/show.do?dataset=trng_lfse_04&lang=en)

### Overview

This dataset has the education enrollment rate (percentage) for EU countries down to their NUTS2 geos, according to the (NUTS2013-NUTS2016) classification. It has the enrollment rate categorized by Male/Female/Total for the years of [2000-2019]


The original dataset is broken up into 3 major families of variables:
1. Date: Years from 1990 to 2018 with some holes in time seris marked with note "b" in the original dataset
2. unit,sex,age,geo: e.g. PC,F,Y25-64,AT (Percent, Female, Years 25 to 64, nuts/AT)
3. value: some with note "e"="estimated" and "u" = "low reliability"

unit,sex,age,geo is further broken down into:
1. unit: Percentage
2. sex: T(Total), F(Female), M(Male)
3. age: 25 to 64 years old
4. geo: NUTS2 codes for regions of Europe

The cleraned csv is broken up into 5 major families of variables:
1. Date: Subset of years from 1990 to 2018 with values in the original dataset
2. GeoID: NUTS3 codes
3. Count_Person_25To64Years_EnrolledInEducationOrTraining_AsAFractionOfCount_Person_25To64Years: float values 
4. Count_Person_25To64Years_EnrolledInEducationOrTraining_Female_AsAFractionOfCount_Person_25To64Years_Female: float values 
5. Count_Person_25To64Years_EnrolledInEducationOrTraining_Male_AsAFractionOfCount_Person_25To64Years_Male: float values 


### Notes and Caveats

- There are breaks in the time series of the original dataset. Note =”b”, value=":"
- There are estimated values in the original dataset. Note =”e”
- There are values with low reliability. Note = "u"
- As written, we're imporing the estimated and low reliable values as regular values.


### License

Eurostat has a policy of encouraging free re-use of its data, both for non-commercial and commercial purposes. 

The license is available online at [here](https://ec.europa.eu/eurostat/about/policies/copyright).

### Dataset Documentation and Relevant Links 

- Documentation: <https://ec.europa.eu/eurostat/cache/metadata/en/demo_r_gind3_esms.htm>

## About the Import

### Artifacts

#### Raw Data
[trng_lfse_04.tsv](./trng_lfse_04.tsv)

#### Cleaned Data
[Eurostats_NUTS2_Enrollment.csv](./Eurostats_NUTS2_Enrollment.csv)

#### Template MCFs
[Eurostats_NUTS2_Enrollment.tmcf](./Eurostats_NUTS2_Enrollment.tmcf)

#### StatisticalVariable Instance MCF
[Eurostats_NUTS2_Enrollment.mcf](./Eurostats_NUTS2_Enrollment.mcf)

#### Scripts
[education_enrollment_preprocess_gen_tmcf.py](./education_enrollment_preprocess_gen_tmcf.py)

#### Pre-Processing Validation

Automated validation:
1. In the processing script (next section), there assertion to check numerical values are correctly formatted.

#### Processing Steps

`PopulationDensity_Eurostat_NUTS3.mcf` was handwritten.

To generate `Eurostats_NUTS2_Enrollment.tmcf` and `Eurostats_NUTS2_Enrollment.csv`, run:

```bash
python3 education_enrollment_preprocess_gen_tmcf.py
```

#### Post-Processing Validation

- Wrote and ran
  [csv_template_mcf_compatibility_checker.py](./csv_template_mcf_compatibility_checker.py)
  to validate that the resulting CSV and Template MCF artifacts are
  compatible.
