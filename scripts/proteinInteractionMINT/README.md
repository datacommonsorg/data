# Scripts for importing ontology dataset from the Molecular INTeraction database (MINT)

```
proteinInteractionEBI
│   README.md
│   parseMINT.ipynb
|   parseMINT.py
|   BioMINTSchema.mcf (contains schema MCF and part of instances to be imported to KG)
|   schemaMCF.txt (contains only schema MCF)
│
└───graph
│   │   MINTexample.png

```

This directory stores all scripts used to import datasets from the Molecular INTeraction database (MINT). MINT contains publicly available protein-protein interactions and uses the Molecular Interaction Ontology of the Proteomics Standard Initiative (PSI-MI).

## Database format

The data can be downloaded at https://mint.bio.uniroma2.it/index.php/download/ 

The downloaded data is tab-separated format.

The dataset contains information for the interaction and the participant proteins. A full interaction example from the website is https://mint.bio.uniroma2.it/index.php/detailed-curation/?id=MINT-4409840. The features of each participant such as "Biological role", "Interactor type" are not included in the downloadable database thus we didn't import these features to Data Commons. The information available in the downloadable database is shown in the graph below.  

![A MINT Record](./graph/MINTexample.png)

A protein-protein interaction instance connects to partipant proteins through property "interactingProtein", connects to detection methods through property "interactionDetectionMethod", connects to interaction type through property "interactionType", connects to the source database through property "interactionSource", connects to related publications through property "references" and connects to related database records through property "identifier". The objects of "interactionType", "interactionDetectionMethod" and "interactionSource" are enumeration instances from EMBL-EBI Molecular Interaction Ontology database. The objects of "interactingProtein" are protein instances from UniPort.


## Links to Dev Browser

ProteinProteinInteraction class node 

https://datcom-browser-dev2.googleplex.com/kg?dcid=ProteinProteinInteraction

ProteinProteinInteraction instance nodes

https://datcom-browser-dev2.googleplex.com/kg?dcid=LITD1_HUMAN_REPS1_HUMAN&db=

https://datcom-browser-dev2.googleplex.com/kg?dcid=AMPH_HUMAN_AP2A_RAT&db= 

 

## Schema overview


### New class

ProteinProteinInteraction.

### New properties

interactingProtein, interactionType, interactionSource.

## Notes and Caveats

There are 133,167 records in the MINT database. Here we imported 129,585 records to Data Commons. The 3,582 records that we didn't import have problematic protein identifiers that we cannot connect them to UniProt right now.

## Reference

Licata, Luana, et al. "MINT, the molecular interaction database: 2012 update." Nucleic acids research 40.D1 (2012): D857-D861.
https://academic.oup.com/nar/article/40/D1/D857/2903552

## TODO

Complete parseMINT.py.
