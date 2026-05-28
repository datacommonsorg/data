\#!/bin/bash

# Step 1: Data Download

curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO\_R\_MWK\_TS/?format=SDMX-CSV&compressed=false" -o input\_files/deaths\_by\_week\_and\_sex\_data\_raw.csv

# Step 2: Data Processing

python3 ../../../tools/statvar\_importer/stat\_var\_processor.py   
"--input\_data=./input\_files/\*.csv"   
"--pv\_map=./deaths\_by\_week\_and\_sex\_pvmap.csv"   
"--config\_file=./deaths\_by\_week\_and\_sex\_metadata.csv"   
"--generate\_statvar\_name=True"   
"--skip\_constant\_csv\_columns=False"   
"--output\_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit"   
"--output\_path=./deaths\_by\_week\_and\_sex\_output"   
"--places\_resolved\_csv=./places\_resolved\_runtime.csv"   
"--existing\_statvar\_mcf=gs://unresolved\_mcf/scripts/statvar/stat\_vars.mcf" \\

