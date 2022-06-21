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
   python3 process_nors.py
   --input_file=./data/NationalOutbreakPublicDataTool.xlsx
   --output_path=./data/output
   ```

### Notes
There are some notes and caveats with this dataset.
1. NORS dashboard data is updated **annually**.
2. NORS dashboard data can differ between two years since past data can be fixed
   by the reporting states any time.

