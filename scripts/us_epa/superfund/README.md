## Superfund
Superfund is a clean programme run by the US EPA for monitoring and removing contaminated waste sites. 
This directory contains the scripts to generate the tmcf and clean csv for the different statistics for superfund sites

### Superfund sites on the National Priority List (NPL)
The dataset of all superfund sites can be accessed in the table-view of [this EPA Arcgis applet](https://epa.maps.arcgis.com/apps/webappviewer/index.html?id=33cebcdfdd1b4c3a8b51d416956c41f1). This dataset shows each superfund site on the [National Priority List (NPL)](https://www.epa.gov/superfund/superfund-national-priorities-list-npl#:~:text=The%20National%20Priorities%20List%20(NPL,United%20States%20and%20its%20territories.) with their location attributes (name, address, city, state), geographic location (latitude, longitude), and the dates when a site had a change in NPL status.

#### How to get the dataset:
To download this dataset, please head to the [EPA Arcgis appliet](https://epa.maps.arcgis.com/apps/webappviewer/index.html?id=33cebcdfdd1b4c3a8b51d416956c41f1) and follow the steps based on the screenshot

<screenshots in screenshots.google.com>
1. Click on the "layers" icon, to see the layers of the map
2. Select the "Superfund National Priorities List (NPL) Sites with Status Information" layer
    a. Click the "three dot" icon to see a menu-> "Show Attribute Table"
3. In the upper-left corener of the table, Select "Option" -> "Export as CSV" to download the data

We also use the remedial action dataset to add info on the ownership of these sites, which is discussed in a subsequent section.

#### Script to generate the clean_csv + tmcf:
    For creating the nodes for superfund sites,
    ```shell
    python3 process_sites.py
    ```

    For adding Statistical Variable Observations on the status of the site on the NPL
    ```shell
    python3 process_sites_fundingStatus.py
    ```
#### Notes
We have another [EPA Superfund Applet](https://epa.maps.arcgis.com/apps/mapviewer/index.html?layers=c2b7cdff579c41bbba4898400aa38815) that lists more superfund sites but we had difficulties finding a means to export this data to csv.
--

### Intersection of Natural Hazard Vulnerability and Superfund Site Location
Spreadsheet lists all active and upcoming Superfund sites and their vulnerability to 12 natural hazards using a vulnerability score between 0 and 100.

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
--

### Contaminant and Contaminated Media
- about the dataset
#### How to get the dataset:
#### Script to generate the clean_csv + tmcf:
    For adding Statistical Variable Observations
    ```shell
    ```
#### Notes
--

### Case study: Tar Creek Superfund site
Tar Creek's 5-year review reports from the EPA has a time-series on the contaminant levels.
These reports are in PDF format|EPA|[cumulis.epa.gov](https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.scs&id=0601269&doc=Y&colid=33990&region=06&type=SC)
#### How to get the dataset:
#### Script to generate the clean_csv + tmcf:
    For adding Statistical Variable Observations
    ```shell
    ```
#### Notes
--

### [Not yet complete] Contaminant and Remedial Action
- about the dataset
#### How to get the dataset:
#### Script to generate the clean_csv + tmcf:
    For adding Statistical Variable Observations
    ```shell
    ```
#### Notes
--