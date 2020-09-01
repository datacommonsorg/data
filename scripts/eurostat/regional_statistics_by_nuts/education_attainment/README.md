# Importing EuroStat Education Attainment Into Data Commons
Author: eftekhari-mhs

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

[TSV] file is available for [download](https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/edat_lfse_04.tsv.gz).

[Data explorer](https://appsso.eurostat.ec.europa.eu/nui/show.do?dataset=edat_lfse_04&lang=en)

### Overview

This dataset has the education attainment rate (percentage) for European Union (EU) countries to their NUTS2 geos. It has the attainment rate categorized by Male/Female/Total for 4 different levels of education for the intervals of [0-2], [3-8], [3-4], [5-8], where the digits are based on ISCED standard explained as follows:

ISCED standard education levels: 

- Level 0 – Less than primary education
- Level 1 – Primary education
- Level 2 – Lower secondary education
- Level 3 – Upper secondary education
- Level 4 – Post-secondary non-tertiary education
- Level 5 – Short-cycle tertiary education
- Level 6 – Bachelor’s or equivalent level
- Level 7 – Master’s or equivalent level
- Level 8 – Doctoral or equivalent level 


The original dataset is broken up into 3 major families of variables:
1. Date: Years from 2000 to 2019 with some holes in time seris marked with note "b" in the original dataset
2. sex,edu-level,age,unit,geo: e.g. F,ED0-2,Y25-64,PC,AT (Female, Lower Secondary or less,Years 25 to 64, Percent, nuts/AT)
3. value: some with note "e"="estimated", "u" = "low reliability", and "d"="definition differs"

sex,edu-level,age,unit,geo is further broken down into:
1. sex-level: 'F_ED0-2', 'F_ED3-8', 'F_ED3_4','F_ED5-8', 'M_ED0-2', 'M_ED3-8', 'M_ED3_4', 'M_ED5-8', 'T_ED0-2', 'T_ED3-8', 'T_ED3_4', 'T_ED5-8'
2. age: 25 to 64 years old
3. unit: Percentage
4. geo: NUTS2 codes for regions of Europe

The cleaned csv is broken up into 5 major families of variables:
1. Date: Subset of years from 2000 to 2019 with values in the original dataset
2. GeoID: NUTS2 codes
3. Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_25To64Years: float values 
4. Count_Person_25To64Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_25To64Years: float values 
5. Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOfCount_Person_25To64Years: float values 
6. Count_Person_25To64Years_TertiaryEducation_AsAFractionOfCount_Person_25To64Years: float values 
7. Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female: float values 
8. Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_25To64Years_Female: float values 
9. Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female: float values 
10. Count_Person_25To64Years_TertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female: float values 
11. Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male: float values 
12. Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_25To64Years_Male: float values 
13. Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male: float values 
14. Count_Person_25To64Years_TertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male: float values 


### Notes and Caveats

- There are breaks in the time series of the original dataset. Note =”b”, value=":"
- There are estimated values in the original dataset. Note =”e”
- There are values with low reliability. Note = "u"
- There are values that definition differs. Note = "d"
- As written, we're importing the estimated, low reliable, and different definitions values as regular values.


### License

Eurostat has a policy of encouraging free re-use of its data, both for non-commercial and commercial purposes. 

The license is [available](https://ec.europa.eu/eurostat/about/policies/copyright).

### Dataset Documentation and Relevant Links 

- Documentation: <https://ec.europa.eu/eurostat/cache/metadata/en/edat1_esms.htm>

## About the Import

### Artifacts

#### Raw Data
[edat_lfse_04.tsv](./edat_lfse_04.tsv)

#### Cleaned Data
[Eurostats_NUTS2_Edat.csv](./Eurostats_NUTS2_Edat.csv)

#### Template MCFs
[Eurostats_NUTS2_Edat.tmcf](./Eurostats_NUTS2_Edat.tmcf)

#### StatisticalVariable Instance MCF
[Eurostats_NUTS2_Edat.mcf](./Eurostats_NUTS2_Edat.mcf)

#### Scripts
[education_attainment_preprocess_gen_tmcf.py](./education_attainment_preprocess_gen_tmcf.py)

#### Pre-Processing Validation

Automated validation:
1. In the processing script (next section), assert to check numerical values are correctly formatted.

#### Processing Steps

`Eurostats_NUTS2_Edat.mcf` and `Eurostats_NUTS2_Edat_Enum.mcf` were handwritten.

To generate `Eurostats_NUTS2_Edat.tmcf` and `Eurostats_NUTS2_Edat.csv`, run:

```bash
python3 education_attainment_preprocess_gen_tmcf.py
```

#### Post-Processing Validation

- Wrote and ran
  [csv_template_mcf_compatibility_checker.py](./csv_template_mcf_compatibility_checker.py)
  to validate that the resulting CSV and Template MCF artifacts are
  compatible.
