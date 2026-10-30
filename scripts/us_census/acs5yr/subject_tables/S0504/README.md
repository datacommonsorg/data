# US Census ACS5YR S0504 Subject Table Import

The table provides data on the selected characteristics of the foreign-born population in the United States by world region of birth:

- Foreign born; Born in Africa
- Foreign born; Born in Northern America
- Foreign born; Born in Oceania

The data is sliced by the following properties:

- nativity
- placeOfBirth
- citizenship
- dateOfEntry
- gender
- age
- race
- householdType
- maritalStatus
- schoolEnrollment
- levelOfSchool
- educationalAttainment
- languageSpokenAtHome
- abilityToSpeakEnglish
- employmentStatus
- armedForcesStatus
- employment
- establishmentOwnership
- workerClassification
- occupation
- naics
- incomeStatus
- earnings
- workStatus
- benefitsStatus
- povertyStatus
- memberStatus
- occupancyStatus
- occupancyTenure
- numberOfRooms
- numberOfOccupants
- numberOfVehicles
- telephoneServiceAvailability
- grossRent
- ownerCost

## Commands to execute the script

To execute the process script from `scripts/us_census/acs5yr/subject_tables`:

```shell
python3 process.py \
  --option=all \
  --table_prefix=S0504 \
  --has_percent=True \
  --debug=False \
  --spec_path=S0504/S0504_spec.json \
  --input_path=S0504/S0504.zip \
  --output_dir=S0504/output
```

## Output Artifacts

Running the command above generates the following files in `S0504/output`:

- `S0504_cleaned.csv`: Cleaned observation data across all years and geographies.
- `S0504_output.mcf`: Generated StatisticalVariable schema nodes.
- `S0504_output.tmcf`: Template MCF mapping `S0504_cleaned.csv` columns to Data Commons schema.
- `S0504_summary.json`: Summary of observation counts and StatVars per year.
- `column_map.json`: Column mapping configuration per release year.

Years: 2010-2024  
Geo: Country, Census Division, State, County, County Subdivision, Census Tract, Block Group, Place, Metropolitan/Micropolitan Statistical Area (CBSA), Congressional District, School District, and ZCTA
