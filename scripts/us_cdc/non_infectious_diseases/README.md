## CDC/WONDER/NORS: Non-infectious disease outbreaks

This directory contains the instructions to download data, process the
downloaded data to generate the clean csv and statvar mcf for Non-infectious
disease outbreaks across the different states of the US.

### Data Download
To download the data,
1. Visit the National Outbreak Reporting System, [NORS Dashboard](https://wwwn.cdc.gov/norsdashboard/)
2. Check if all the checkboxes are selected under *What types of outbreaks would you like to include?*
3. Scroll down towards the footer of the page to find a link to download data in
   excel format. Select the link called *Download all NORS Dashboard data (Excel)*. This will download all the required dataset.

### Here's an alternative way to download the NORS data:
Instead of navigating the website, you can try using this direct link to export the data in Excel format: [NORS Dashboard](https://data.cdc.gov/Foodborne-Waterborne-and-Related-Diseases/NORS/5xkq-dg7x/about_data). Clicking on this link should directly initiate the download of the complete dataset in an Excel file.


### Notes
There are some notes and caveats with this dataset.
1. NORS dashboard data is updated **annually**.
2. NORS dashboard data can differ between two years since past data can be fixed by the reporting states any time.
3. This is a partial import the NORS Dashboard i.e. the statistical variables are aggregated on the Primary Mode, Etiology and Etiology Status columns.
	> The other columns add more classification of the etiology outbreak which can be added to the script at a later time -- since it requires new schema
4. This import also imports statistics only for a single etiology -- since it is unclear how to interpret the statistics with multiple Etiologies
5. The columns `Info on Hospitalisations` and `Info on Deaths` are not used in this import.

### Automation Refresh
The process.py has a parameter 'mode' with values 'download' and 'process'

when the file 'process.py' is ran with the flag --mode=download, it will only download the files and place it in the 'input_files' directory.
i.e. python3 process.py mode=download

when the file 'process.py' is ran with the flag --mode=process, it will process the downloaded files and place it in the 'output' directory.
i.e. python3 process.py mode=process

when the file 'process .py' is ran without any flag, it will download and process the files and keep it in the respective directories as mentioned above.
i.e. python3 process.py

