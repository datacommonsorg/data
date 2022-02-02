### Contaminant and Contaminated Media
Here we process the [Contaminant of concern data from Superfund decision documents issued in fiscal years 1982-2017](https://semspub.epa.gov/src/document/HQ/401062) dataset. This dataset describes the contaminants that have affected a superfund site with specific information on what media are contaminated at the site.

The dataset includes sites 1) final or deleted on the National Priorities List (NPL); and 2) sites with a Superfund Alternative Approach (SAA) Agreement in place. The only sites included that are 1) not on the NPL; 2) proposed for NPL; or 3) removed from proposed NPL, are those with an SAA Agreement in place.

#### How to get the dataset:
This dataset can be downloaded as a spreadsheet using [the direct download link](https://semspub.epa.gov/src/document/HQ/401062)

If the link did not work, the dataset can be found by name in the [EPA Superfund page](https://www.epa.gov/superfund/superfund-data-and-reports)

#### Script to generate the clean_csv + tmcf:
    For adding Statistical Variable Observations
    
    ```shell
    python3 process_sites_contamination.py
    ```
#### Notes
2022/01 - The code currently does not import contaminants that are organic compunds.