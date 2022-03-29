## Sites

This directory has each superfund site whose historical contamination data we add to the Data Commons knowledge graph. 
We add the contamination data at the level of each site since they are available in the EPA five-year review reports that is published by each superfund site. 

When importing contamination data there are two steps to follow:
1. Adding new places of `placeType: SuperfundMeasurementSite`.
    The steps to add a new site is described in [measurement_sites/README.md](measurement_sites/README.md)
2. Download the five-year review reports and extract the tabular data before generating the clean csv, tmcf and statvar mcf files
    - The five-year review reports can be accessed for each Superfund site at their respective "Site Documents & Data" section. For example, [this link](https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.scs&id=0601269&doc=Y&colid=33990&region=06&type=SC) is for the Tar Creek superfund site.
    - Extracting tabular data and generating the clean csv, tmcf and statvar mcf files can be done using scripts. For example, imports for Tar Creek used the following scripts:
      - [`tar_creek/process_report2020.py`](tar_creek/process_report2020.py) extracts the tabular data from the 6th five-year review report for the Tar Creek superfund site, and stores the data to an intermediate csv file.
        > **NOTE:** The extracted tabular data in the intermediate csv file can contain some values that are not decoded correctly. In [`tar_creek/process_report2020.py`](tar_creek/process_report2020.py), we use `replace()` to fix the decoding issues.

      - [`tar_creek/process_contaminants.py`](tar_creek/process_contaminants.py) uses the intermediate csv file as input and generates the clean csv, tmcf and statvar mcf files.
      > **TIP:** It is recommended to spot-check decoding issues or bad comma-separation for values in the clean csv using the [`dc-import`](https://github.com/datacommonsorg/import) tool.

With these two steps, the import for new contamination data from other superfund sites can be done.
