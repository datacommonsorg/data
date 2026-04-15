# AP, IB, and GT Enrollment Data Downloader

This script downloads and processes Advanced Placement (AP), International Baccalaureate (IB), and Gifted and Talented (GT) enrollment data from the Civil Rights Data Collection (CRDC).

## Scripts

There are two python scripts available:

*   `download_ap_ib_gt.py`: This is the main script that downloads and processes AP, IB, and GT enrollment data for multiple years.
*   `download_2015_16.py`: This script is specifically for downloading and processing the 2015-16 data, which has a different structure.

## Usage

To run the scripts, execute the following commands from the `data` directory:

### Main Script

```bash
python3 statvar_imports/us_urban_school/ap_ib_gt_enrollment/download_ap_ib_gt.py
```

You can also specify which data to download by using the following flags:

*   `--ap`: Download Advanced Placement data only.
*   `--ib`: Download International Baccalaureate data only.
*   `--gt`: Download Gifted and Talented data only.

For example, to download only the Advanced Placement data, run the following command:

```bash
python3 statvar_imports/us_urban_school/ap_ib_gt_enrollment/download_ap_ib_gt.py --ap
```

### 2015-16 Script

```bash
python3 statvar_imports/us_urban_school/ap_ib_gt_enrollment/download_2015_16.py
```

You can also specify which data to download by using the following flags:

*   `--ap`: Download Advanced Placement data for 2015-16 only.
*   `--ib`: Download International Baccalaureate data for 2015-16 only.
*   `--gt`: Download Gifted and Talented data for 2015-16 only.

For example, to download only the Advanced Placement data for 2015-16, run the following command:

```bash
python3 statvar_imports/us_urban_school/ap_ib_gt_enrollment/download_2015_16.py --ap
```

## Output Files

The scripts will download the data into the following directories:

*   `statvar_imports/us_urban_school/ap_ib_gt_enrollment/advanced_placements/input_files`
*   `statvar_imports/us_urban_school/ap_ib_gt_enrollment/international_baccalaureate/input_files`
*   `statvar_imports/us_urban_school/ap_ib_gt_enrollment/gifted_and_talented/input_files`

The output files will be in CSV or XLSX format.

## Data Source

The data is downloaded from the Civil Rights Data Collection (CRDC).

## Processing Steps

The scripts perform the following processing steps:

1.  Download the data from the CRDC website.

2.  Extract the relevant file from the downloaded zip file.

3.  Add a 'YEAR' and 'ncesid' column to the data.

4.  Save the processed data as a CSV or XLSX file.


## Processing the downloaded data

To process the data, you can run the `run_process.sh` script in each of the data directories. This script first downloads the relevant data and then processes it.

For example, to process the Advanced Placement data, change into the directory and then run the script:

```bash
cd statvar_imports/us_urban_school/ap_ib_gt_enrollment/advanced_placements/
bash run_process.sh
```

The processing script will:

1.  **Download the data** using `download_ap_ib_gt.py` and `download_2015_16.py`.
2.  Create an `output_files` directory.
3.  Process the downloaded data for each year.
4.  Generate statistical variables using the `stat_var_processor.py` script.
