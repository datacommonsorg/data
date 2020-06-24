#!/usr/bin/env python
# coding: utf-8

import collections
import re
import sys


def get_class_name_helper(astring):
    """Convert a name string to format: ThisIsAnUnusualName.
    
    Take a space delimited string, return a class name such as ThisIsAnUnusualName 
    Here we use this function for instance name. Thus it allows to start with a number
    """
    jointName = astring.title().replace(" ","")
    # substitute except for  _, character, number
    nonLegit = re.compile(r'[\W]+')
    className = nonLegit.sub('', jointName)
    return className

def get_class_name(astring):
    return get_class_name_helper(astring)

def get_property_name(astring):
    """Convert a name string to format: thisIsAnUnusualName.
    Take a space delimited string, return a property name such as thisIsAnUnusualName 
    """
    className = get_class_name_helper(astring)
    return className[0].lower()+className[1:]


def get_references(term):
    """Convert reference string to the corresponding reference property schema
    
    Args:
        term: a string with the format "source:idNum"
    
    Returns:
        a tuple: (propertyLine,newSourceMap). propertyLine is the reference 
        property in schema, and newSourceMap is the dictionary of with source
        name as the key and the identifier as the value, if new source exists.
        For example:
        
        ("pubMedID: 1007323", {aNewSource:100100})
    """
    source = term.split(":")[0]
    idNum = ":".join(term.split(":")[1:])
    newSourceMap = {}
    if source == "PMID" or source == "pmid":
        propertyLine =  "pubMedID: " + "\"" + idNum +"\""
    elif source == "GO":
        propertyLine =  "goID: " + "\"" + idNum +"\""
    elif source == "RESID":
        propertyLine =  "residID: " + "\"" + idNum +"\""
    elif source == "doi":
        propertyLine =  "digitalObjectID: " + "\"" + idNum +"\""
    else:
        newReference[source] = idNum
        propertyLine = None
        
    return (propertyLine, newSourceMap)


class Node(object):
    """Node class for containing each ontology
    Attributes:
        value: A string shows the ontology name
        parentList: A list of Node contains the parent nodes. One node can have multiple parent nodes.
        childList: A list of Node contains the child nodes.     
    """
    def __init__(self, value):
        self.value = value
        self.parentList = []
        self.childList = []
        
def get_parent_id_list(termList):
    """Takes a list with string elements of a node, return a list containing string identifiers of its parent nodes. 
    Args:
        termList: for example:
        ['id: MI:0000',
         'name: molecular interaction',
         'def: "Controlled vocabularies originally created for protein protein interactions, extended to other molecules interactions." [PMID:14755292]',
         'subset: Drugable',
         'subset: PSI-MI_slim']
    
    Returns:
        idStringList: a list of string identifiers of its parent nodes. For example:
        ["MI:0013", "MI:1349"]
    
    """
    idStringList = []
    for term in termList:
        '''
        term containining parent information is "is_a: MI:0013 ! biophysical" 
        or "relationship: part_of MI:1349 ! chembl"
        ''' 
        if term.startswith("is_a"):
            idStringList.append(term.split(" ")[1])
        elif term.startswith("relationship"):
            idStringList.append(term.split(" ")[2])
        else: continue
            
    return idStringList

class GetTreeValues(object):
    """A computation class to get all the node values of a subtree from the subtree root by DFS.
    
    Attributes:
        nodeValueSet: a set to save and return all the node values in the subtree
    """
    
    def __init__(self):
        self.nodeValuesSet = set()

    def get_subset_id(self, node):
        """Takes the string identifer such as "MI:1349" as the root node value
            returns all the tree node values as a set."""
        # reset the value set to be empty every function call
        self.nodeValuesSet = set()
        # run a DFS on the tree
        self.dfs(node)
        return self.nodeValuesSet

    def dfs(self, node):
        """Takes a tree node as root, do a DFS tree traversal recursively"""
        if not node: return
        self.nodeValuesSet.add(node.value)
        for child in node.childList:
            self.dfs(child)


def get_schema_from_text(term, id2node, newSourceMap, id2className,interactionTypeIdSet,detectionMethodIdSet,interactionSourceIdset):
    
    """Takes a list with each item containing the information, return a list: [data schema, PSI-MI, DCID] 
    Args:
        term: For example:
        ['id: MI:0000',
         'name: molecular interaction',
         'def: "Controlled vocabularies originally created for protein protein interactions, extended to other molecules interactions." [PMID:14755292]',
         'subset: Drugable',
         'subset: PSI-MI_slim']
    Returns:
        [data schema, PSI-MI, DCID], for example:
        ['''Node: dcid:Biophysical
        typeOf: dcs:InteractionTypeEnum
        name: "Biophysical"
        psimiID: "MI:0013"
        description: "The application of physical principles and methods to biological experiments"
        pubMedID: "14755292"
        specializationOf: dcs:ExperimentalInteractionDetection''','MI:0001', "Biophysical", {"references":{"newConfidence":"AA10010"}}]
        
    """
    termDic = collections.defaultdict(list)
    for line in term:
        lineList = line.split(": ")
        key = lineList[0]
        value = ": ".join(lineList[1:])
        termDic[key].append(value)
        
    defLong = termDic['def'][0]
    idStart = defLong.rfind('[')
    description = defLong[1:idStart-1-2]
    termDic['def'] = [description]
    IDString = defLong[idStart+1:-1]
    if len(IDString)>0:
        IDList = defLong[idStart+1:-1].split(", ")
        termDic['references']= IDList     
    
    schemaPieceList = []
    keyList = ["id", "def","references","parentClassName"]
    
    idString = termDic['id'][0]
    dcid = id2className[idString]
    
    curLine = "Node: dcid:" + dcid
    schemaPieceList.append(curLine)
    
    if idString in interactionTypeIdSet:
        curLine = "typeOf: dcs:InteractionTypeEnum"
    elif idString in detectionMethodIdSet:
        curLine = "typeOf: dcs:InteractionDetectionMethodEnum"
    elif idString in interactionSourceIdset:
        curLine = "typeOf: dcs:InteractionSourceEnum"
    else:
        return None
        
    termDic["parentClassName"] = [id2className[node.value] for node in id2node[idString].parentList] 
    schemaPieceList.append(curLine)
    
    curLine = "name: \"" + dcid + "\""
    schemaPieceList.append(curLine)

    '''
    termDic:
    id:  ['MI:0001']
    name:  ['interaction detection method']
    def:  ['Method to determine the interaction']
    subset:  ['Drugable', 'PSI-MI_slim']
    synonym:  ['"interaction detect" EXACT PSI-MI-short []']
    relationship:  ['part_of MI:0000 ! molecular interaction']
    references:  ['PMID:14755292']
    parentClassName:  ['MolecularInteraction']
    '''
    
    for key in keyList:
            
        if key=="def" and len(termDic[key])>0 :
            curLine = "description: \"" + termDic[key][0][0].upper() + termDic[key][0][1:] +"\""
            schemaPieceList.append(curLine)

        elif key=="references" and len(termDic[key])>0:
            itemList = []
            for i in range(len(termDic[key])):
                if termDic[key][i]!="": 
                    curLine, newReferenceMap = get_references(termDic[key][i])
                    if curLine:
                        schemaPieceList.append(curLine)
                    if newReferenceMap:
                        newSourceMap[key] = newSourceMap[key].update(newReferenceMap)
            
        elif key=="id" and len(termDic[key])>0:       
            curLine = "psimiID: \"" + termDic[key][0] + "\""
            schemaPieceList.append(curLine)
            
        elif key=="parentClassName" and len(termDic[key])>0:
            itemList = []
            for i in range(len(termDic[key])):
                itemList.append( "dcs:" + termDic[key][i])
            curLine = "specializationOf: " +  ",".join(itemList)
            schemaPieceList.append(curLine)
            
    curLine = "descriptionUrl: \"http://psidev.info/groups/controlled-vocabularies\""
    schemaPieceList.append(curLine)
    
    return "\n".join(schemaPieceList), termDic['id'][0], dcid, newSourceMap


def main(argv):
    dbFile = argv[0]
    with open(dbFile, 'r') as fp:
        file = fp.read()
    # clip exists in dcs already. Substitute with ClipInteraction
    file = file.replace("name: clip\ndef", "name: clip interaction\ndef")
    fileTerms = file.split('\n\n')[1:]

    '''
    Parsing Steps:
    1. build the tree by the psi-mi number. A dictionary {psi-mi: node} is used 
    to access nodes as well.
    2. save all the tree nodes in the subtree of the three nodes into three set:
        id: MI:0001 name: interaction detection method
        id: MI:0190 name: interaction type
        id: MI:0444 name: database citation
    3. save the nodes in the three sets to the corresponding enumearation schema
    '''
    
    id2node = {}
    id2className = {}
    # build nodes and create the id2node dictionary at first iteration
    for termText in fileTerms:
        if not termText.startswith("[Term]"):
            continue
        # idString example: "MI:0000"
        idString = termText.split("\n")[1].split(" ")[1]
        className = get_class_name(termText.split("\n")[2].split(": ")[1])
        id2className[idString] = className
        id2node[idString] = Node(idString)

    # build the parent-child relation at the second iteration
    for termText in fileTerms:
        if not termText.startswith("[Term]"):
            continue
        termList = termText.split("\n")
        idString = termList[1].split(" ")[1]
        parentIdList = get_parent_id_list(termList[1:])
        for pId in parentIdList:
            id2node[pId].childList.append(id2node[idString])
            id2node[idString].parentList.append(id2node[pId])

    # get the idStrings for the three target set
    dfsCaller = GetTreeValues()
    interactionTypeIdSet = dfsCaller.get_subset_id(id2node["MI:0001"]) # root id: MI:0001 
    detectionMethodIdSet = dfsCaller.get_subset_id(id2node["MI:0190"])# root id: MI:0190
    interactionSourceIdset = dfsCaller.get_subset_id(id2node["MI:0444"]) # root id: MI:0444

    # delete root node value from the set
    interactionTypeIdSet.remove("MI:0001")
    detectionMethodIdSet.remove("MI:0190")
    interactionSourceIdset.remove("MI:0444")

    setList = [interactionTypeIdSet, detectionMethodIdSet,interactionSourceIdset]
    print("The schema amount of each Enum: interactionType, detectionMethod,interactionSource are ")
    print([len(s) for s in setList])

    schemaList = []
    psimi2dcid = []
    newSourceMap = {"references":{}}
    for termText in fileTerms:
        if not termText.startswith("[Term]"):
            continue
        term = termText.split("\n")[1:]
        schemaRes = get_schema_from_text(term,id2node,newSourceMap,id2className,
                                      interactionTypeIdSet,detectionMethodIdSet,interactionSourceIdset)
        if schemaRes:
            schema, psimi, dcid, newSourceMap  = schemaRes
            schemaList.append(schema)
            psimi2dcid.append(psimi+': ' + dcid)
    schemaEnumText = "\n\n".join(schemaList)
    schema = "# This schema file is generated by parseEBI.py. Please don't edit.\n"
    schemaEnumText = schema + schemaEnumText

    # dev browser imported name: BioOntologySchema
    with open('BioOntologySchemaEnum.mcf','w') as fp:
        fp.write(schemaEnumText)
    with open('psimi2dcid.txt','w') as fp:
        fp.write("\n".join(psimi2dcid))
        
    writeList = []
    for sourceType in newSourceMap:
        if not newSourceMap[sourceType]: continue
        writeList.append(sourceType)
        for source in newSourceMap[sourceType]:
            line = source + ": " + newSourceMap[sourceType][source]
            writeList.append(sourceType)
        writeList.append("\n")
    if writeList:
        with open('BioEBINewSource.txt','w') as fp:
            fp.write("\n".join(writeList))


if __name__ == "__main__":
    main(sys.argv[1:])

