# Importing CDC Wonder Natality Data

This directory imports [CDC Wonder Natality data](https://wonder.cdc.gov/natality.html) into Data Commons. It includes data at US, state and county level.

## Cleaning source data
To clean the source data, run:

```bash
python clean_cdc_data.py --input_path=source_data/<year_bracket> --output_path=<output_path>
```

## Generating Artifacts at a State or County level:
The artifacts can be generated from the cleaned data.
To generate `cleaned.csv`, `output.mcf` run:

```bash
python preprocess.py --input_path=<path to cleaned data> --config_path=<path to config> --output_path=<path to write cleaned csv and mcf>
```

## Aggregating at a Country level
At a country level, aggregation is performed by summing over the state level `cleaned.csv`.
To generate `cleaned.csv` run:

```bash
python aggregate.py --input_path=<path to state level csv> --output_path=<path to write cleaned csv>
```

## Data Caveats:
- There are four brackets (year ranges) in which data is provided. 95-02, 03-06, 07-20, 16-20(extended data). The availability of statistics varies across these brackets.
- Race statistics for 03-06 and 07-20 is available for only 4 bridged races whereas 95-02 and 16-20 brackets provide data for 8 and 15 races respectively.
- Data from 2007-2015 is picked up from 07-20 and 2016-2020 data is picked from the 16-20 bracket.
- County level data is restricted to counties with a population of 100,000 or higher
- Some measures are available only from 2016-2020
- Suppressed data points are skipped in this import
- At the country level, only count statvars are aggregated