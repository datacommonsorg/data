# Sri Lanka Census Dataset

## Overview

This dataset contains demographic, agriculture, and education statistical indicators for Sri Lanka sourced from the Humanitarian Data Exchange (HDX):
1. **Subnational Population Statistics (`cod-ps-lka`)**: Population counts by age and gender across country (`LKA`), 9 provinces (`LK1`–`LK9`), and 25 districts (`LK11`–`LK92`) for 2022 and 2023, sourced from the Department of Census and Statistics of Sri Lanka / UNFPA.
2. **Agriculture and Rural Development (`world-bank-agriculture-and-rural-development-indicators-for-sri-lanka`)**: National agricultural land, yield, fertilizer consumption, and rural population indicators from 1960 to present.
3. **Education (`world-bank-education-indicators-for-sri-lanka`)**: National education enrollment, attainment, completion, literacy, expenditure, and Barro-Lee demographic indicators from 1960 to present.

- **Type of place**: Country (`country/LKA`), AdministrativeArea1 (Provinces), AdministrativeArea2 (Districts)
- **Years**: 1960 to present

## Data Sources
- **Subnational Population**: https://data.humdata.org/dataset/cod-ps-lka
- **Agriculture & Rural Development**: https://data.humdata.org/dataset/world-bank-agriculture-and-rural-development-indicators-for-sri-lanka
- **Education**: https://data.humdata.org/dataset/world-bank-education-indicators-for-sri-lanka

## Refresh Type
Automatic Refresh

## Download & Processing Details

1. **Download (`download.py`)**:
   - Queries the HDX CKAN API (`https://data.humdata.org/api/3/action/package_show`) for the three datasets (`cod-ps-lka`, `world-bank-agriculture-and-rural-development-indicators-for-sri-lanka`, and `world-bank-education-indicators-for-sri-lanka`).
   - Downloads `lka_admpop_2022_v2.xlsx` (extracting sheets `lka_admpop_adm0_2022`, `lka_admpop_adm1_2022`, and `lka_admpop_adm2_2022`) and the 2023 CSV tables (`lka_admpop_adm0_2023.csv`, `lka_admpop_adm1_2023.csv`, `lka_admpop_adm2_2023.csv`), standardizing place codes (`LKA`, `LK1`–`LK9`, `LK11`–`LK92`) into `input_files/srilanka_population.csv`.
   - Downloads `agriculture-and-rural-development_lka.csv` and `education_lka.csv`, strips HXL tag rows (`#...`), filters to mapped indicator codes defined in `srilanka_census_pvmap.csv`, and writes `input_files/srilanka_agriculture.csv` and `input_files/srilanka_education.csv`.

2. **Processing (`stat_var_processor.py`)**:
   ```bash
   python3 download.py --output_dir=input_files --pv_map=srilanka_census_pvmap.csv
   python3 ../../tools/statvar_importer/stat_var_processor.py \
     --input_data=input_files/*.csv \
     --pv_map=srilanka_census_pvmap.csv \
     --config_file=srilanka_census_metadata.csv \
     --output_path=output_files/srilanka_census_output \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_counters=counters/srilanka_census_counters.csv
   ```

## Key Files
- `download.py`: Downloads and preprocesses raw HDX files into `input_files/`.
- `download_test.py`: Unit tests for `download.py`.
- `srilanka_census_pvmap.csv`: Property-Value mappings for places, population columns, and WDI indicator codes.
- `srilanka_census_metadata.csv`: Configuration parameters for `stat_var_processor.py`.
- `srilanka_places_resolved.csv`: Place resolution mappings from PCODE/ISO3 to Data Commons DCIDs.
- `manifest.json`: Import automation manifest configuration.
- `validation_config.json`: Validation rules for the automated pipeline.

## Validation
```bash
java -jar datacommons-import-tool.jar genmcf \
  output_files/srilanka_census_output.tmcf \
  output_files/srilanka_census_output.csv
```
