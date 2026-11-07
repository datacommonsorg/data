# US Census ACS5YR S0505 Subject Table Import

The subject table (`S0505`: *Selected Characteristics of the Foreign-Born Population by Region of Birth: Asia*) provides counts and selected demographic, social, economic, and housing characteristics for the foreign-born population in the United States whose place of birth (`placeOfBirth`) is:
- `asia` (`Foreign born; Born in Asia`)
- `EasternAsia` (`Foreign born; Born in Eastern Asia`)
- `SouthCentralAsia` (`Foreign born; Born in South Central Asia`)
- `SouthEasternAsia` (`Foreign born; Born in South Eastern Asia`)
- `WesternAsia` (`Foreign born; Born in Western Asia`)

Years: `2010–2024`

## Download Step

Run `census_api_data_downloader.py` from `scripts/us_census/api_utils` to download the survey data:

```bash
cd scripts/us_census/api_utils

python3 census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S0505 \
  --start_year=2010 \
  --end_year=2024 \
  --all_summaries \
  --output_path=<output_path> \
  --api_key=<YOUR_API_KEY>
```

Copy the generated `.zip` file into `S0505/`:

## Process Step

Run the subject table processor from `scripts/us_census/acs5yr/subject_tables`:

```bash
cd scripts/us_census/acs5yr/subject_tables

python3 process.py \
  --option=all \
  --table_prefix=S0505 \
  --has_percent=True \
  --debug=False \
  --spec_path=S0505/S0505_spec.json \
  --input_path=S0505/S0505.zip \
  --output_dir=S0505
```

- `--option=all`: Runs both column map generation (`column_map.json`) and observation processing (`S0505_cleaned.csv`, `S0505_output.mcf`, `S0505_output.tmcf`, `S0505_summary.json`).
- `--has_percent=True`: Converts percentage values in the dataset to counts using the `denominators` mapping in `S0505_spec.json`.

## Notes

1. Percentage values in the dataset are converted into corresponding counts using the `denominators` configuration in `S0505_spec.json`.
2. Monetary measurements (`Median earnings (dollars) for full-time, year-round workers`, `Mean earnings (dollars)`, `Median Household income (dollars)`, `Mean Social Security income (dollars)`, `Mean Supplemental Security Income (dollars)`, `Mean cash public assistance income (dollars)`, and `Mean retirement income (dollars)`) use `InflationAdjustedUSD_CurrentYear` as the unit.
3. `Total`, `Total MOE`, `PERCENT ALLOCATED`, and `PERCENT IMPUTED` columns are ignored in `S0505_spec.json` to prevent duplication.
4. `Count_Person_ForeignBorn_PlaceOfBirthAsia` and `MarginOfError_Count_Person_ForeignBorn_PlaceOfBirthAsia` are mapped to `Count_Person_PlaceOfBirthAsia` and `MarginOfError_Count_Person_PlaceOfBirthAsia` via `overwrite_dcids`.
