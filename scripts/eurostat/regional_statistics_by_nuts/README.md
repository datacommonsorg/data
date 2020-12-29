# Importing EuroStat Regional Statistics Into Data Commons

Authors: Data Commons 2020 Summer Interns (eftekhari-mhs, jinpz, qlj-lijuan, fpernice-google)

The imports in this directory are widely used across Data Commons surfaces. Eurostat is the
main source of European sub-country level statistics.

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [About the Imports](#about-the-imports)

## About the Dataset

EuroStat Regional Statistics reports demographic data these geo levels:

- Countries
- NUTS1
- NUTS2
- NUTS3 (not all vars)

The provided NUTS codes are resolved by DCID, based on the fact that the DCIDs
of NUTS geos are `nuts/` + the NUTS ID.

NUTS (Nomenclature of Territorial Units for Statistics) is a hierarchical classification for dividing regions of Europe.

Useful links:

- [NUTS Background](https://ec.europa.eu/eurostat/web/nuts/background)

- [NUTS Map](https://ec.europa.eu/eurostat/web/nuts/nuts-maps)

- [Dataset Metadata](https://ec.europa.eu/eurostat/data/metadata).

### Download URL

[TSV] file is available for download from <https://ec.europa.eu/eurostat/data/database> under 'Data navigation tree > Database by themes > General and regional statistics > Regional statistics by NUTS classification (reg)'.

### License

Eurostat has a policy of encouraging free re-use of its data, both for non-commercial and commercial purposes. See [the license](https://ec.europa.eu/eurostat/about/policies/copyright) for more info.

## Imported datasets:

- Birth, deaths, and migrations (by NUTS3)
- Education attainment by gender (by NUTS2)
- Education enrollment by gender (by NUTS2)
- Employed per sector (by NUTS3)
- Fertility rate, median and mean age of mothers at childbirth (by NUTS3)
- Various measures of GDP (by NUTS3)
- Life expectancy by age and gender (by NUTS2)
- Population density (by NUTS3)

See the READMEs in the individual subdirectories for more information about
each import's variables.

## Unfinished work:

- Moratality rate by cause (NUTS2): There is some in-progress work in the now-closed
  [PR 146](https://github.com/datacommonsorg/data/pull/146). Part of that PR
  is checked in ("Birth, deaths, and migrations (by NUTS3)" above).
  If this work is picked up again, there may need to be careful work to make
  sure the enums reuse existing causes of death enums if applicable.
