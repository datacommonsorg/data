# US Census ACS5YR S0804 Subject Table Import

The table provides data on the number of people who commute to work by means of transportation. The movement is classified under one of the following types:

- Car, truck, or van - Drove Alone
- Car, truck, or van - Carpooled
- Public transportation (excluding taxicab) (2010–2018) / Public transportation (2019–2024)
- Worked from home

The data is sliced by the following properties:

- age
- incomeStatus
- gender
- race
- ethnicity
- employmentStatus
- commuteMode
- numberOfVehiclesInHousehold
- commuteTime
- commuteStartTime
- income
- placeOfWork
- languageSpokenAtHome
- abilityToSpeakEnglish
- nativity
- citizenship
- povertyStatus
- occupation
- commuteType
- residenceType
- naics
- workerClassification
- occupancyTenure
- occupancyStatus

## Commands to execute the script

To execute the process script from `scripts/us_census/acs5yr/subject_tables`:

```shell
python3 process.py \
  --option=all \
  --table_prefix=S0804 \
  --has_percent=True \
  --debug=False \
  --spec_path=S0804/S0804_spec.json \
  --input_path=S0804/S0804.zip \
  --output_dir=S0804/output
```

## Output Artifacts

Running the command above generates the following files in `S0804/output`:

- `S0804_cleaned.csv`: Cleaned observation data across all years and geographies.
- `S0804_output.mcf`: Generated StatisticalVariable schema nodes.
- `S0804_output.tmcf`: Template MCF mapping `S0804_cleaned.csv` columns to Data Commons schema.
- `S0804_summary.json`: Summary of observation counts and StatVars per year.
- `column_map.json`: Column mapping configuration per release year.

Years: 2010-2024  
Geo: Country, Census Division, State, County, County Subdivision, Census Tract, Block Group, Place, Metropolitan/Micropolitan Statistical Area (CBSA), Congressional District, School District, and ZCTA

