# Group Quarters Population
This census table details the counts of people in various types of group quarters defined in the [manual](https://www2.census.gov/programs-surveys/acs/tech_docs/group_definitions/2019GQ_Definitions.pdf) sliced by various properties like age, sex, employment, occupation, citizenship, ... The table contains country, state level data. The group quarters can be Institutinalized or Noninstitutionalized, and can be subdived into their specific types like Adult Correctional Facility, College/University Housing. This table provides data for the major categories only. Tables S2603, S2602, S2602PR provides data for the specific types of group quarters.

## Download Step

Run `census_api_data_downloader.py` from `scripts/us_census/api_utils` to download the survey data:

```bash
cd scripts/us_census/api_utils

python3 census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S2601A \
  --start_year=2010 \
  --end_year=2024 \
  --all_summaries \
  --output_path=/tmp/census_download \
  --api_key=<YOUR_API_KEY>
```

Copy only the generated `.zip` file into `input_data/`:

```bash
mkdir -p scripts/us_census/acs5yr/subject_tables/S2601A/input_data
cp /tmp/census_download/S2601A.zip scripts/us_census/acs5yr/subject_tables/S2601A/input_data/S2601A.zip
```

## Process Step

Run the subject table processor from `scripts/us_census/acs5yr/subject_tables`:

```bash
cd scripts/us_census/acs5yr/subject_tables

python3 process.py \
  --option=all \
  --table_prefix=S2601A \
  --has_percent=True \
  --debug=False \
  --spec_path=S2601A/S2601A_spec.json \
  --input_path=S2601A/input_data/S2601A.zip \
  --output_dir=S2601A
```

- `--option=all`: Runs both column map generation (`column_map.json`) and observation processing (`S2601A_cleaned.csv`, `S2601A_output.mcf`, `S2601A_output.tmcf`, `S2601A_summary.json`).
- `--has_percent=True`: Automatically converts percentage estimates into counts using the mapped denominator keys.

## Changes Done for 2020–2024 Refresh

To refresh and support data for vintages 2020 through 2024 in `S2601A_spec.json`:

1. **`ignoreTokens` (Inflation year tokens)**:
   Added the inflation-adjusted income tokens for each survey year from 2020 to 2024:
   ```json
   "INCOME AND BENEFITS IN THE PAST 12 MONTHS (IN 2020 INFLATION-ADJUSTED DOLLARS)",
   "INCOME AND BENEFITS IN THE PAST 12 MONTHS (IN 2021 INFLATION-ADJUSTED DOLLARS)",
   "INCOME AND BENEFITS IN THE PAST 12 MONTHS (IN 2022 INFLATION-ADJUSTED DOLLARS)",
   "INCOME AND BENEFITS IN THE PAST 12 MONTHS (IN 2023 INFLATION-ADJUSTED DOLLARS)",
   "INCOME AND BENEFITS IN THE PAST 12 MONTHS (IN 2024 INFLATION-ADJUSTED DOLLARS)"
   ```

2. **`ignoreColumns` (Median & mean income columns)**:
   Added 16 columns per year for 2020–2024 (80 columns total) covering median and mean earnings across the 4 population groups and both sexes (`Total population`, `Total group quarters population`, `Institutionalized group quarters population`, `Noninstitutionalized group quarters population` $\times$ `Median / Mean` $\times$ `Male / Female`).

3. **`denominators` (Poverty rate denominators)**:
   Added 4 denominator keys per year for 2020–2024 (20 keys total) across the 4 population groups:
   `Estimate!!<Population Group>!!INCOME AND BENEFITS IN THE PAST 12 MONTHS (IN <YYYY> INFLATION-ADJUSTED DOLLARS)!!Individuals`
   Each key maps to the 8 poverty rate targets (Estimate & MOE pairs for `All people`, `18 years and over`, `18 to 64 years`, and `65 years and over`).
