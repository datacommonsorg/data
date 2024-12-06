# CDCWonder NNDSS InfectiousWeekly Import

## About the Dataset
Notifiable Infectious Diseases Data: Weekly tables from CDC WONDER which has the incident counts of different infectious diseases per week that are reported by the 50 states, New York City, the District of Columbia, and the U.S. territories

### Download URL

Source URL {https://wonder.cdc.gov/nndss/nndss_weekly_tables_menu.asp}.

To download the latest versions of ALL datasets available, run the following command. Files will be downloaded and extracted to a nndss_weekly_data folder.

### License

This dataset is available for public use, license is available at https://www.cdc.gov/other/agencymaterials.html


### Downloading and Processing Data


    If you want to perform "only download", run the below command:

```bash
python3 process_weekly_data.py --mode=download
```
If you want to perform "only process", run the below command:

   Running this command generates input_fles and csv, mcf, tmcf files

```bash
    python3 process_weekly_data.py --mode=process
```

 To Download and process the data together, run the below command
 ```bash
    python3 process_weekly_data.py
```
To download and process for a specific year range, refer to the following command with flags
```
    python3 process_weekly_data.py --mode=download  --start_year=2008 --end_year=2009
```