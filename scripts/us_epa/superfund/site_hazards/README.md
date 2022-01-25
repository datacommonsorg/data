### Intersection of Natural Hazard Vulnerability and Superfund Site Location
Spreadsheet lists all active and upcoming Superfund sites and their vulnerability to 12 natural hazards using a vulnerability score between 0 and 100.Additional risk/exposure metrices are also imported. The metrics described in this dataset can be better understood from the following scientific articles:

1. [Regionalizing resilience to acute meteorological events: Comparison of regions in the U.S](https://pubmed.ncbi.nlm.nih.gov/33447596/)
2. [National Hazards Vulnerability and the Remediation, Restoration and Revitalization of Contaminated Sites-2. RCRA Sites](https://pubmed.ncbi.nlm.nih.gov/34123411/)

This dataset is associated with the following publication: Summers, K., A. Lamaper, and K. Buck. National Hazards Vulnerability and the Remediation, Restoration and Revitalization of Contaminated Sites – 1. Superfund. ENVIRONMENTAL MANAGEMENT. Springer-Verlag, New York, NY, USA, 14, (2021).


#### How to get the dataset:
To download the dataset, visit [catalog.data.gov](https://catalog.data.gov/dataset/intersection-of-natural-hazard-vulnerability-and-superfund-site-location) and you will be able to find the dataset in excel format under the Downloads section under `SF_CRSI_OLEM.xlsx` filename.

#### Script to generate the clean_csv + tmcf:
    For creating tmcf + clean csv for Statistical Variable Observations 
    ```shell
    python3 process_sites_hazards.py
    ```
#### Notes
The dataset has only observations for 1 year, and hence when visualized you will see a single data point.
