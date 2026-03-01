# National Family Health Survey - India

## About
The National Family Health Survey (NFHS) is a large-scale, multi-round survey conducted in a representative sample of households throughout India. National Family Health Survey (NFH) provides information on fertility, infant and child mortality, the practice of family planning, maternal and child health, reproductive health, nutrition, anaemia, utilization and quality of health and family planning services in a state as well as pan India level. The specific goal of the National Family Health Survey (NFHS) are a) to provide essential data on health and family welfare for policy and programme purposes, and b) to provide information on important emerging health and family welfare issues. Besides providing evidence for the effectiveness of ongoing programs, the National Family Health Survey (NFHS-5) data helps identify the need for new programmes with an area-specific focus and identifying groups that are most in need of essential services.

## NDAP Data Portal
There are 3 datasets available for National Family Health Survey:-
1) [National Family Health Survey - 4 & 5: State](https://ndap.niti.gov.in/dataset/6821)
2) [National Family Health Survey - 4 : District](https://ndap.niti.gov.in/dataset/7034)
3) [National Family Health Survey - 5 : District](https://ndap.niti.gov.in/dataset/6822)

## Dataset in this directory
This import directory has National Family Health Survey data for all Indian states and districts for year 2015-2016 and 2019-2020. The data can be found in [states/data/](./states/data/) and [districts/data/](./districts/data/) directories.

The processed CSVs, MCFs and TMCFs can be found in the following paths:
- Processed CSV => States: [states/NFHS_Health.csv](./states/NFHS_Health.csv); Districts: [districts/NFHS_Health.csv](./districts/NFHS_Health.csv)
- Processed MCF => States: [states/NFHS_Health.csv](./states/NFHS_Health.mcf); Districts: [districts/NFHS_Health.csv](./districts/NFHS_Health.mcf)
- Processed TMCF => States: [states/NFHS_Health.csv](./states/NFHS_Health.tmcf); Districts: [districts/NFHS_Health.csv](./districts/NFHS_Health.tmcf)

## Running the import code
To generate CSV, MCF and TMCF for the state level data, run the following command from the current directory:

```python -m states.preprocess```

To generate CSV, MCF and TMCF for the district level data, run the following command:

```python -m districts.preprocess```