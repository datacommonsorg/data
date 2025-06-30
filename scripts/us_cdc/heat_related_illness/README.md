# Importing EPH Heat and Heat-related Illness data

This directory imports [Heat and Heat-related Illness](https://ephtracking.cdc.gov/qrlist/35) from EPH Tracking into Data Commons. It includes data at a state level.

## Cleaning source data
The source data is available from the EPH [website](https://ephtracking.cdc.gov/qrlist/35). Currently, this import brings in data related to [Heat-related Emergency Department Visits](https://ephtracking.cdc.gov/qrd/438), [Heat-Related Mortality](https://ephtracking.cdc.gov/qrd/370), and [Heat-related Hospitalizations](https://ephtracking.cdc.gov/qrd/431).

All the source urls are added in the `configs.py` file.

To download and clean the source data, run:

`python clean_data.py`

Note:

The `clean_data.py` script downloads HTML files from the source URL and converts them into CSV files. These multiple CSV files are then combined into a single CSV file for each of the following categories: hospitalizations, hospitalizations_age, hospitalizations_gender, hospitalizations_age_by_gender, edVisits, edVisits_age, edVisits_gender, edVisits_age_by_gender, and deaths.
The final CSV input files are available in the `input_files/` directory.

## Generating artifacts at a State level & Aggregating at a Country level:
Artifacts are generated based on the cleaned data.
Specifically, the state-level `output_files/cleaned.csv` output file serve as an input for country-level aggregation. This aggregation is achieved by summing their values, and the final country-level data is output to `output_files/country_output.csv`.


`cleaned.csv`: This is the final output CSV file at state level including all the categories (hospitalizations, hospitalizations_age, hospitalizations_gender, hospitalizations_age_by_gender, edVisits, edVisits_age, edVisits_gender, edVisits_age_by_gender, and deaths)

`output.mcf`: An MCF file which includes the statistical variable descriptions. For example,
```
    Node: dcid:Count_MedicalConditionIncident_SummerSeason_ConditionHeatStress_PatientDeceased
    populationType: dcs:MedicalConditionIncident
    medicalStatus: dcs:PatientDeceased
    medicalCondition: dcs:HeatStress
    climaticSeason: dcs:SummerSeason
    measuredProperty: dcs:count
    statType: dcs:measuredValue
    typeOf: dcs:StatisticalVariable
```

`output.tmcf`: A TMCF file which describes the template of the output data. This file is used as a common TMCF for both state and country level data. For example,
```
    Node: E:EPHHeatIllness->E0
    typeOf: dcs:StatVarObservation
    measurementMethod: C:EPHHeatIllness->measurementMethod
    observationAbout: C:EPHHeatIllness->Geo
    observationDate: C:EPHHeatIllness->Year
    variableMeasured: C:EPHHeatIllness->StatVar
    observationPeriod: P5M
    value: C:EPHHeatIllness->Quantity
```

`country_output.csv`: Final output file at country level, generated after aggregating the state-level data from `output_files/cleaned.csv`.

To generate `cleaned.csv`, `output.mcf`, `output.tmcf` and `country_output.csv`run:

```bash
python preprocess.py
```

## Data Caveats:
- Suppressed data points are skipped.
- Data for heat related deaths is heavily suppressed.
- State level data is aggregated to get the country level data.
