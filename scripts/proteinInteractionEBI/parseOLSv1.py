#!/usr/bin/env python
# coding: utf-8

# In[1]:


import collections
#todo: divide the terms into ohters, interactionType, detectionMethod, Interaction Source


# In[65]:


def getClassName(astring):
    """
    Take a space delimited string, return a class name such as ThisIsAnUnusualName 
    """
    return astring.title().replace(" ","")
    
def getPropertyName(astring):
    """
    Take a space delimited string, return a property name such as thisIsAnUnusualName 
    """
    className = astring.title().replace(" ","")
    return className[0].lower()+className[1:]


# In[2]:


"""
June 10, 2020
Parsing Steps:
1. build the tree by the psi-mi number. A dictionary {psi-mi: node} is used 
to access nodes as well.
2. save all the tree nodes in the subtree of the three nodes into three set:
    id: MI:0001 name: interaction detection method
    id: MI:0190 name: interaction type
    id: MI:0444 name: database citation
3. save the nodes in the three sets to the corresponding enumearation schema
"""


# In[13]:


with open('mi.owl','r') as fp:
    file = fp.read()


# In[4]:


#get the file instruction and save into a dictionary
fileHeader = file.split('\n\n')[0]


# In[4]:


fileHeaderDic = collections.defaultdict(list)
pairs = fileHeader.split("\n")
for pair in pairs:
    pairList = pair.split(":")
    key = pairList[0]
    value = ":".join(pairList[1:])
    fileHeaderDic[key].append(value)


# In[14]:


fileTerms = file.split('\n\n')[1:]


# In[5]:


fileHeaderDic.keys()


# In[6]:


#In this version synonym is saved as a string and is not linked to each synonym type.


# In[7]:


#Three subsets are saved to enumeration schema 
schemaPiece = """Node: dcid:BiomedicalOntologySubsetEnum
typeOf: schema:Enumeration
name: "BiomedicalOntologySubsetEnum"
description: \"The subset enumeration in biomedical ontologies\""""
schemaEnum = [schemaPiece]

for subsetPair in fileHeaderDic['subsetdef']:
    subsetList = subsetPair.split()  
    dcid = subsetList[0]
    description = ' '.join(subsetList[1:])
    schemaPiece = 'Node: dcid:' + dcid + '\n'+'typeOf: dcs:BiomedicalOntologySubsetEnum\nname: “'+dcid+'”\ndescription: '+description
    schemaEnum.append(schemaPiece)
schemaEnumText = '\n\n'.join(schemaEnum)


# In[68]:


class Node():
    def __init__(self, value):
        self.value = value
        self.parentList = []
        # one node can have multiple child nodes
        self.childList = []
def getParentIdList(termList):
    """
    Takes a list with each item containing the information, return a list of idString of parent node. 
    Example:
    term = ['id: MI:0000',
     'name: molecular interaction',
     'def: "Controlled vocabularies originally created for protein protein interactions, extended to other molecules interactions." [PMID:14755292]',
     'subset: Drugable',
     'subset: PSI-MI_slim']
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

class GetTreeValues():
    
    def __init__(self):
        self.nodeValuesSet = set()

    def getSubsetId(self, node):
        """
        Take the idString of as the root node value, return all the tree nodes value as a set.
        """
        # reset return set to empty
        self.nodeValuesSet = set()
        # run a DFS on the tree
        self.dfs(node)
        return self.nodeValuesSet

    def dfs(self, node):
        """
        Take a tree node, do tree traversal recursively 
        """
        if not node: return
        self.nodeValuesSet.add(node.value)
        for child in node.childList:
            self.dfs(child)
        
    
id2node = {}
id2className = {}
# build nodes and create the id2node dictionary at first iteration
for termText in fileTerms:
    if not termText.startswith("[Term]"):
        continue
    # idString example: "MI:0000"
    idString = termText.split("\n")[1].split(" ")[1]
    className = getClassName(termText.split("\n")[2].split(": ")[1])
    id2className[idString] = className
    id2node[idString] = Node(idString)


# In[106]:


# build the parent-child relation at the second iteration
for termText in fileTerms:
    if not termText.startswith("[Term]"):
        continue
    termList = termText.split("\n")
    idString = termList[1].split(" ")[1]
    parentIdList = getParentIdList(termList[1:])
    for pId in parentIdList:
        id2node[pId].childList.append(id2node[idString])
        id2node[idString].parentList.append(id2node[pId])


# In[107]:


# get the idStrings for the three target set
dfsCaller = GetTreeValues()
interactionTypeIdSet = dfsCaller.getSubsetId(id2node["MI:0001"]) # root id: MI:0001 
detectionMethodIdSet = dfsCaller.getSubsetId(id2node["MI:0190"])# root id: MI:0190
interactionSourceIdset = dfsCaller.getSubsetId(id2node["MI:0444"]) # root id: MI:0444


# In[108]:


setList = [interactionTypeIdSet, detectionMethodIdSet,interactionSourceIdset]
print ([len(s) for s in setList])


# In[123]:


def getSchemaFromText(term, id2node):
    
    """
    Takes a list with each item containing the information, return a data schema. 
    Example:
    term = ['id: MI:0000',
     'name: molecular interaction',
     'def: "Controlled vocabularies originally created for protein protein interactions, extended to other molecules interactions." [PMID:14755292]',
     'subset: Drugable',
     'subset: PSI-MI_slim']
    """
    termDic = collections.defaultdict(list)
    for line in term:
        lineList = line.split(": ")
        key = lineList[0]
        value = ": ".join(lineList[1:])
        termDic[key].append(value)
    try:
        defLong = termDic['def'][0]
    except:
        print("No def attribute",term)
    try:
        idStart = defLong.rfind('[')
        description = defLong[1:idStart-1-2]
        termDic['def'] = [description]
        IDList = defLong[idStart+1:-1].split(", ")
        termDic['publications']= IDList
        
    except:
        print(defLong)
    
    schemaPieceList = []
    keyList = ["id", "def","publications","subset","synonym","is_obsolete","parentClassName"]
    curLine = "Node: dcid:bio/" + id2className[termDic['id'][0]]
    schemaPieceList.append(curLine)
    
    idString = termDic['id'][0]
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
    curLine = "name: \"" + id2className[idString] + "\""
    schemaPieceList.append(curLine)

    '''
    termDic:
    id:  ['MI:0001']
    name:  ['interaction detection method']
    def:  ['Method to determine the interaction']
    subset:  ['Drugable', 'PSI-MI_slim']
    synonym:  ['"interaction detect" EXACT PSI-MI-short []']
    relationship:  ['part_of MI:0000 ! molecular interaction']
    publications:  ['PMID:14755292']
    parentClassName:  ['MolecularInteraction']
    '''

    for key in keyList:
            
        if key=="def" and key in termDic:

            curLine = "description: \"" + termDic[key][0][0].upper() + termDic[key][0][1:] +"\""
            schemaPieceList.append(curLine)

        elif key=="publications" and key in termDic:
            itemList = []
            for i in range(len(termDic[key])):
                itemList.append( "\"" + termDic[key][i] + "\"")
            curLine = "publications: " +  ",".join(itemList)
            schemaPieceList.append(curLine)
            
        elif key=="id" and key in termDic:       
            curLine = "psimi: \"" + termDic[key][0] + "\""
            schemaPieceList.append(curLine)
            
        elif key=="subset" and key in termDic:
            itemList = []
            for i in range(len(termDic[key])):
                itemList.append(termDic[key][i])
            curLine = "subsetOf: dcid:"  + ",".join(itemList)
            schemaPieceList.append(curLine)
            
        elif key=="synonym" and key in termDic:
            itemList = []
            for i in range(len(termDic[key])):
                itemList.append("\"" + termDic[key][i] + "\"" )
            curLine = "alias: " + ",".join(itemList)
            schemaPieceList.append(curLine)
                
        elif key=="is_obsolete" and key in termDic:
            itemList = []
            for i in range(len(termDic[key])):
                itemList.append( termDic[key][i]  )
            curLine = "isObsolete: " + ",".join(itemList)
            schemaPieceList.append(curLine)
            
        elif key=="parentClassName" and key in termDic:
            itemList = []
            for i in range(len(termDic[key])):
                itemList.append( "dcid:bio/" + termDic[key][i])
            curLine = "specializationOf: " +  ",".join(itemList)
            schemaPieceList.append(curLine)

    return "\n".join(schemaPieceList)


# In[124]:


schemaList = []
schema = '''Node: dcid:BiomedicalOntologySubsetEnum\ntypeOf: schema:Enumeration\nname: "BiomedicalOntologySubsetEnum"\ndescription: "The subset enumeration in biomedical ontologies"\n\nNode: dcid:Drugable\ntypeOf: schema:BiomedicalOntologySubsetEnum\nname: "Drugable"\ndescription: "Drugable Genome Project"\n\nNode: dcid:PSI-MI_slim\ntypeOf: schema:BiomedicalOntologySubsetEnum\nname: "PSI-MI_slim"\ndescription: "Subset of PSI-MI"\n\nNode: dcid:PSI-MOD_slim\ntypeOf: schema:BiomedicalOntologySubsetEnum\nname: "PSI-MOD_slim"\ndescription: "subset of protein modifications"\n\nNode: dcid:InteractionTypeEnum\ntypeOf: schema:Enumeration\nname: "InteractionTypeEnum"\ndescription: "The interaction type enumeration in biomedical ontologies"\n\nNode: dcid:InteractionDetectionMethodEnum\ntypeOf: schema:Enumeration\nname: "InteractionDetectionMethodEnum"\ndescription: "The detection method enumeration in biomedical ontologies"\n\nNode: dcid:InteractionSourceEnum\ntypeOf: schema:Enumeration\nname: "InteractionSourceEnum"\ndescription: "The interaction source database enumeration in biomedical ontologies"'''
# count = 0
schemaList.append(schema)
for termText in fileTerms:
    if not termText.startswith("[Term]"):
        continue
    term = termText.split("\n")[1:]
    schema = getSchemaFromText(term, id2node)
    if schema:
        schemaList.append(schema)
#     count+=1
#     if count>5:
#         break
schemaEnumText = "\n\n".join(schemaList)
with open('BioOntologyEnumSchema.mcf','w') as fp:
    fp.write(schemaEnumText)


# In[ ]:




