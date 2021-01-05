# Importing EuroStat Education Attainment Into Data Commons

Author: eftekhari-mhs

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [About the Import](#about-the-import)

## About the Dataset

This dataset has the employee per sector (thousand persons) for European Union (EU) countries specified by their NUTS3 geos.

It has the employees and employed persons counts categorized by NACE classification for 15 different economic activities in [1995-2018]. The NACE categories are as follows:

- Total – All NACE activities.
- A – Agriculture, forestry and fishing.
- B-E – Industry (except construction).
- C – Manufacturing.
- F – Construction.
- G-J – Wholesale and retail trade, transport, accommodation and food service activities, information and communication.
- G-I – Wholesale and retail trade, transport, accommodation and food service activities.
- J – Information and communication.
- K-N – Financial and insurance activities, real estate activities, professional, scientific and technical activities, administrative and support service activities.
- K – Financial and insurance activities.
- L – Real estate activities.
- M_N – Professional, scientific and technical activities, administrative and support service activities
- O-U – Public administration and defence, compulsory social security, education, human health and social work activities, arts, entertainment and recreation... .
- O-Q – Public administration, defence, education, human health and social work activities.
- R-U – Arts, entertainment and recreation, other service activities, activities of household and extra-territorial organizations and bodies.

### Download URL

[TSV] file is available for [download](https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/nama_10r_3empers.tsv.gz).

### License

See parent README.

### About the TSV

The original dataset is broken up into the following columns:

1. `Date`: Years from 1995 to 2018 with some holes in time series marked with note "b" in the original dataset
2. `nace_r2,wstatus,unit,geo`: e.g. THS,EMP,A,AT (Thousand, Employed Person, NACE/A, nuts/AT)
3. `value`: some with note "p" = "provisional", "u" = "low reliability", and "d" = "definition differs"

`nace_r2,wstatus,unit,geo` is further broken down into:

1. wstatus-nace: 'EMP_A', 'EMP_B-E', 'EMP_C','EMP_F', 'EMP_G-I', 'EMP_G-J', 'EMP_J', 'EMP_K', 'EMP_K-N', 'EMP_L', 'EMP_M_N', 'EMP_O-Q', 'EMP_O-U', 'EMP_R-U', 'EMP_TOTAL'
2. unit: Thousand
3. geo: NUTS3 codes for regions of Europe

### Dataset Documentation and Relevant Links

- Documentation: <https://ec.europa.eu/eurostat/cache/metadata/en/reg_eco10_esms.htm>
- [Data explorer](https://appsso.eurostat.ec.europa.eu/nui/show.do?dataset=nama_10r_3empers&lang=en)

### Notes and Caveats

- There are breaks in the time series of the original dataset. Note =”b”, value=":"
- There are estimated values in the original dataset. Note =”e”
- There are provisional values. Note = "p"
- There are values that definition differs. Note = "d"
- As written, we're importing the estimated, low reliable, and different definitions values as regular values.

## About the Import

### Artifacts

#### Cleaned Data

[Eurostats_NUTS3_Empers.csv](./Eurostats_NUTS3_Empers.csv)

#### Template MCFs

[Eurostats_NUTS3_Empers.tmcf](./Eurostats_NUTS3_Empers.tmcf)

#### StatisticalVariable Instance MCF

[Eurostats_NUTS3_Empers.mcf](./Eurostats_NUTS3_Empers.mcf)

#### Scripts

[emp_persec_preprocess_gen_tmcf.py](./emp_persec_preprocess_gen_tmcf.py)

### Processing Steps

`Eurostats_NUTS3_Empers.mcf` is handwritten.

To generate `Eurostats_NUTS3_Empers.tmcf` and `Eurostats_NUTS3_Empers.csv`, run:

```bash
python3 emp_persec_preprocess_gen_tmcf.py
```

### Post-Processing Validation

- Wrote and ran
  [csv_template_mcf_compatibility_checker.py](./csv_template_mcf_compatibility_checker.py)
  to validate that the resulting CSV and Template MCF artifacts are
  compatible.
