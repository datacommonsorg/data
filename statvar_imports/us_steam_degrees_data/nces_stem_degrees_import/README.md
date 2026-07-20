# NCES STEM Degrees Dataset

## Overview

This dataset contains information on science, technology, engineering, and mathematics (STEM) degrees and certificates conferred by postsecondary institutions in the United States, sourced from the National Center for Education Statistics (NCES) Digest of Education Statistics (Table 318.45). The dataset provides national-level coverage over an 11-year span from 2013 to 2023 (corresponding to academic years 2012–13 through 2022–23). It includes detailed breakdowns of STEM degrees conferred across various educational attainment levels (certificates below baccalaureate, associate's degrees, bachelor's degrees, master's degrees, and doctor's degrees) categorized by demographic variables such as race, ethnicity, sex, and citizenship/residency status. Data is reported in multiple units for versatile analysis, including absolute counts of degree recipients and percentage distributions.

**type of place:** Country  
**years:** 2013 to 2023  

## Data Source

**Source URL:**  
https://nces.ed.gov/programs/digest/d24/tables/dt24_318.45.asp

## License

**License Type:**  
Public Domain (U.S. Government Work)

**License URL:**  
https://nces.ed.gov/help/webpolicies.asp

**License Description:**  
Information produced by the National Center for Education Statistics (NCES) and the U.S. Department of Education is in the public domain and may be reproduced or copied without explicit permission.

## Refresh Type
Automatic Refresh

The refresh is automated via cron schedule defined in `manifest.json` (`0 05 4,18 * *`), which periodically executes the download script and `stat_var_processor.py`.

## Processing the Data

### Download Script
To download the source data table:
```bash
python3 ../../../util/download_util_script.py --download_url="https://nces.ed.gov/programs/digest/d24/tables/xls/tabn318.45.xlsx" --output_folder="source_files" --unzip=False
```

### Run StatVar Processor
To process the downloaded data into Data Commons CSV and TMCF format:
```bash
python3 stat_var_processor.py \
  --input_data='source_files/*.xlsx' \
  --pv_map='pvmap.csv' \
  --config='metadata.csv' \
  --output_path='output/nces_steam_degree' \
  --statvar_dcid_remap_csv='dcid_remap.csv'
```
