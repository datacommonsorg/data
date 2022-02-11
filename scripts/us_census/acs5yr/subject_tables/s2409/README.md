# Artefacts for US census ACS5YR S2409 Subject Table import #

This import includes the class of worker characteristics for full-time, year-round, 16 year and over civilian employed population characterized by the gender.
For years 2010-2014, Median Earnings (in Dollars Inflation Adjusted) are also available.

Years: 2010-2019
Geo : Country, State, County and Place

Important Notes :
1. Counts of Males and Females were available as percentages for years 2010-2014. Same are converted to absolute values using 'denominators' section in json spec.
2. Local import scripts s2409/process.py and s2409/data_loader.py are created to process denominators section of json spec only for years 2010-2014.
3. Margin of Error for Median Earnings is not processed in this import.
