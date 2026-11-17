# Selected Characteristics of the Foreign-Born Population by Period of Entry into the United States: Europe (S0503)

This US Census ACS 5-Year Subject Table (`S0503`) provides counts and selected demographic, social, economic, and housing characteristics of the foreign-born population born in Europe (including breakdowns for Northern and Western Europe, Southern and Eastern Europe, and other European regions), sliced by citizenship, period of entry, age, sex, marital status, school enrollment, educational attainment, language spoken at home, employment status, occupation, industry, class of worker, earnings, household income, poverty status, and housing tenure.

- **Years Covered**: `2010–2024`
- **Source Table**: [US Census Bureau Table S0503](https://data.census.gov/table?q=S0503)

## Geographic Coverage

| Summary Level Code | Summary Level Name |
| :--- | :--- |
| `010` | US Country-level |
| `040` | State-level |
| `050` | County-level |
| `060` | State-County-County Subdivision |
| `140` | Census Tract |
| `160` | City / Places |
| `500` | Congressional District |
| `860` | ZCTA |
| `950, 960, 970` | School Districts |

## Download Step

Run `census_api_data_downloader.py` from `scripts/us_census/api_utils` to download the survey data:

```bash
cd scripts/us_census/api_utils

python3 census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S0503 \
  --start_year=2010 \
  --end_year=2024 \
  --all_summaries \
  --output_path=/tmp/census_download \
  --api_key=<YOUR_API_KEY>

cd ../../..
```

Copy the generated `.zip` file into `S0503/`:

```bash
cp /tmp/census_download/acs/acs5/subject/S0503/S0503.zip scripts/us_census/acs5yr/subject_tables/S0503/S0503.zip
```

## Process Step

Run the subject table processor from `scripts/us_census/acs5yr/subject_tables`:

```bash
cd scripts/us_census/acs5yr/subject_tables

python3 process.py \
  --option=all \
  --table_prefix=S0503 \
  --has_percent=True \
  --debug=False \
  --spec_path=S0503/S0503_spec.json \
  --input_path=S0503/S0503.zip \
  --output_dir=S0503/output

cd ../../../..
```

- `--option=all`: Runs both column map generation (`column_map.json`) and observation processing (`S0503_cleaned.csv`, `S0503_output.mcf`, `S0503_output.tmcf`, `S0503_summary.json`).
- `--has_percent=True`: Converts percentage values in the dataset to counts using the `denominators` mapping in `S0503_spec.json`.

## Validation & Testing Step

### 1. Run Unit Tests (`testdata/`)

Verify `S0503_spec.json` and the generated test artifacts in `S0503/testdata/`:

```bash
cd scripts/us_census/acs5yr
python3 -m unittest subject_tables/subject_table_test.py
cd ../../..
```

### 2. Run Data Commons Import Tool Linter

Validate the generated `.tmcf`, `.mcf`, and `.csv` files using the Data Commons import tool:

```bash
cd scripts/us_census/acs5yr/subject_tables/S0503

java -jar ~/Downloads/import_tools_import-tool.jar genmcf \
  -e=false \
  output/S0503_cleaned.csv \
  output/S0503_output.tmcf \
  output/S0503_output.mcf \
  -o=output/dc_generated

cd ../../../../..
```
