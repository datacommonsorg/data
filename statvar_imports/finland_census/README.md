# Finland Demographics Dataset
## Overview

This dataset contains demographic information from Finland sourced from Statistics Finland (Tilastokeskus). The data includes population statistics and census information from the official Finnish statistical database. 

## Data Source

**Source URL:** https://pxdata.stat.fi/PxWeb/pxweb/en/StatFin/StatFin__vaerak/statfin_vaerak_pxt_11ra.px/table/tableViewLayout1/

The data comes from Finland's official statistical authority and includes comprehensive demographic variables such as population counts, age distributions, and other census-related metrics.

## Processing Instructions

To process the Finland Census data and generate statistical variables, use the following command from the "data" directory:

```bash
python ./data/tools/statvar_importer/stat_var_processor.py --input_data="./test_data/Finland_Census_input.csv" --pv_map=Finland_Census_pvmap.csv --config_file=Finland_Census_metadata.csv --output_path=Finland_Census_output
