# Check Indian Districts WikidataId

## About This Tool

The purpose of this script is to facilitate the manual labor of checking that the wikidataId matches the data.
This script will export a `./output.csv` file in the following format:

``wikidataId,country=India,districtName,wikidataName
Q4726845,True,Alipurduar,Alipurduar district
Q2088458,True,Bankura,Bankura district
Q2088440,True,Birbhum,Birbhum district``

## CSV Column Names

1. wikidataId is the wikidataId for the given district name.
2. country=India will be True if WikiData confirms that the place belongs to India.
3. districtName is the distrist name as per Covid19India.org.
4. wikidataName is the district's name as per WikiData.
IMPORTANT: Ensure that the names match and that the district belongs to India.

One must then manually check that the districtName and the wikidataName match and that it belongs to the country of India.
NOTE: Some districts might return country=India False because WikiData does not contain the country.

## How to Run The Script

```shell
python3 CheckWikidataId.py
```
