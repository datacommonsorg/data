# UN Energy Dataset import

This folder includes scripts to download and process the annual UN Energy dataset from https://unstats.un.org/.

The UN, Energy Statistics Database contains comprehensive energy statistics on the production, trade, conversion and final consumption of primary and secondary; conventional and non-conventional; and new and renewable sources of energy. This data is obtained annually through an [energy questionnaire](https://unstats.un.org/unsd/energystats/questionnaire/documents/Energy-Questionnaire-Guidelines.pdf) from all countries.

The data set is organized by energy source types and for each source, the csv file contains values for different applications, also called transaction flows with quantity per country per year from 1990. 

The data set can be downloaded from [UNData explorer](http://data.un.org/Explorer.aspx) with the following API:
```
https://data.un.org/Handlers/DownloadHandler.ashx?DataFilter=cmID:${ID}&DataMartId=EDATA&Format=csv&c=0,1,2,3,4,5,6,7,8&s=_crEngNameOrderBy:asc,_enID:asc,yr:desc
Where ${ID} is a 2-letter energy code, for eg: 'BT' for Bitumen, 'MO' for Motor gasoline, 'KR' for Kerosene.
```

The energy data file has the following columns:
- Commodity Code:  2-letter code for the energy/fuel source
- Country or Area Code: ISO-3166 numeric country code
- Country or Area: Name of the country
- Transaction Code: Alphanumeric code indicating the energy generation or usage
- Commodity - Transaction Code: Concatenated commodity transaction code
- Commodity - Transaction: Description of the energy transaction
- Year
- Unit
- Quantity
- Quantity Footnotes: Indicates if the Quantity is an estimate


The import process generates the following files:
- mcf: all StatVar definitions
- tmcf: template for mapping csv to a StatVarObservation
- csv: with one row for each StatVarObs with the following columns
    - Country_dcid
    - Year
    - Quantity
    - Unit_dcid
    - Scaling_factor
    - Estimate
    - StatVar


## Run

Run all following commands from the data/scripts directory.

To download and process the data:
```bash
python3 un/energy/process.py
```
This downloads multiple csv files into a tmp_data_dir/ folder and generates .csv with accompanying .mcf and .tmcf. There are about 300 csv files that take about 10 minutes to download.

To download the data:
```bash
python3 un/energy/download.py --download_data_dir=tmp_data_dir/un_energy

# Merge all csv into a single file
cat tmp_data_dir/un_energy*/*.csv > tmp_data_dir/un_energy_all.csv
```

To process a set of downloaded files:
```bash
python3 un/energy/process.py --csv_data_files=tmp_data_dir/un_energy_all.csv --output_path=tmp_raw_data/un_energy_output
```

This would generate the files: tmp_raw_data/un_energy_output.{csv, mcf, tmcf}

To run tests:
```bash
# from the data/scripts directory
python3 -m unittest un/energy/process_test.py
```
