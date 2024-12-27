# India CPCB Air Quality Data

This is an import of Air Quality dataset from [India CPCB website](https://airquality.cpcb.gov.in/caaqms/rss\_feed). This is an hourly RSS feed. 

This dataset involves two imports:
- Air Quality sites
- Air Quality data

**Air Quality Sites**
We need to import site info along with air quality data since the RSS feed may include new sites which have not been added to Data Commons.  Thus, we need to periodically import site data as well. In order to add sites, place resolution is performed. Each site includes LatLong information. These coordinates are used with the DC resolve API to retrieve the corresponding district dcid (WikiDataId). Finally,  this data is joined (using WikiDataId) with the India LGD dataset to obtain the LGD code for the corresponding district for each site. This LGD code along with site/city is used to construct SiteId in the form cpcbAq/LGDDistrictCode\_Station\_City

**Air Quality Data**
Steps involved in importing the air quality data:
- Convert the RSS feed to CSV using XSLT stylesheet
- Join the dataset with sites data (obtained in the previous step) using site name to get place information (SiteId) for each observation


**Known issues**
Few sites have “duplicate” stations which are differentiated only by a suffix attached to the site name. Current site id ignores the suffix (to align with historical site data already imported into KG). Thus, we drop air quality data associated with such duplicate sites in the current implementation.

**Script usage**

```
export DC_API_KEY=<api_key>
python process.py
```

The script can also read the air quality data from a file for processing using the flag dataFile.
