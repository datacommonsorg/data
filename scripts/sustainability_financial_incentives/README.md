# Textproto to CSV Conversion Script

This script converts financial incentive data from textproto format to CSV format.

## Updating the Schema

If the schema of the input textproto files changes, you will need to update the protobuf definition file (`sustainable_financial_incentives.proto`) and regenerate the Python code.

1. **Update the `.proto` file:**
    Modify `sustainable_financial_incentives.proto` to reflect the new schema. This may involve adding or changing fields and enums.

2. **Regenerate the Python code:**
    Run the following command from the `scripts/sustainability_financial_incentives` directory to regenerate the `sustainable_financial_incentives_pb2.py` file:

    ```bash
    protoc -I=. --python_out=. sustainable_financial_incentives.proto
    ```

## Running the Script

To convert a textproto file to CSV, run the script from the `scripts/sustainability_financial_incentives` directory with the following command. You can use flags to specify the input and output paths:

```bash
python convert_textproto_to_csv.py --textproto_path=<path_to_input.textproto> --csv_path=<path_to_output.csv>
```

**Example:**

```bash
python convert_textproto_to_csv.py --textproto_path=testdata/all_incentives.textproto --csv_path=output.csv
```

## Running the Tests

To run the unit tests for this script, execute the following command from the `scripts/sustainability_financial_incentives` directory:

```bash
python -m unittest convert_textproto_to_csv_test.py
```
