## Superfund National Priorities List (NPL) Sites with Status Information
The dataset of all superfund sites can be accessed in the table-view of [this EPA Arcgis applet](https://epa.maps.arcgis.com/apps/webappviewer/index.html?id=33cebcdfdd1b4c3a8b51d416956c41f1). This dataset shows each superfund site on the [National Priority List (NPL)](https://www.epa.gov/superfund/superfund-national-priorities-list-npl#:~:text=The%20National%20Priorities%20List%20(NPL,United%20States%20and%20its%20territories.) with their location attributes (name, address, city, state), geographic location (latitude, longitude), and the dates when a site had a change in NPL status.

#### How to get the dataset:
To download this dataset, please head to the [EPA Arcgis appliet](https://epa.maps.arcgis.com/apps/webappviewer/index.html?id=33cebcdfdd1b4c3a8b51d416956c41f1) and follow the steps based on the screenshot

<screenshots in screenshots.google.com>
1. Click on the "layers" icon, to see the layers of the map
2. Select the "Superfund National Priorities List (NPL) Sites with Status Information" layer
    a. Click the "three dot" icon to see a menu-> "Show Attribute Table"
3. In the upper-left corener of the table, Select "Option" -> "Export as CSV" to download the data

We also use the remedial action dataset to add info on the ownership of these sites, which is discussed in a subsequent section.

Additionally, we use the [Remedy Component Data for Decision Documents by Media, FYs 1982-2017](https://semspub.epa.gov/work/HQ/401063.xlsx) dataset that lists the different remedial actions carried out different superfund sites based on the contaminated media between 1982 to 2017. In this script, this dataset is used to map the ownership type (government-owned, privately-owned) of the site. 

This file can be downloaded with the [direct link](https://semspub.epa.gov/work/HQ/401063.xlsx) or by finding the dataset by name in the [EPA Superfund page](https://www.epa.gov/superfund/superfund-data-and-reports)

#### Script to generate the clean_csv + tmcf:
    For creating the nodes for superfund sites,
    ```shell
    python3 process_sites.py
    ```

    For adding Statistical Variable Observations on the status of the site on the NPL
    ```shell
    python3 process_sites_fundingStatus.py
    ```
    The `fundingStatus` dataset requires a StatisticalVariable definition, which is found in the [statvar.mcf](statvar.mcf) file.

    > using the argument `--help` with any of the above commands lists the different command line arguments that is expected.

#### Notes
1. We have another [EPA Superfund Applet](https://epa.maps.arcgis.com/apps/mapviewer/index.html?layers=c2b7cdff579c41bbba4898400aa38815) that lists more superfund sites but we had difficulties finding a means to export this data to csv.
2. The first run of `python3 process_sites.py` will take a few minutes to run, since the place mapping through the Data Commons recon API takes place first.



