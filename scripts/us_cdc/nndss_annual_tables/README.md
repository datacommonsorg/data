# CDCWonder NNDSS InfectiousAnnual Import

## About the Dataset
Notifiable Infectious Diseases Data: Annual tables from CDC WONDER which has the incident counts of different infectious diseases per year and are aggregated based on demographic factors. The statistics are reported by the 50 states, New York City, the District of Columbia, and the U.S. territories

### Download URL

Source URL {https://wonder.cdc.gov/nndss/nndss_annual_tables_menu.asp}.


To download the latest versions of ALL datasets available, run the following command. Files will be downloaded and extracted to a nndss_Annual_data folder.

### License

This dataset is available for public use, license is available at https://www.cdc.gov/other/agencymaterials.html


### Downloading and Processing Data


   To download the data run the below command

```bash
	python3 download_annual_data.py
```
    To process the data, execute the below command:

   Running this command generates input_fles and csv, mcf, tmcf files

```bash
   A. python3 process_annual_demographics.py
   B. python3 process_annual_reporting.py
```


 
