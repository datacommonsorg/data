# Importing FBI Crime Data

This directory imports [FBI Crime Data](https://ucr.fbi.gov/crime-in-the-u.s) into Data Commons, more specifically, offenses known to law enforcement data.



The script generates:
- TBD

and it relies on these statistic variables:
- TBD


## Data Caveats:
- From 2013-2016, the FBI reported statistics for two different definitions of rape before fully transitioning to the current definition in 2017. We add a dummy column after it (so all years have two Rape columns).
- 2016 FBI reported data breakdown by city in [table6](https://ucr.fbi.gov/crime-in-the-u.s/2016/crime-in-the-u.s.-2016/tables/table-6/table-6.xls/view), instead of [table8](https://ucr.fbi.gov/crime-in-the-u.s/2019/crime-in-the-u.s.-2019/tables/table-8/table-8.xls/view) like other years. See `YEAR_TO_URL` for each year the FBI table we use.
- For duplicate city data, we remove the one with wrong population data (Google search city population). 

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