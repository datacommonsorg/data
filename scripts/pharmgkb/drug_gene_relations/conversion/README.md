## Conversion Files

### Overview
The `.csv` files found in are used to convert external ids into dcids, which are based on ChEMBL IDs. The tools used for conversion are listed below:

- (PharmGKB --> Chembl) and (PubChem Compound ID --> Chembl) both use UniChem API.
  - For more info: https://www.ebi.ac.uk/unichem/info/webservices#GetSrcCpdIds

- (InChI --> InChI Key) uses InChI API.
  - For more info: https://www.chemspider.com/InChI.asmx?op=InChIToInChIKey

- (InChI Key --> Chembl) uses ChEMBL Python API.
  - For more info: https://github.com/chembl/chembl_webresource_client

Requirements:
    pip install chembl_webresource_client

#### Note
Generating the csv files takes at least  3 hours!

### Py Files
- `generate_conversion_files.py` querries UniChem, InChI, and Chembl web resources to find Chembl ids matching the provided identifer.
- `generate_conversion_files_tests.py` contains unit tests for generate_conversion_files.py


### Generating CSVs
To generate the csv files, run

``` bash
$python3 generate_conversion_files.py
```
You will prompted to confirm that you do wish to run `generate_conversion_files.py`, since it takes a considerable amount of time to complete.

To run the unit tests for generate_conversion_files.py run

```bash
$python3 generate_conversion_files_test.py
```
