# US FDA Drugs Import

## Table of Contents

- [Importing FDA Data](#importing-fda-data)
  - [About the Dataset](#about-the-dataset)
    - [Download Data](#download-data)
    - [Overview](#overview)
    - [Notes and Caveats](#notes-and-caveats)
    - [License](#license)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
      - [Files](#files)
    - [Import Procedure](#import-procedure)
      - [Download](#download)
      - [Run Scripts](#run-scripts)
      - [Additional Information](#additional-information)

## About the Dataset

### Download Data
The FDA drugs data can be directly downloaded from their official [website](https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files) under the download data section. 

### Overview
“Drugs@FDA includes information about drugs, including biological products, approved for human use in the United States (see FAQ), but does not include information about FDA-approved products regulated by the Center for Biologics Evaluation and Research (for example, vaccines, allergenic products, blood and blood products, plasma derivatives, cellular and gene therapy products). For prescription brand-name drugs, Drugs@FDA typically includes the most recent labeling approved by the FDA (for example, Prescribing Information and FDA-approved patient labeling when available), regulatory information, and FDA staff reviews that evaluate the safety and effectiveness of the drug.” </br>

The downloaded data bulk consists of the following files:

- ApplicationDocs.txt
- Applications.txt
- ApplicationsDocsType_Lookup.txt
- MarketingStatus_Lookup.txt
- MarketingStatus.txt
- Products.txt
- SubmissionClass_Lookup.txt
- SubmissionPropertyType.txt
- Submissions.txt
- TE.txt

### Notes and Caveats
Since the data is in .txt format, it's not too hard to ingest it in the knowledge graph, however, we faced some issues which are listed below:

- The entities in each of the files aren't inherently interlinked and mapped to each other which had to be accomplished programmatically. 
- Chemical compounds/drugs coming from the FDA import weren't linked to any standard chemical compound database, like PubChem or ChEMBL. We solved this issue by querying for the compound names through PubChem or ChEMBL python APIs, and for the compounds that didn't match to any (<10%), we simply used their chemical names as dcids. 
- The chemical compound strengths as stored as strings (ex: 250 MG/ML), however, in the knowledge graph, the node is stored as a string where it would be broken down into a numerical component (value) and unit of measurement (unitOfMeasure). This too is accomplished programmatically. 

### License
Drugs@FDA is public domain and made available with a Creative Commons CC0 1.0 Universal dedication.

## About the import

### Artifacts

#### Scripts

- ['format_app.py'](format_app.py)</br>
This file is used to format `Applications.txt`.
- ['format_application_docs.py'](format_application_docs.py)</br>
This file is used to format `ApplicationDocs.txt` and `ApplicationsDocsType_Lookup.txt`.
- ['format_product.py'](format_product.py)</br>
This file is used to format `Products.txt`
- ['format_submissions.py'](format_submissions.py)</br>
This file is used to format `SubmissionClass_Lookup.txt`, `SubmissionPropertyType.txt`, `Submissions.txt`
- ['format_te_market.py'](format_te_market.py.py)</br>
This file is used to format `MarketingStatus_Lookup.txt`, `MarketingStatus.txt`, `TE.txt`

#### Files

- ['chembl-mapping.json'](chembl-mapping.json)
This file stores the mapping between chemical compound names from FDA and their corresponding ChEMBL IDs obtained by using ChEMBL python api. 
- ['pubchem-mapping.json'](pubchem-mapping.json)
This file stores the mapping between chemical compound names from FDA and their corresponding PubChem CIDs obtained by using PubChem python api. 

### Import Procedure

#### Download

For the ease of downloading all files and generating formatted files, the user can just run the `run.sh` script:

```bash
bash run.sh
```

#### Additional Information

Dosage Form Enumerations are based on the information from https://www.fda.gov/industry/structured-product-labeling-resources/dosage-forms
Administration Route Enumerations are based on the information from https://www.fda.gov/drugs/data-standards-manual-monographs/route-administration

The main file for this import is Products.txt. Other information is pulled from the relevant files to provide more information. The following describes how each column in Products.txt is used or ingested:
* ApplNo is used to look up the Application from Applications.txt
  * FDAApplication is property of DrugStrength
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

* Drug name is ingested as drugName text property of Drug
* Drug Name is used to search for the corresponding ChEMBL ID or PubChem Compound ID in order to form an existing DCID already in the KG
  * If the drugName is not in the dict, then the ChEMBL python API is used to search for the drugName
  * Drugs whose names are not found by the two pass search system have a new DCID created for them based on a sanitized version of the drugName and will become new Drug nodes in the KG instead of appending to existing ones
* ActiveIngredients are appended list of text properties to each Drug node