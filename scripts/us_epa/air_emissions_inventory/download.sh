mkdir -p "scripts/us_epa/air_emissions_inventory/input_html_files"
for i in 2008 2011 2014 2017
do
    curl  -X GET "https://enviro.epa.gov/enviro/nei.htm?pType=TIER&pReport=county&pState=DUMMY&pPollutant=&pPollutant=NH3&pPollutant=CO&pPollutant=NOX&pPollutant=PM10-PRI&pPollutant=PM25-PRI&pPollutant=SO2&pPollutant=VOC&pTier=&pTier=13&pTier=04&pTier=01&pTier=02&pTier=03&pTier=11&pTier=05&pTier=14&pTier=12&pTier=07&pTier=06&pTier=08&pTier=09&pTier=10&pYear=${i}&pCounty=&pSector=&pWho=NEI" -o "scripts/us_epa/air_emissions_inventory/input_html_files/"${i}_allstates.html 
done
