# Importing FBI Crime Data

This directory imports [FBI Crime Data](https://ucr.fbi.gov/crime-in-the-u.s) into Data Commons, more specifically, offenses known to law enforcement data.



The script generates:
- TBD

and it relies on these statistic variables:
- TBD


## Data Caveats:
- From 2013-2016, the FBI reported statistics for two different definitions of rape before fully transitioning to the current definition in 2017. We add a dummy column after it (so all years have two Rape columns).
- 2016 FBI reported data is missing population. We blindly add one column with value 1. 
- Right now, there is no duplicate city state. In case it happens in the future, you will see error message like "duplicate city state". Add logic in clean_crime_file() function to ignore the one with wrong population data. 

## Generating Artifacts:

To generate `TBD`, run:

```bash
python3 preprocess.py
```

### Running Tests

```bash
python3 preprocess_test.py
python3 geocode_cities_test.py
```
