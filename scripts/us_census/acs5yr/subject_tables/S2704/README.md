# Public Health Insurance Coverage by Type and Selected Characteristics (S2704)

This US Census ACS 5-Year Subject Table (`S2704`) provides civilian noninstitutionalized population counts on public health insurance coverage by type (Medicare, Medicaid/means-tested public coverage, and VA health care) sliced by selected demographic and socioeconomic characteristics such as age, poverty status (ratio to poverty threshold), and work experience.

- **Years Covered**: `2015–2024`
- **Source Table**: [US Census Bureau Table S2704](https://data.census.gov/table?q=S2704:%20Public%20Health%20Insurance%20Coverage%20by%20Type%20and%20Selected%20Characteristics&g=010XX00US,$0400000,$0500000,$0600000,$1400000,$1600000,$3100000,$31000M1,$31000M2,$5000000,$8600000,$9500000,$9600000,$9700000)

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
  --table_id=S2704 \
  --start_year=2015 \
  --end_year=2024 \
  --all_summaries \
  --output_path=/tmp/census_download \
  --api_key=<YOUR_API_KEY>

cd ../../..
```

Copy the generated `.zip` file into `S2704/` (or `S2704/input_data/`):

```bash
mkdir -p scripts/us_census/acs5yr/subject_tables/S2704/input_data
cp /tmp/census_download/acs/acs5/subject/S2704/S2704.zip scripts/us_census/acs5yr/subject_tables/S2704/input_data/S2704.zip
```

## Process Step

Run the subject table processor from `scripts/us_census/acs5yr/subject_tables`:

```bash
cd scripts/us_census/acs5yr/subject_tables

python3 process.py \
  --option=all \
  --table_prefix=S2704 \
  --has_percent=False \
  --debug=False \
  --spec_path=S2704/S2704_spec.json \
  --input_path=S2704/input_data/S2704.zip \
  --output_dir=S2704

cd ../../..
```

- `--option=all`: Runs both column map generation (`column_map.json`) and observation processing (`S2704_cleaned.csv`, `S2704_output.mcf`, `S2704_output.tmcf`, `S2704_summary.json`). You can also run `--option=colmap` followed by `--option=process` sequentially.
- `--has_percent=False`: S2704 directly provides population counts, so percentage-to-count conversion is not required.

## Validation & Testing Step

### 1. Run Unit Tests (`testdata/`)

Verify `S2704_spec.json` and the generated test artifacts in `S2704/testdata/`:

```bash
cd scripts/us_census/acs5yr
python3 -m unittest subject_tables/subject_table_test.py
cd ../../..
```

### 2. Run Data Commons Import Tool Linter

Validate the generated `.tmcf` and `.csv` files using the Data Commons import tool:

```bash
cd scripts/us_census/acs5yr/subject_tables/S2704

java -jar ~/Downloads/import_tools_import-tool.jar lint \
  S2704_output.tmcf \
  S2704_cleaned.csv
```