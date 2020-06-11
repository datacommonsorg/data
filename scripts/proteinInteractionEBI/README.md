# Scripts for importing ontology dataset from the European Bioinformatics Institute (EMBL-EBI)

This directory stores all scripts used to import datasets from the European Bioinformatics Institute (EMBL-EBI). 
Here we only import the three subsets of the ontologies: "interaction detection method", "interaction type" and "database citation", which are commonly used in protein-protein interactions. 

## Database format

The ontologies dictionary has a tree structure. Note here that one parent node can have multiple child nodes and one child node can have multiple parent nodes as well.
![Tree Structure](./graph/ontologyTree.png)
![Multiple Parent Node](./graph/multipleParent.png)

The original data file (mi.owl) uses "is_a" and "part_of" as the relation property to connect the child node to the parent node, however we don't distinguish these two and a property "specializationOf" is used for the child-parent connection.
![Original Data Sample](./graph/originalDataSample.png)

We make each term as a enumeration node of three subtrees with root nodes as: "database citation", "interaction detection method", and "interaction type". There are two main concerns that we didn't import all the nodes. First, we focus on the ontologies in protein-protein interaction and these three categories are the most commonly used. Secondly, importing too many general terms may cause the confusion in our dataCommons knowledge graph.  


## Algorthm for parsing the file

Parsing Steps:
1. build the tree by the psi-mi number. A dictionary {psi-mi: node} is used to access nodes as well. 
2. save all the tree nodes in the subtree of the three nodes into three set with depth first search:
    id: MI:0001 name: interaction detection method
    id: MI:0190 name: interaction type
    id: MI:0444 name: database citation
3. save the nodes in the three sets to the corresponding enumearation schema
"""

## Schema Overview

### New Properties: 
interactionDetectionMethod, interactionType, interactionSource, alias, psimi, isObsolete, publications.

### New Enumeration Schema:
BiomedicalOntologySubsetEnum, InteractionTypeEnum, InteractionDetectionMethodEnum, InteractionSourceEnum.


