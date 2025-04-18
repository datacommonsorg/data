About Opendataafrica:
OpenAFRICA is a platform that provides access to a wide range of open data from across the African continent. It aims to make data easily discoverable and usable for various purposes, including research, development, and civic engagement. The platform uses a standardized data format called SDMX (Statistical Data and Metadata eXchange) to ensure interoperability and consistency.

Folder Structure:
1.download.sh:This script is basically used to download the xml data of Opendataafrical coutries.
2.xml_to_json.py: This python script is used to convert the xml files into json files.
3.json_to-csv.py:This python script is used to convert the json files into final csv files.
4.xml_to_json_test.py:This is a test script to test the functionality of xml_to_json script.


- how to download data: automatic download

Dependancy:
Before running the script we have to install few packages mentioned in the requirement.txt using pip.
### How to run:

bash download.sh '{country_name}' '{csv folder path to store csv files}'
Example:
bash download.sh 'cotedivoire' 'opendata_csv_folders'
bash download.sh 'egypt' 'opendata_csv_folders'

To download specific dataset
bash download.sh 'cotedivoire' 'opendata_csv_folders' 'qdanpdb,sfulpbb'

Installation part:
pip install xmltodict
