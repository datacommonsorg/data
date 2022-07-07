## Measurement sites at superfund sites
> **IMPORTANT**: Please add a new entry to the existing csv, to ensure that older measurement sites that were added are untouched.

The level of contaminants at a superfund site, the level of clean-up done to remedy contaminated media at superfund sites are done by making measurements from sampling sites located within and aroung a superfund site. Through observations made at the sampling wells over a period of time it is possible to see the impact of different contaminants at the site on the surrounding areas and population.

This directory uses a csv file at [`data/measurement_sites.csv`](data/measurement_sites.csv) which has the following columns
`Site Name` - Name of the sampling site
`Latitude` - Latitude of the location of the superfund site
`Longitude` - Longitude of the location of the superfund site
`containedInPlace` - refers to the superfund site where the measurement site is present. This column is filled with the `**EPA ID**` of the superfund site, prefixed with `epaSuperfundSiteId/`. 
`dcid` - refers to the unique id on the KG for the measurement site. The convention for constructing this ID is explained in the example below.

#### Example to add a new measurement site to the `measurement_sites` csv
In this section, we add a new site to the [`data/measurement_sites.csv`](data/measurement_sites.csv) file.

In this example, we add a new measurement site in the [Tar Creek](https://en.wikipedia.org/wiki/Tar_Creek_Superfund_site) superfund site. Tar Creek has measurement sites which are sampling wells and in this example, we add a new well to the [`data/measurement_sites.csv`](data/measurement_sites.csv) file.

Before adding the new sampling well, the `data/measurement_sites.csv` file looks as follows:

|Site Name|Latitude|Longitude|containedInPlace|
|------------|--------|-------|--------|
|Picher #5 - MW|36.96544|-94.830952|OKD980629844|
|Picher #7 - MW|36.973079|-94.847524|OKD980629844|

The new sampling well want to add is `Quapaw#4` and we find this sampling well from Tar Creek's [five-year review report](https://semspub.epa.gov/src/document/06/100021610). The location for the site is inferred based on the image of a map of the site provided in every five-year review report of the site. Looking up for the closest location based on road networks and natural landmarks the location of the `Quapaw#4` is estimated to be in location with latitude: `36.94244` and longitude: `-94.787671`. 

> **TIP**: Setting a zoom-level which is at a 5km resolution was helpful to identify the location of sampling wells based on the road networks and natural landmarks. If the map in the review report for the site is not clear, it does help to look for the map of the measurement sites in earlier reports. In the case of Tar Creek, the 2015 review report had a better map of the sites that was used to identify the closest road networks for the sampling wells.

We know that the `Quapaw#4` sampling well is related to the Tar Creek superfund and the Tar Creek superfund site has the EPA ID: `OKD980629844`.

> **TIP**: If you need help finding the EPA ID of a superfund site, referring [this Arcgis EPA applet](https://epa.maps.arcgis.com/apps/webappviewer/index.html?id=33cebcdfdd1b4c3a8b51d416956c41f1) and finding the site by name will be helpful.

### Generating TMCF + CSV for the measurement sites
After the sites are added to the `measurement_sites.csv` file we generate the `mcf` file for the sites by running the following script,

```
python3 generate_mcf.py --input_file=data/measurement_sites.csv --output_path=data/output
```

This script also generated the `dcid` for each measurement site.

In the context of the Data Commons knowledge graph, the `dcid` is a unique `id` associated with a node or entity in the graph. In the context of `measurement_sites dataset`, each measurement site irrespective of it's type is a node. The `dcid` for a measurement site is constructed with three parts which are joined using `/`. The three parts constituting the dcid are:

1. Common identifying prefix: `epaSuperfundMeasurementSite`
2. The superfund site's EPA ID where the measurement site is present
3. Name of the site in `Snake_Case` where all punctuations and spaces are replaced with `_`. Example: `Quapaw#4` will be replaced with `Quapaw_4`.
Thus the resulting `dcid` for the `Quapaw#4` measurement site located in Tar Creek superfund site where the superfund has an EPA ID `OKD980629844` is `epaSuperfundMeasurementSite/OKD980629844/Quapaw_4`.

After adding `dcids`, the columns in the processed csv looks as follows:
|Site Name|Latitude|Longitude|containedInPlace|dcid|
|------------|--------|-------|--------|------------|
|Picher #5 - MW|36.96544|-94.830952|epaSuperfundSiteId/OKD980629844|epaSuperfundMeasurementSite/OKD980629844/Pitcher_5MW|
|Picher #7 - MW|36.973079|-94.847524|epaSuperfundSiteId/OKD980629844|epaSuperfundMeasurementSite/OKD980629844/Pitcher_7MW|
|Quapaw#4|36.94244|-94.787671|epaSuperfundSiteId/OKD980629844|epaSuperfundMeasurementSite/OKD980629844/Quapaw_4|

The processed csv is then used to generate the `measurement_sites.mcf` file which is stored in the specified `output_path`.

