### Contaminant and Contaminated Media
Here we process the [Contaminant of concern data from Superfund decision documents issued in fiscal years 1982-2017](https://semspub.epa.gov/src/document/HQ/401062) dataset. This dataset describes the contaminants that have affected a superfund site with specific information on what media are contaminated at the site.

The dataset includes sites 1) final or deleted on the National Priorities List (NPL); and 2) sites with a Superfund Alternative Approach (SAA) Agreement in place. The only sites included that are 1) not on the NPL; 2) proposed for NPL; or 3) removed from proposed NPL, are those with an SAA Agreement in place.

#### How to get the dataset:
This dataset can be downloaded as a spreadsheet from the EPA Superfund's [data and reports page](https://www.epa.gov/superfund/superfund-data-and-reports) by clicking on the link with the name "Contaminant of concern data from Superfund decision documents issued in fiscal years 1982-2017".

> NOTE: The link to this dataset changes with every update. It is recommended to
> have a local copy of the file.

#### Script to generate the clean csv + tmcf:
    For adding Statistical Variable Observations

    ```shell
    python3 process_sites_contamination.py
    ```
#### Notes
2022/05 - The static file with DC node ids of contaminants is updated with
organic compounds. The **scripts do not create statistical variables for
organice compounds.**
2022/01 - The code currently does not import contaminants that are organic compunds.
