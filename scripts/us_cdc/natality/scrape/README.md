# Download process for CDC Wonder Natality

Source url: `https://wonder.cdc.gov/natality-expanded-current.html`

## Requirements
Run the following commands to install the required packages

- `pip3 install -r requirements.txt`

- `pip3 install -r scripts/us_cdc/scrape/requirements.txt` (contains selenium)

## Configuration steps
There are certain options to be selected to download the required data

### Web page
-  Inspect the page -> Elements

### natality_config.json
- `group_by`: Select the `Geo level` and `year` for every file.
- `measure`: Select the required datasets for example: `Births`, `Birth Rate`, `Fertility Rate` etc. Select the respective `ids` of the datasets.
- `select`: Start selecting additional properties - age, race, education, marital status, ethnicity, nativity.
- If the property is a radio button, give "`radio`" under that id. Unwanted values in a property like "`Exc, NR`" can be excluded - "`exclude_options`"
- While selecting the properties, "`name`" can be given under their 
respective `ids` so that it appears in the file name.

## Executing the download script
- For County data.
```shell
 python3 scripts/us_cdc/scrape/scrape_cdc_wonder.py --alsologtostderr --download_path=scripts/us_cdc/natality/county/raw_data/   --website=https://wonder.cdc.gov/natality-expanded-current.html   --config_path=scripts/us_cdc/scrape/natality_config.json --parallel_download=0 --headless   --calculate_combinations --show_totals --include_zeroes
```

- For State data.
```shell
 python3 scripts/us_cdc/scrape/scrape_cdc_wonder.py --alsologtostderr --download_path=scripts/us_cdc/natality/state/raw_data/   --website=https://wonder.cdc.gov/natality-expanded-current.html   --config_path=scripts/us_cdc/scrape/natality_config.json --parallel_download=0 --headless   --calculate_combinations --show_totals --include_zeroes
```