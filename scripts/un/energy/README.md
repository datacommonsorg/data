# UN Energy Dataset import

This folder includes scripts to download and process the annual UN Energy dataset from https://unstats.un.org/.

The UN, Energy Statistics Database contains comprehensive energy statistics on the production, trade, conversion and final consumption of primary and secondary; conventional and non-conventional; and new and renewable sources of energy. This data is obtained annually through an [energy questionnaire](https://unstats.un.org/unsd/energystats/questionnaire/documents/Energy-Questionnaire-Guidelines.pdf) from all countries.

The data set is organized by energy source types and for each source, the csv file contains values for different applications, also called transaction flows with quantity per country per year from 1990. 

The data set can be downloaded from [UNData explorer](http://data.un.org/Explorer.aspx) with the following API:
```
https://data.un.org/Handlers/DownloadHandler.ashx?DataFilter=cmID:${ID}&DataMartId=EDATA&Format=csv&c=0,1,2,3,4,5,6,7,8&s=_crEngNameOrderBy:asc,_enID:asc,yr:desc
Where ${ID} is a 2-letter energy code, for eg: 'BT' for Bitumen, 'MO' for Motor gasoline, 'KR' for Kerosene.
```

## Run

To download and process the data:
```bash
python3 -m un/energy/process.py
```

This downloads multiple csv files into a tmp_data_dir/ folder and generates *.csv with accompanying *.mcf and *.tmcf.


To run tests:
```bash
python3 -m unittest un/energy/process_test.py
```
