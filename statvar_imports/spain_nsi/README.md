### This import process handles data from Spain platform.

- Description: population, health, education, and labor statistics at the province and municipality levels.

- Source URL: https://www.ine.es/en/index.htm

- Type of place: Province and Municipality

- Place Resolution: Ran place_resolver.py script and manual verification

- Import Type: Fully Autorefresh

- Data Availability: 1975 to 2024

- Release Frequency: P1Y, which means every year.

### Preprocessing and Data Acquisition

To get the raw input files, you need to update the import_config.json file with the required direct source URLs, and then run the following script:

```bash

    python3 download_script.py
```
This script downloads the source data into a main input_files directory. 


### Data Processing

You can process the data in below way:

* Automated Processing

The run.sh script automates the processing for all downloaded files. Simply run the following command:

```bash
sh run.sh
```

### Automation

This import pipeline is configured to run automatically on a monthly schedule.

- Cron Expression: 30 09 27 * *

Schedule: The script runs at 9:30 AM on the 27th day of every month.