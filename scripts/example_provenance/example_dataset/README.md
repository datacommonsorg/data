> This README is a template of what an import's README might look like.

# Importing <example_provenance> <example_dataset> Into Data Commons

Author: <github_handle>

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

[CSV | XLSX | TXT | etc.] file is available for download from <download_url>.

### Overview

> Explain as much as you need so that others can understand what the
dataset's variables are without digging into the data and documentation.
Here's an example skeleton you may find helpful:

This dataset is broken up into 3 major families of variables:
1. XXX: <description_of_XXX>
2. YYY: <description_of_YYY>
3. ZZZ: <description_of_ZZZ>

X is further broken down into:
1. a: <description_of_a>
2. b: <description_of_b>

Y is further broken down into:
1. aa: <description_of_aa>
2. bb: <description_of_bb>
3. cc: <description_of_cc>

Z is further broken down into:
1. aaa: <description_of_aaa>
2. bbb: <description_of_bbb>


### Notes and Caveats

> Some example notes/caveats:

- This dataset considers Honolulu County a city.
- This dataset is a best-effort and occasionally contains decreasing
  numbers for cumulative count statistics.
- This dataset's documentation warns users not to compare across years
  due to <some_statistical_reason>.

### License

> An example license summary:

This dataset is made available for all commercial and non-commercial
use under the FooBar Agreement.

The license is available online at <license_url>.

### Dataset Documentation and Relevant Links 

- Documentation: <documentation_url>
- Data Visualization UI: <some_other_url>

## Import Artifacts

### Raw Data
- <file_name_with_hyperlink>: <file_description>
- <file_name_with_hyperlink>: <file_description>

### Cleaned Data
- <file_name_with_hyperlink>: <file_description>
- <file_name_with_hyperlink>: <file_description>

### Template MCFs
- <file_name_with_hyperlink>: <file_description>
- <file_name_with_hyperlink>: <file_description>

### StatisticalVariable Instance MCF
- <file_name_with_hyperlink>: <file_description>
- <file_name_with_hyperlink>: <file_description>

### Scripts
- <file_name_with_hyperlink>: <file_description>
- <file_name_with_hyperlink>: <file_description>

### Notes

> Include any import related notes here. Here's an example:

New starting 2020-06-25, two new columns were added:

- abc
- def

These two variables have not been integrated into the import yet.

## Generating Artifacts

> Include any commands for running your scripts. This is especially relevant if
  your code relies on flags. Here's an example:

`statvar_filename.mcf` was handwritten.

To generate `template_filename.tmcf` and `data_filename.csv`, run:

```bash
python3 preprocess_csv.py
```

To run the test file `preprocess_csv_test.py`, run:

```bash
python3 -m unittest preprocess_csv_test
```
