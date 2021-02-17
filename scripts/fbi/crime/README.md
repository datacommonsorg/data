# Importing FBI Crime Data

This directory imports [FBI Crime Data](https://ucr.fbi.gov/crime-in-the-u.s) into Data Commons, more specifically, offenses known to law enforcement data.


The script generates:
- `crime.csv`, `state_crime.csv`, `FBI_crime.tmcf` & `FBI_state_crime.tmcf`

and it relies on these statistic variables:
- Count_CriminalActivities_AggravatedAssault
- Count_CriminalActivities_Arson
- Count_CriminalActivities_Burglary
- Count_CriminalActivities_ForcibleRape
- Count_CriminalActivities_LarcenyTheft
- Count_CriminalActivities_MotorVehicleTheft
- Count_CriminalActivities_MurderAndNonNegligentManslaughter
- Count_CriminalActivities_PropertyCrime
- Count_CriminalActivities_Robbery
- Count_CriminalActivities_CombinedCrime

Source data are copied into the repository under source_data. 

## Data Caveats:
- From 2013-2016, the FBI reported statistics for two different definitions of rape before fully transitioning to the current definition in 2017. We add a dummy column after it (so all years have two Rape columns).
- 2016 FBI reported data breakdown by city in [table6](https://ucr.fbi.gov/crime-in-the-u.s/2016/crime-in-the-u.s.-2016/tables/table-6/table-6.xls/view), instead of [table8](https://ucr.fbi.gov/crime-in-the-u.s/2019/crime-in-the-u.s.-2019/tables/table-8/table-8.xls/view) like other years. See `YEAR_TO_URL` for each year the FBI table we use.
- Right now, there is no duplicate city state. In case it happens in the future, you will see error message like "duplicate city state". Add logic in clean_crime_file() function to ignore the one with wrong population data. 
- Arson data is not reported at state level. Per FBI: "Although arson data are included in the trend and clearance tables, sufficient data are not available to estimate totals for this offense. Therefore, no arson data are published in this table."

## Generating Artifacts:

To generate `crime.csv` & `FBI_crime.tmcf`, run:

```bash
python3 preprocess.py
```

To generate `state_crime.csv` & `FBI_state_crime.tmcf`, run:

```bash
python3 preprocess_states_test.py
```

### Running Tests

```bash
python3 preprocess_test.py
python3 preprocess_states_test.py
python3 geocode_cities_test.py
```
