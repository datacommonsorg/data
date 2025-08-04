1. # Import Overview

BJS is the primary statistical agency of the Department of Justice. It is one of the thirteen principal federal statistical agencies throughout the Executive Branch, agencies whose activities are predominantly focused on the collection, compilation, processing, or analysis of information for statistical purposes.

The mission of BJS is to collect, analyze, publish, and disseminate information on crime, criminal offenders, victims of crime, and the operation of justice systems at all levels of government. BJS also provides financial and technical support to state, local, and tribal governments to improve both their statistical capabilities and the quality and utility of their criminal history records. 

Jurisdiction by various factors and combinations of factors including: location, gender, race, correctional facility type, sentencing lengths
Custody by various factors and combinations of factors including: citizenship, correctional facility type, sentencing lengths
Admission and Discharge


## Source URL: "https://www.icpsr.umich.edu/web/NACJD/studies/38871"
## Import Type: Manual upload
## Source Data Availability: Yearly


2. # PreProcessing Steps:
No Preprocessing required.

3. # Autorefresh Type:
## Semi-Autorefresh: 
We can't put this import on a full auto-refresh schedule. The process requires a manual file download because the source uploads the data to a webpage without a static link, making it impossible to automate the download step.

First go to the source link where we can find the data: https://www.icpsr.umich.edu/web/pages/NACJD/
Search for 'National Prisoner Statistics, [United States]' in the page's search bar and press Enter
From the results, locate the file with the most recent year in its range (e.g., 1978-2022)
Click on the file it will redirect to the page like given below (file name should look like National Prisoner Statistics, [United States], 1978-2022 (ICPSR 38871) years and code may vary).
download the data from https://www.icpsr.umich.edu/web/NACJD/studies/38871
Click the download dropdown and select delimited. You'll be redirected to a login page; after successfully logging in, the data will download automatically.
upload the data file at location gs://unresolved_mcf/us_bjs/nps/semiautomation_files

4. # Script Execution Details
run the following command with the option -i followed by the name of the tsv data file that was downloaded and uploaded to unresolved bucket:
```
python3 import_data.py
```

#### Cleaned Data
- [national_prison_stats.csv](national_prison_stats.csv).

#### Template MCFs
- [national_prison_stats.tmcf](national_prison_stats.tmcf).

#### StatisticalVariable Instance MCF
- [nps_statvars.mcf](nps_statvars.mcf).

#### Scripts
- [import_data.py](import_data.py): BJS National Prison Statistics import script.




