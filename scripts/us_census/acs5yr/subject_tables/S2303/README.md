# US Census ACS5YR S2303 Subject Table Import

This import gives the count of people in the age range 16-64 years who have worked 1 or more weeks in the past 12 months. It provides a further breakdown of the data on the gender, number of working weeks and the amount of hours worked per week.

- **Years**: 2010-2024
- **Geo**: Country, State, County, County Subdivision, Census Tract, Place/City, Congressional District, ZCTA, School District, CBSA, Census Division

## Important Notes
1. Median age of workers is not available from 2010-2014.
2. Data for "Workers 16 to 64 years who worked full-time, year-round" is not available from 2010-2014.
3. The breakdown of usual hours worked from 2010 - 2014 is a subset of the ones available from 2015 - 2024.
4. The values are published as counts from 2015 - 2024 and as percentages from 2010 - 2014.

## Download Step

Run `census_api_data_downloader.py` from `scripts/us_census/api_utils` for each 3-year range using `--start_year` / `--end_year` and copy each generated `S2303.zip` into `input_files/`:

```bash
cd scripts/us_census/api_utils
mkdir -p ../acs5yr/subject_tables/S2303/input_files

for range in 2010_2012 2013_2015 2016_2018 2019_2021 2022_2024; do
  start_yr=${range%_*}
  end_yr=${range#*_}
  python3 census_api_data_downloader.py \
    --dataset=acs/acs5/subject \
    --table_id=S2303 \
    --start_year=$start_yr \
    --end_year=$end_yr \
    --summary_levels=010,030,040,050,060,140,160,310,500,860,950,960,970 \
    --output_path=~/us_census \
    --api_key=<YOUR_API_KEY>
  cp ~/us_census/acs/acs5/subject/S2303/S2303.zip \
     ../acs5yr/subject_tables/S2303/input_files/s2303_${range}.zip
done
```

## Process Step

Run `process.py` from `scripts/us_census/acs5yr/subject_tables/S2303`:

```bash
cd ../acs5yr/subject_tables/S2303

for b in s2303_2010_2012 s2303_2013_2015 s2303_2016_2018 s2303_2019_2021 s2303_2022_2024; do
  python3 process.py \
    --option=all \
    --table_prefix=$b \
    --has_percent=True \
    --debug=False \
    --spec_path=./S2303_spec.json \
    --input_path=input_files/${b}.zip \
    --output_dir=./
  mv column_map.json ${b}_column_map.json
  mv ${b}_output.tmcf s2303_output.tmcf
done
```

- `--option=all`: Runs both column map generation (`column_map.json`) and observation processing (`<prefix>_cleaned.csv`, `<prefix>_output.mcf`, `<prefix>_output.tmcf`, `<prefix>_summary.json`).
- `--has_percent=True`: Converts percentage estimates (`2010`–`2014`) into counts using the mapped denominator keys in `S2303_spec.json` (`S2303SubjectTableDataLoader` in `process.py` restricts conversion to `percent_years = ['2014', '2013', '2012', '2011', '2010']`).
- Only a single shared `s2303_output.tmcf` and `s2303_2013_2015_output.mcf` (which spans both the `2010`–`2014` and `2015`–`2024` column layouts and contains all 210 unique StatVar nodes) need to be retained in the final import folder alongside the 5 `*_cleaned.csv` batch files.

## Batch Splitting & Runtime Optimization

Processing all 15 years (`2010`–`2024`, ~80 GiB intermediate CSV / ~459M rows) as a single `.zip` requires ~155 GiB RAM during the final `pd.read_csv()` cleanup step and spills to swap. Splitting into **5 3-year `.zip` batches** keeps each run in RAM with zero swap thrashing:

| Batch / `--table_prefix` | CSV Files Inside `.zip` | Output Files Generated |
| :--- | :--- | :--- |
| `s2303_2010_2012` | `ACSST5Y2010*.csv`, `ACSST5Y2011*.csv`, `ACSST5Y2012*.csv` | `s2303_2010_2012_{cleaned.csv, output.mcf, summary.json}` |
| `s2303_2013_2015` | `ACSST5Y2013*.csv`, `ACSST5Y2014*.csv`, `ACSST5Y2015*.csv` | `s2303_2013_2015_{cleaned.csv, output.mcf, summary.json}` |
| `s2303_2016_2018` | `ACSST5Y2016*.csv`, `ACSST5Y2017*.csv`, `ACSST5Y2018*.csv` | `s2303_2016_2018_{cleaned.csv, output.mcf, summary.json}` |
| `s2303_2019_2021` | `ACSST5Y2019*.csv`, `ACSST5Y2020*.csv`, `ACSST5Y2021*.csv` | `s2303_2019_2021_{cleaned.csv, output.mcf, summary.json}` |
| `s2303_2022_2024` | `ACSST5Y2022*.csv`, `ACSST5Y2023*.csv`, `ACSST5Y2024*.csv` | `s2303_2022_2024_{cleaned.csv, output.mcf, summary.json}` |

### Runtime Comparison
| Method | Total Wall-Clock Time | Time Saved | Notes |
| :--- | :---: | :---: | :--- |
| **1 Single `.zip` (`2010`–`2024`)** | ~110 – 120 mins | — | Spills to swap during final `pd.read_csv()` rewrite. |
| **5 Split `.zip`s (Sequential)** | ~45 – 55 mins | ~60 – 65 mins (~2x faster) | Each batch (~16 GiB CSV) fits in RAM with zero swap. |
| **5 Split `.zip`s (Parallel, 2–3 jobs)** | ~18 – 22 mins | ~90 – 100 mins (~5x faster) | Utilizes multiple cores while staying under system RAM. |



