# Local Government Directory - Districts

## About the Dataset
[Local Government Directory](https://lgdirectory.gov.in/) is a complete directory of land regions/revenue, rural and urban local governments.

### Overview

#### LGD Data
Districts data is available from the Local Government Directory for viewing and [downloading](https://lgdirectory.gov.in/downloadDirectory.do?OWASP_CSRFTOKEN=G4BW-2HK0-ZHUD-605W-VA1F-EAC8-M9J0-W4S5).

The LGD dataset has the following columns
- District Code
- District Name(In English)
- State Code
- State Name (In English)
- Census 2001 Code
- Census 2011 Code

#### WikiData

WikiData of Districts of India is [downloaded](https://w.wiki/3fLF) using the SPARQL endpoint. [Query](https://w.wiki/3fLE) used is below

```
SELECT DISTINCT ?district ?districtLabel ?districtDescription ?state ?stateLabel ?stateDescription ?Census2011Code  WHERE {
  ?district wdt:P31 wd:Q1149652 ; wdt:P131/wdt:P131? ?state . ?state wdt:P31/wdt:P279 wd:Q131541.
  FILTER(NOT EXISTS { ?district wdt:P576 ?dt. })
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  OPTIONAL { ?district wdt:P5578 ?Census2011Code. }
}
```

The WikiData dataset has the following columns
- district - WikiData URL
- districtLabel - Label of the district item
- districtDescription - Description of the district item
- state - WikiData URL
- stateLabel - Label of the state item
- stateDescription - Description of the state item
- census2011Code - Census 2011 Code


#### Clean CSV

- LGDDistrictCode - District code as per LGD
- LGDDistrictName - District name as per LGD
- LGDStateCode - State code as per LGD
- LGDStateName - State name as per LGD
- LGDCensus2001Code - Formatted Census 2001 Code 
- LGDCensus2011Code - Formatted Census 2001 Code
- district -  WikiData district item URL
- districtLabel - WikiData label of the district item
- districtDescription - WikiData Description of the district item
- state -  WikiData state item URL
- stateLabel - WikiData label of the state item
- stateDescription - WikiData Description of the state item
- census2011Code - WikiData Census 2011 code
- WikiDataId - District WikiDataId
- LGDDistrictNameTitleCase - Formatted LGD District Name
- districtLabelTitleCase - WikiData district label in title case
- closestDistrictLabel - Matched WikidData `districtLabel`. Matching is based on the algorithm defined in the function `get_closest_district_label`. So in a clean and valid CSV the value of this column will be same as `districtLabel`.


#### Template MCFs
- [LocalGovernmentDirectory_Districts.tmcf](LocalGovernmentDirectory_Districts.tmcf).


#### Reconciliation
1. The states are resolved using lgdCode, which is expected to be added to the KG first. All states are expected to resolve.
2. The districts are expected to be resolved using the wikidataId (because indianCensusAreaCode20* coverage for districts is poor).
3. New districts might be created.


#### Scripts
- [preprocess.py](preprocess.py): Clean up and import script.

### Running Tests

```bash
python3 -m unittest discover -v -s scripts/ -p *_test.py
```

### Import Procedure

To import data, run the following command:

```bash
python -m india_lgd.local_government_directory_districts.preprocess
```

