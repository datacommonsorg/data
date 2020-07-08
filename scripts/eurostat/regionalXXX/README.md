# Importing EuroStat XXX Into Data Commons
Author: <author>

## Table of Contents

1. [About the Dataset](#about-the-dataset)

## About the Dataset

### Download URL

[TSV] file is available for download from <url>.

### Overview
The metadata for Population change - Demographic balance and crude rates at regional level (NUTS 3) is available online at [here](https://ec.europa.eu/eurostat/cache/metadata/en/demo_r_gind3_esms.htm)

NUTS (Nomenclature of Territorial Units for Statistics) is a hierarchical classification for dividing regions of Europe. NUTSi, starting at NUTS1, is the ith classification which is more detailed than the NUTS(i-1). We’re importing population density for regions in the NUTS3 classification.

The format of each region’s NUTS3 GEO is two letters continued by 0,1,2, or 3 digits. 
Example: BE, BE1, BE21, BE254 


NUTS2 and NUTS3 can be accessed by dcid: nuts/xxx, typeOf:EurostatNUTS2, typeOf:EurostatNUTS3 (respectively) 


### Notes and Caveats

#### available flags: Available flags:
- b	break in time series	
- c	confidential	
- d	definition differs, see metadata
- e	estimated	
- f	forecast	
- n	not significant
- p	provisional	
- r	revised	
- s	Eurostat estimate
- u	low reliability	
- z	not applicable 
- Special value: ":" not available

- Downloading csv from the browser includes part of the data. To get full access to all data points one must download the tsv file instead.


### License

Eurostat has a policy of encouraging free re-use of its data, both for non-commercial and commercial purposes. 

The license is available online at [here](https://ec.europa.eu/eurostat/about/policies/copyright).

### Dataset Documentation and Relevant Links 

- Documentation: <documentation_url>
