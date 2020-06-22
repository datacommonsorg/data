# Importing CHHS Licensed and Certified Healthcare Facility Bed Types and Counts

This directory contains artifacts required for importing
CHHS Licensed and Certified Healthcare Facility Bed Types and Counts
into Data Commons, along with scripts used to generate these artifacts.

## Metadata:
[Licensed and Certified Healthcare Facility Bed Types and Counts](https://data.chhs.ca.gov/dataset/healthcare-facility-bed-types-and-counts)

This whole dataset is about licensed healthcare facility bed types and counts in California. It gives some statistics value for healthcare facilities and hospital beds in CA. Furthermore, this whole dataset contains two data tables.:
* Dataset 1: [Licensed and Certified Healthcare Facility Bed Types and Counts](https://data.chhs.ca.gov/dataset/09b8ad0e-aca6-4147-b78d-bdaad872f30b/resource/0997fa8e-ef7c-43f2-8b9a-94672935fa60/download/healthcare_facility_beds.xlsx)
* Dataset 2: [County General Acute Care Hospitals (GACH) Bed Types and Counts](https://data.chhs.ca.gov/dataset/09b8ad0e-aca6-4147-b78d-bdaad872f30b/resource/d6599aac-ff5e-4693-a295-9f9d646a1f06/download/ca_county_gach_bed_counts.xlsx)

## Artifacts:

- [CA_Licensed_Healthcare_Facility_Types_And_Counts.csv](CA_Licensed_Healthcare_Facility_Types_And_Counts.csv): the cleaned CSV for dataset 1.
- [CA_Licensed_Healthcare_Facility_Types_And_Counts.tmcf](CA_Licensed_Healthcare_Facility_Types_And_Counts.tmcf): the mapping file (Template MCF) for dataset 1.
- [CA_Licensed_Healthcare_Facility_Types_And_Counts.mcf](CA_Licensed_Healthcare_Facility_Types_And_Counts.mcf): the new StatisticalVariables defined for dataset 1.
- [CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.csv](CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.csv): the cleaned CSV for dataset 2.
- [CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.tmcf](CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.tmcf): the mapping file (Template MCF) for dataset 2.
- [CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.mcf](CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.mcf): the new StatisticalVariables defined for dataset 2.

## Generating Artifacts:

`CAHealthcare_Facility_Bed_Counts_And_Types_StatisticalVariables.mcf` was handwritten.

To generate `CA_Licensed_Healthcare_Facility_Types_And_Counts.csv`, `CA_Licensed_Healthcare_Facility_Types_And_Counts.tmcf`, `CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.csv` and `CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.tmcf`, run:

```bash
python3 preprocess_csv.py
```
