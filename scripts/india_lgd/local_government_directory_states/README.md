# Local Government Directory - States

## About the Dataset
[Local Government Directory](https://lgdirectory.gov.in/) is a complete directory of land regions/revenue, rural and urban local governments.

### Overview
States data is available from the Local Government Directory for viewing and [downloading](https://lgdirectory.gov.in/downloadDirectory.do?OWASP_CSRFTOKEN=G4BW-2HK0-ZHUD-605W-VA1F-EAC8-M9J0-W4S5).

The LGD dataset has the following columns
- S No
- State Code
- State Version
- State Name (In English)
- State Name (In Local)
- Census 2001 Code
- Census 2011 Code
- State or UT

WikiData of States and Union territories of India is [downloaded](https://w.wiki/3bym) using the SPARQL endpoint. [Query](https://w.wiki/3byk) used is below

```
SELECT DISTINCT ?S ?SLabel ?SDescription ?isoCode ?census2001Code WHERE {
  # where s is "state of india" aka wd:Q12443800 or is "union territory of India" aka wd:Q467745
  { ?S wdt:P31 wd:Q12443800.}
  UNION
  { ?S wdt:P31 wd:Q467745. }
  
  # remove the ones with dissolved property
  # S has the dissolved property, lets call it dt     
  FILTER(NOT EXISTS { ?S wdt:P576 ?dt. })
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  OPTIONAL { ?S wdt:P300 ?isoCode. } 
  OPTIONAL { ?S wdt:P3213 ?census2001Code. } 
}
```

The WikiData dataset has the following columns
- S - WikiData URL
- SLabel - Label of the item
- SDescription - Description
- isoCode - ISO Code of the state or UT
- census2001Code - Census 2001 Code

#### Cleaned Data

The cleaned CSV has the following columns

- WikiDataId
- Name - Name in Latin
- StateCode - LGD state code
- Census2001Code - Census of India 2001 code
- Census2011Code - Census of India 2011 code


#### Template MCFs
- [LocalGovernmentDirectory_States.tmcf](LocalGovernmentDirectory_States.tmcf).

#### Scripts
- [preprocess.py](preprocess.py): Clean up and import script.

### Running Tests

```bash
python3 -m unittest discover -v -s scripts/ -p *_test.py
```

### Import Procedure

To import data, run the following command:

```bash
`python -m india_lgd.local_government_directory_states.preprocess`
```
