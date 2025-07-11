# Sustainability Financial Incentives Data Import

This directory contains tools and processes for importing sustainability financial incentives data into the Data Commons platform.

## Prerequisites

1. **Google Cloud Authentication**: Ensure you have proper GCS access credentials configured
2. **Python Dependencies**: Install required packages:
   ```bash
   pip install -r requirements_all.txt
   ```

## Data Download and Conversion

The `download_and_convert.py` script downloads the latest sustainability financial incentives data from Google Cloud Storage and converts it from JSON to CSV format for Data Commons ingestion.

### Overview

The script performs the following operations:
1. **Discovers the latest data**: Finds the most recent dated folder (YYYY_MM_DD format) in the GCS bucket
2. **Downloads JSON data**: Retrieves the financial incentives JSON file from GCS
3. **Converts to CSV**: Transforms the JSON data to CSV format using the Data Commons json_to_csv utility

### Usage

**Basic usage:**
```bash
python download_and_convert.py
```

**With custom output file:**
```bash
python download_and_convert.py --output_csv=latest_incentives.csv
```


### Output

The script generates:
- **JSON file**: Downloaded to the input_files directory
- **CSV file**: Converted data ready for Data Commons ingestion
- **Detailed logs**: Processing status and file locations

## Testing

Run the unit tests:
```bash
python -m unittest download_and_convert_test.py
```

## Troubleshooting

**Common Issues:**
- **Authentication errors**: Ensure GCS credentials are properly configured
- **Permission errors**: Check read permissions on the GCS bucket
- **File not found**: Verify the JSON filename exists in the latest dated folder

All log messages include full file paths to help with troubleshooting.