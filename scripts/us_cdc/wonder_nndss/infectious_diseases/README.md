## CDC WONDER: NNDS - Infectious diseases

There are three data sources for this import

### Nationally Notifiable Infectious Diseases and Conditions, United States: Annual Tables (2016 - 2019 | tables: 4-8)
This is downloaded using the `process_annual_tables_16-19.py --mode=<all|download|process> --input_path=<path> --output_path=<path> --table_ids=4,5,6,7,8 --years=2016,2017,2018,2019

### Nationally Notifiable Infectious Diseases and Conditions, United States: Annual Tables (2007 - 2015 | tables: 4-8)
The annual tables from 1993 to 2015 is available through [MMWR](https://www.cdc.gov/mmwr/mmwr_nd/index.html). In this website, the tables are embedded as HTML table content in the webpage.

> **NOTE:** While MMWR has data from 1993 to 2015, between 1993 to 2006 the datasets are images which cannot be scrapped to plain text and will need an OCR approach to extract data points. Hence, in this import we do not import the NNDSS Infectious diseases Annual table for the period between 1993 to 2006 in this import.

The webapages by year is tabulated below:

|Year|Webpage URL|
|----|-----------|
|2007|[https://www.cdc.gov/mmwr/preview/mmwrhtml/mm5653a1.htm](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm5653a1.htm)|
|2008|[https://www.cdc.gov/mmwr/preview/mmwrhtml/mm5754a1.htm](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm5754a1.htm)|
|2009|[https://www.cdc.gov/mmwr/preview/mmwrhtml/mm5853a1.htm](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm5853a1.htm)|
|2010|[https://www.cdc.gov/mmwr/preview/mmwrhtml/mm5953a1.htm](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm5953a1.htm)|
|2011|[https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6053a1.htm](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6053a1.htm)|
|2012|[https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6153a1.htm](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6153a1.htm)|
|2013|[https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6253a1.htm](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6253a1.htm)|
|2014|[https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6354a1.htm](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6354a1.htm)|
|2015|[https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6453a1.htm](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6453a1.htm)|

We will be using [`beautifulsoup`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to extract and process the datasets.

```
script for data download and processing
```

### Nationally Notifiable Infectious Diseases and Conditions, United States: Weekly Tables (1996 - 2022 | counts of medicalConditions)
The CDC releases [weekly cases](https://wonder.cdc.gov/nndss/nndss_weekly_tables_menu.asp) of selected infectious national notifiable diseases, from the National Notifiable Diseases Surveillance System (NNDSS). NNDSS data reported by the 50 states, New York City, the District of Columbia, and the U.S. territories are collated and published weekly as numbered tables and the data available in [CDC WONDER](https://wonder.cdc.gov/nndss/nndss_weekly_tables_menu.asp) starts from Week1 of 1996.

A similar dataset from 2014 onwards is available at [data.cdc.gov](https://data.cdc.gov/NNDSS/NNDSS-Weekly-Data/x9gk-5huc). This dataset is relatively clean and we extract the count of weekly cases but since we were able to get data from 2022 and not older, hence we use [CDC WONDER](https://wonder.cdc.gov/nndss/nndss_weekly_tables_menu.asp) as the preferred data source for this import.


```
scripts for data processing
```
The csv file is updated periodically every week and we pick up the entire csv file each time to ensure the corrections done after review (reflected in [Notice to Data Users](https://wonder.cdc.gov/nndss/NTR.html) page) is reflected in the import.
