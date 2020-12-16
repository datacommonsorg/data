# US FDA Drugs Import
## About the Dataset
### URL
CSV is available for download from https://www.fda.gov/media/89850/download
### Overview
“Drugs@FDA includes information about drugs, including biological products, approved for human use in the United States (see FAQ), but does not include information about FDA-approved products regulated by the Center for Biologics Evaluation and Research (for example, vaccines, allergenic products, blood and blood products, plasma derivatives, cellular and gene therapy products). For prescription brand-name drugs, Drugs@FDA typically includes the most recent labeling approved by the FDA (for example, Prescribing Information and FDA-approved patient labeling when available), regulatory information, and FDA staff reviews that evaluate the safety and effectiveness of the drug.”
### License
Drugs@FDA is public domain and made available with a Creative Commons CC0 1.0 Universal dedication.

## Files

### main.py

Executing `python3 main.py` from the command line will download the Drugs@FDA data files from https://www.fda.gov/media/89850/download, then clean the raw data, and generate the mcf file.


### clean.py

Functions involving combining original data from different files and writing cleaned data to cleand_data.csv can be found in `clean.py`.

Required files are Products.txt, Applications.txt, TE.txt and MarketingStatus.txt.

A cleaned DataFrame containing all required data is returned from clean.get_df().

### generate_mcf.py

Functions involving parsing the clean DataFrame from clean.get_df() and writing the final mcf file for the FDA Drugs Import can be found in `write_mcf.py`.

### utils/config.py:

Contains MCF template strings, enum dictionaries, and other constants related to cleaning and reading the data files.

### utils/format.py:

Contains helper functions required by both clean.py and generate_mcf.py to convert data into correct quantity and quantity range formatting.

### utils/drug_refs.json

This file is used to store drug names and their ChEMBL IDs to avoid querying ChEMBL database for each drug every time the script is run.

Initial data came from generating chembl_ids.out using the following steps
chemblIDs.out (used to map drug names to their ChEMBL IDs) originates from chembl_27.0_molecule.ttl found at ftp://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBL-RDF/latest/

```
$ awk '{ if ($0~/^chembl_molecule:/) { molecule=$1; } else if ($0=="") { molecule=""; } if (molecule != "" && $0~/rdfs:label/) { print molecule, $0; }}' chembl_27.0_molecule.ttl > chemblIDs.out    
$ awk '$3 !~ "CHEMBL"' chemblIDs.out > chembl_ids.out
```
Then to convert chembl_ids.out to the initial drug_refs.json file. The following was performed in a Colab notebook:

```
import json
chemblDF = pd.read_csv('./chembl_ids.out', sep='\t', names=['chembl', 'name'])
chemblDF['chembl_clean'] = chemblDF['chembl'].apply(lambda x: ''.join(x.split(':')[1:]).strip())
chemblDF['name_clean'] = chemblDF['name'].apply(lambda x: ''.join(x.split('label')[1:]).strip(';').strip())
chemblDF['name_clean'] = chemblDF['name_clean'].str.replace('"', "")
chembl_dict = chemblDF.set_index('name_clean').to_dict()['chembl_clean']
with open("./chembl_ids.json", "w") as outfile:
    json.dump(chembl_dict, outfile)
```
A new copy of './drug_refs_updated.js is written with any new drug name : ChEMBL ID relations appended after clean.get_df() is called.

## AdditionalInformation

Dosage Form Enumerations are based on the information from https://www.fda.gov/industry/structured-product-labeling-resources/dosage-forms
Administration Route Enumerations are based on the information from https://www.fda.gov/drugs/data-standards-manual-monographs/route-administration

The main file for this import is Products.txt. Other information is pulled from the relevant files to provide more information. The following describes how each column in Products.txt is used or ingested:
* ApplNo is used to look up the Application from Applications.txt
  * FDAApplication is property of DrugStrength
  * Applications.txt also provides the manufacturer property for the DrugStrength node and the sponsor property for the FDAApplication node
  * Applications.txt provides the Application Type enum property for FDAApplication
* ProductNo is ingested as property of DrugStrength
* ApplNo and ProductNo are used together as look ups to match the Drug entry to the appropriate TECode and MarketingStatusID from TE.txt, and MarketingStatus.txt.
  * TECode and MarketingStatusID are properties of each DrugStrength for the Drug
  * TE.txt contains both TECodes and MarketingStatusIDs
  * MarketingStatus.txt only contains MarketingStatusIDs
    * MaketingStatus_Lookup.txt was used to match marketingStatusID to the marketingStatus
  * In the case of conflicting MarketingStatusIDs from the two files, both IDs are added to the KG
* The Form column is split by the semicolon with the general format of <DosageForm> ; <AdministrationRoute> wich are both enum properties of Drug
  * If AdministationRoute specifies the drug course (ie Oral-28), then the drugCourse is saved as a property of the drugStrength (ie drugCourse: [28 "days"] )
  * If AdministrationRoute specifies a dosage pattern (ie SINGLE-USE), then the singleDose boolean property of DrugStrength is appropriately set
* The Strength designates the amount of each ActiveIngredient in the drug, therefore the Strength column and ActiveIngredient column must be read together
  * Typical Format (1:1 ratio of strength quantities to activeIngredient):
    * Each Drug points to one DrugStrength node. This DrugStrength node has properties of type ActiveIngredientAmount in which each ActiveIngredientAmount node indicates a single strengthQuantity/ActiveIngredient pair.
    * Sometimes there are equivalent quantities listed in a single ActiveIngredientAmount node (ie ingredientStrength: [10 "mg/2ml"], [5 "mg/ml"]
  * Special Cases:
    * When there are equal number of semicolons in Strength and ActiveIngredient, then the ingredient is zipped to the amount by the comma
      * Ex: 1 mg, 2mg, 3mg; 4mg, 5mg, 6mg    ingred1 ; ingred2
      * Strength 1:  1mg - ingred1, 4mg-ingred2
      * Strength 2: 2mg - ingred1, 5mg - ingred2
      * Strength 3: 3mg-ingred1, 6mg - ingred2
    * When there is unequal semicolons, but equal number of strengths per semi as ingredient, ingredients are zipped to strengths by semi colon
      * Ex: 1mg, 2mg; 3mg, 4mg; 5mg, 6mg     ingred1;ingred2
      * Strength 1: 1mg - ingred1, 2mg-ingred2
      * Strength 2: 3mg - ingred1, 4mg-ingred2
      * Strength 3: 5mg-ingred1, 6mg-ingred2
    * Otherwise all of the listed strengths and the active Ingredients are listed under one Strength node
      * Ex: 1mg; 2mg; 3mg     ingred1; ingred2
      * Strength node → [1 mg],[2 mg],[3 mg]
      * Strength node → "ingred1","ingred2"
* ReferenceDrug is ingested as isAvailableGenerically boolean property of Drug
* Drug name is ingested as drugName text property of Drug
* Drug Name is used to search for the corresponding ChEMBL ID in order to form an existing DCID already in the KG
  * To get the ChEMBL ID, a dictionary of ChEMBL IDs is created from chembl_27.0_molecules.ttl from ChEMBL DB
  * If the drugName is not in the dict, then the ChEMBL python API is used to search for the drugName
  * Drugs whose names are not found by the two pass search system have a new DCID created for them based on a sanitized version of the drugName and will become new Drug nodes in the KG instead of appending to existing ones
* ActiveIngredients are appended list of text properties to each Drug node
* ReferenceStandard is ingested as the boolean Drug property called isReferenceStandard
* All Drug Nodes have the recognizingAuthority property labeled as dcid:USFederalDrugAdministration
Organization type node is created for FDA at the beginning of the data MCF
