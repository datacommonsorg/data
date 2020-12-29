# Importing EuroStat Education Enrollment (Participation Rate) Into Data Commons

Author: eftekhari-mhs

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [About the Import](#about-the-import)

## About the Dataset

This dataset has the education enrollment rate (percentage) for European Union (EU) countries down to their NUTS2 geos, according to the (NUTS2013-NUTS2016) classification.

It has the enrollment rate for the years of [2000-2019] categorized by

- Male/Female/Total

### Raw Data

[TSV] file is available for [download](https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/trng_lfse_04.tsv.gz).

The original dataset is broken up into 3 columns:

1. Date: Years from 2000 to 2019 with some holes in time series marked with note "b" in the original dataset
2. unit,sex,age,geo: e.g. PC,F,Y25-64,AT (Percent, Female, Years 25 to 64, nuts/AT)
3. value: some with note "e"="estimated" and "u" = "low reliability"

unit,sex,age,geo is further broken down into:

1. unit: Percentage
2. sex: T(Total), F(Female), M(Male)
3. age: 25 to 64 years old
4. geo: NUTS2 codes for regions of Europe

### Dataset Documentation and Relevant Links

- Documentation: <https://ec.europa.eu/eurostat/cache/metadata/en/trng_lfs_4w0_esms.htm>
- [Data explorer](https://appsso.eurostat.ec.europa.eu/nui/show.do?dataset=trng_lfse_04&lang=en)

### License

See parent README.

### Notes and Caveats

- There are breaks in the time series of the original dataset. Note =”b”, value=":"
- There are estimated values in the original dataset. Note =”e”
- There are values with low reliability. Note = "u"
- As written, we're importing the estimated and low reliable values as regular values.

## About the Import

### Artifacts

#### Raw Data

[trng_lfse_04.tsv](./trng_lfse_04.tsv)

#### Cleaned Data

[Eurostats_NUTS2_Enrollment.csv](./Eurostats_NUTS2_Enrollment.csv)

#### Template MCFs

[Eurostats_NUTS2_Enrollment.tmcf](./Eurostats_NUTS2_Enrollment.tmcf)

#### StatisticalVariables

This import uses StatVars in the Data Commons graph:

- [Count_Person_25To64Years_EnrolledInEducationOrTraining_AsAFractionOfCount_Person_25To64Years](http://datacommons.org/browser/Count_Person_25To64Years_EnrolledInEducationOrTraining_AsAFractionOfCount_Person_25To64Years)
- [Count_Person_25To64Years_EnrolledInEducationOrTraining_Female_AsAFractionOfCount_Person_25To64Years_Female](http://datacommons.org/browser/Count_Person_25To64Years_EnrolledInEducationOrTraining_Female_AsAFractionOfCount_Person_25To64Years_Female)
- [Count_Person_25To64Years_EnrolledInEducationOrTraining_Male_AsAFractionOfCount_Person_25To64Years_Male](http://datacommons.org/browser/Count_Person_25To64Years_EnrolledInEducationOrTraining_Male_AsAFractionOfCount_Person_25To64Years_Male)

#### Scripts

[education_enrollment_preprocess_gen_tmcf.py](./education_enrollment_preprocess_gen_tmcf.py)

### Import Procedure

#### Generating Import Artifacts

`Eurostats_NUTS2_Enrollment.mcf` was handwritten.

To generate `Eurostats_NUTS2_Enrollment.tmcf` and `Eurostats_NUTS2_Enrollment.csv`, run:

```bash
python3 education_enrollment_preprocess_gen_tmcf.py
```

#### Post-Processing Validation

Run
[csv_template_mcf_compatibility_checker.py](./csv_template_mcf_compatibility_checker.py)
to validate that the resulting CSV and Template MCF artifacts are
compatible.
