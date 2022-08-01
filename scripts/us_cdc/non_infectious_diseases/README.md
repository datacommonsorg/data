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

### Data processing
1. Copy the downloaded data to the `data` sub-directory
2. Run the following command to generate the clean csv, statvar mcf files,
   ```bash
   python3 process.py
   --input_file=./data/NationalOutbreakPublicDataTool.xlsx
   --output_path=./data/output
   ```

### Notes
There are some notes and caveats with this dataset.
1. NORS dashboard data is updated **annually**.
2. NORS dashboard data can differ between two years since past data can be fixed by the reporting states any time.
3. This is a partial import the NORS Dashboard i.e. the statistical variables are aggregated on the Primary Mode, Etiology and Etiology Status columns.
	> The other columns add more classification of the etiology outbreak which can be added to the script at a later time -- since it requires new schema
4. This import also imports statistics only for a single etiology -- since it is unclear how to interpret the statistics with multiple Etiologies
5. The columns `Info on Hospitalisations` and `Info on Deaths` are not used in this import.
