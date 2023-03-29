# Processing super/enhanced TMCF and mapping files for the CSV data.

This directory contains scripts to process a super/enhanced TMCF file (see `sample_input_tmcf.tmcf` file) and
a mappings file which points to data CSV files at a remote location (see `sample_census_mappings.txt`). The output
is a usual TMCF file with processed data CSV files which can then be used with the dc-import tool for resolution.

The following steps are performed (in `process_mappings.py`):

1. Using the FLAGS provided, first check that the input TMCF + mappings files are found. Note: there are sample files provided (in this same directory) for the mappings and super/enhanced TMCF for one US Census table.
2. Use the mappings file to download all the zip files (if not already done).
3. Unzip the downloaded zip files and keep the CSV file with the relevant Data (identified by the `data_csv_file_unique_substring` flag).
4. Write all downloaded data CSV files to the input directory.
5. Process the super/enhanced TMCF file along with all the CSV files downloaded. It is assumed that all CSV files correspond to the same super/enhanced TMCF.
6. Parse all the CSV files with the super/enhanced TMCF and produce one (traditional) TMCF file with modified CSV files.
7. The output directory contains all the produced output files (one TMCF and processed CSV files). They can now be validated with the dc-import tool.


## US Census
Note that while the current implementation is being tested on the U.S. Census tables, the same
format can be used for other imports as well.

## Generating and Validating Artifacts

0. To run unit tests:

      ```
      python3 -m unittest discover -v -s ../ -p "*etmcf_test.py"
      ```

1. Ensure that a `data_directory` exists with an `input_directory` which has a mappings text file (e.g. `mappings.txt`) and a super/enhanced TMCF file (e.g. `input.tcmf`). See `sample_input_tmcf.tmcf` and `sample_census_mappings.txt` as samples files.

2. Provide all FLAGS in `process_mappings.py` and execute the script:

      ```
      python3 process_mappings.py --data_directory=<> -- ......
      ```

3. To validate and generate the MCF outputs, run the [dc-import](https://github.com/datacommonsorg/import#using-import-tool) tool as:

    ```
    dc-import genmcf -ep --allow-non-numeric-obs-values <output_folder>/*.tmcf <output_folder>/*.csv
    ```
