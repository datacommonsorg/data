#!/usr/bin/env python
# coding: utf-8

import collections
import math
import re
import sys


def get_references(term):
    """Convert reference string to the corresponding reference property schema
    
    Args:
        term: a string with the format "source:idNum"
    
    Returns:
        a tuple: (propertyLine,newSourceMap). propertyLine is the reference 
        property in schema, and newSourceMap is the dictionary of with source
        name as the key and the identifier as the value, if new source exists.
        For example:
        
        ("imexID: 1007323", {aNewSource:100100})
    """
    source = term.split(":")[0]
    idNum = ":".join(term.split(":")[1:])
    newSourceMap = {}
    if source == "pubmed":
        propertyLine = "pubMedID: " + "\"" + idNum +"\""
    elif source == "imex":
        propertyLine = "imexID: " + "\"" + idNum +"\""
    elif source == "mint":
        propertyLine =  "mintID: " + "\"" + idNum +"\""
    elif source == "doi":
        propertyLine =  "digitalObjectID: " + "\"" + idNum +"\""
    elif source == "rcsb pdb":
        propertyLine =  "rcsbPDBID: " + "\"" + idNum +"\""
    else:
        newReference[source] = idNum
        newSourceMap = None
    return (propertyLine, newSourceMap) 
    
def get_identifier(term):
    """Convert identifier string to the corresponding identifier property schema
    
    Args:
        term: a string with the format "source:idNum"
    
    Returns:
        a tuple: (propertyLine,newSourceMap). propertyLine is the identifier 
        property in schema, and newSourceMap is the dictionary of with source
        name as the key and the identifier as the value, if new source exists.
        For example:
        
        ("imexID: 1007323", "{aNewSource:100100}")
    """
    source = term.split(":")[0]
    idNum = ":".join(term.split(":")[1:])
    newSourceMap = {}
    if source == "intact":
        propertyLine = "intActID: " + "\"" + idNum +"\""
    elif source == "mint":
        propertyLine = "mintID: " + "\"" + idNum +"\""
    elif source == "imex":
        propertyLine = "imexID: " + "\"" + idNum +"\""
    elif source == "emdb":
        propertyLine = "electronMicroscopyDataBankID: " + "\"" + idNum +"\""   
    elif source == "wwpdb":
        propertyLine = "worldWideProteinDataBankID: " + "\"" + idNum +"\""
    elif source == "rcsb pdb":
        propertyLine = "rcsbPDBID: " + "\"" + idNum +"\""
    elif source == "psi-mi":
        propertyLine = "psimiID: " + "\"" + idNum[1:-1] +"\""
    elif source == "reactome":
        propertyLine = "reactomePathwayID: " + "\"" + idNum +"\""
    elif source == "pdbe":
        propertyLine = "proteinDataBankInEuropeID: "  + "\"" + idNum +"\""
    else:
        newSourceMap[source] = idNum
        propertyLine = None
    return (propertyLine, newSourceMap)
    
def get_confidence(term):
    """Convert confidence string to the corresponding confidence property schema

    Args:
        term: a string with the format "source:idNum"

    Returns:
        a tuple: (propertyLine,newSourceMap). propertyLine is the identifier 
        property in schema, and newSourceMap is the dictionary of with source
        name as the key and the identifier as the value, if new source exists.
        For example:
        
        ("[13 dcs:AuthorScore]", {aNewSource:10})
    """
    source = term.split(":")[0]
    idNum = ":".join(term.split(":")[1:])
    newSourceMap = {}
    if source == "author score":
        if idNum.split(" ")[0] == "Below":
            propertyLine =  "[- "+ idNum.split(" ")[1] + " dcs:AuthorScore" +  "]"
        elif idNum.split(" ")[0] == "Above":
            propertyLine =  "["+ idNum.split(" ")[1] + " - dcs:AuthorScore" +  "]"
        for part in idNum.split("."):
            if not part.isnumeric():
                # if author score is "++++"
                propertyLine =  "["+ str(len(idNum)) + " dcs:AuthorScore" +  "]"
                
        
        propertyLine =  "["+ idNum + " dcs:AuthorScore" +  "]"
    elif source == "intact-miscore":
        propertyLine =  "["+ idNum + " dcs:IntactMiScore" +  "]"
    else:
        newSourceMap[source] = idNum
        propertyLine =  None
        
    return (propertyLine, newSourceMap)


def get_protein_dcid(mintAliases):
    """Takes a string from the mint database, return the dcid of the protein.
    Args: 
        mintAliases: a line contains the aliases of the protein. The capitalized "display_long" name is the
    dcid of the participant protein.
    """
    if len(mintAliases)>1:
        return mintAliases.split("|")[0].split(":")[1].split('(')[0].upper()
    else:
        # for a self-interacting protein, one of the protein name is empty, denoted by "-" 
        return None


def check_uniprot(alias):
    """
    Return True if the protein has UniProt identifier
    """ 
    return len(alias)==1 or alias.split(":")[0] == "uniprotkb"


def check_dcid(alias):
    """
    if alias == '-': return 1
    elif it contains the "display_long" name, which is the protein name in UniProt, and if it
        has the right format (contains only number, char, "_"), and it has two parts separated 
        by "_", return 2
    else return 0
    """
    if len(alias) == 1:
        return 1
    aliasList = alias.split("|")
    aliasDic = {}
    for ali in aliasList:
        key = ali.split("(")[1][:-1]
        value = ali.split("(")[0].split(":")[1]
        aliasDic[key] = value
    if "display_long" in aliasDic:
        dcid = aliasDic["display_long"]
        if re.search("[\W]+", dcid)!=None or len(dcid.split("_"))!=2:
            return 0    
    else:
        return 2
        


def get_property_content(content, prefix):
    """Add the prefix to each object in the content and return the concatenated string with "," separator.
    Args:
        content: the list containing property objects
        prefix: the prefix before dcid, such as "dcs:"
    Returns:
        objects separated by comma. For example:
        
        "dcs:bio/UniProt_CWH41_YEAST,dcs:bio/UniProt_RPN3_YEAST"
    """
    if not content:
        return None
    itemList = []
    for obj in content:
        itemList.append(prefix + obj)

    return ",".join(itemList)

def get_cur_line(keyName, valueList, prefix):
    """Return the line of property schema from objects, property name and prefix
    Args:
        keyName: property name
        valueList: object list
        prefix: prefix for the objects
    Return:
        The property string line in a schema. For example:
        
        "interactingProtein: dcs:bio/UniProt_CWH41_YEAST,dcs:bio/UniProt_RPN3_YEAST"
    """
    propertyContent = get_property_content(valueList, prefix)
    if not propertyContent: return None
    curLine = keyName + ": " + propertyContent 
    return curLine


def get_schema_from_text(term, newSourceMap, psimi2dcid):
    
    """
    Args: 
        term: a list with each item containing the information
        newSourceMap: a map contaning new source information. For example:
        
        {"refereces":{},"identifier":{},"confidence":{"newConfidence":"AA10010"}}
        
    Returns:
        a string, which is a data schema
        newSourceMap: and a map with new reference,identifier and confidence sources. For example:
        
        ['''Node: dcid:bio/MT1A_HUMAN_P53_HUMAN
        typeOf: ProteinProteinInteraction
        name: "MT1A_HUMAN_P53_HUMAN"
        interactingProtein: dcs:bio/UniProt_MT1A_HUMAN,dcs:bio/UniProt_P53_HUMAN
        interactionDetectionMethod: dcs:AntiBaitCoimmunoprecipitation
        interactionType: dcs:PhysicalAssociation
        interactionSource: dcs:Mint
        intActID: "EBI-8045171"
        mintID: "MINT-1781444"
        imexID: "IM-11231-3"
        confidenceScore: [0.54 dcs:IntactMiScore]
        pubMedID: "16442532"
        imexID: "IM-11231"
        mintID: "MINT-5218281"''',{"references":{},"identifier":{},"confidence":{"newConfidence":"AA10010"}}]
        
    """
    termDic = collections.defaultdict(list)
    protein = get_protein_dcid(term[4])
    if protein:
        termDic['interactingProtein'].append(protein)
    protein = get_protein_dcid(term[5])
    if protein:
        termDic['interactingProtein'].append(protein)
    detectionMethod = psimi2dcid[term[6].split(":\"")[1].split("(")[0][:-1]]
    termDic['interactionDetectionMethod'].append(detectionMethod)
    termDic['references'] = term[8].split("|")
    interactionType = psimi2dcid[term[11].split(":\"")[1].split("(")[0][:-1]]
    termDic['interactionType'].append(interactionType)
    interactionSource =  psimi2dcid[term[12].split(":\"")[1].split("(")[0][:-1]]
    termDic['interactionSource'].append(interactionSource)
    termDic['identifier'] = term[13].split("|")
    confidence = term[14]
    if confidence!= "-":
        termDic['confidence']=term[14].split("|")

    '''
    termDic example:
    interactingProtein:  ['RPN1_YEAST', 'RPN3_YEAST']
    interactionDetectionMethod:  ['TandemAffinityPurification']
    references:  ['pubmed:16554755', 'imex:IM-15332', 'mint:MINT-5218454']
    interactionType:  ['PhysicalAssociation']
    interactionSource:  ['Mint']
    identifier:  ['intact:EBI-6941860', 'mint:MINT-1984371', 'imex:IM-15332-8532']
    confidence:  ['intact-miscore:0.76']
    '''
    
    schemaPieceList = []
    keyList = ["interactingProtein", "interactionDetectionMethod","interactionType","interactionSource",
               "identifier", "confidence","references"]
    if len(termDic["interactingProtein"])>1:
        dcid = termDic["interactingProtein"][0] + "_" + termDic["interactingProtein"][1]
    else:
        dcid = termDic["interactingProtein"][0] + "_" + termDic["interactingProtein"][0]
    curLine = "Node: dcid:bio/" + dcid
    schemaPieceList.append(curLine)
    curLine = "typeOf: ProteinProteinInteraction"
    schemaPieceList.append(curLine)
    curLine = "name: " + "\"" + dcid + "\""
    schemaPieceList.append(curLine)

    for key in keyList:
        if key in set(["interactionDetectionMethod", "interactionType", "interactionSource"]):
            curLine = get_cur_line(key, termDic[key], "dcs:")
            if curLine:
                schemaPieceList.append(curLine)
            
        elif key=="interactingProtein" and termDic[key]:
            curLine = get_cur_line(key, termDic[key], "dcs:bio/UniProt_")
            if curLine:
                schemaPieceList.append(curLine)

        elif key=="references" and termDic[key]:
            for term in termDic[key]:
                if term:
                    curLine, newReferenceMap = get_references(term)
                    if curLine:
                        schemaPieceList.append(curLine)
                    if newReferenceMap:
                        newSourceMap[key] = newSourceMap[key].update(newReferenceMap)
                          
        elif key=="identifier" and termDic[key]:
            for term in termDic[key]:
                if term:                  
                    curLine, newIdentifierMap = get_identifier(term)
                    if curLine:
                        schemaPieceList.append(curLine)
                    if newIdentifierMap:
                        newSourceMap[key] = newSourceMap[key].update(newIdentifierMap)
   
        elif key=="confidence" and termDic[key]:       
            itemList = []
            for term in termDic[key]:
                if term: 
                    item, newConfidenceSource = get_confidence(term)
                    itemList.append(item)
            if itemList:
                curLine = "confidenceScore: " +  ",".join(itemList)        
                schemaPieceList.append(curLine)
            if newConfidenceSource:
                newSourceMap[key] = newSourceMap[key].update(newConfidenceSource)
                
    return "\n".join(schemaPieceList), newSourceMap


def main(argv):
    
    dbFile = argv[0]
    #schemaMCF = argv[1]
    psimi2dcidFile = argv[1]
    parts = int(argv[2])
    
    with open(dbFile, 'r') as fp:
        file = fp.read()
        
    # read the file which has paired PSI-MI and DCID. This file was generated from EBI MI Ontology
    with open(psimi2dcidFile,'r') as fp:
        p2d = fp.read()


    lines = file.split('\n')


    psimi2dcid = {}
    p2d = [line.split(": ") for line in p2d.split("\n")]
    for line in p2d:
        psimi2dcid[line[0]] = line[1]

    newSourceMap = {"references":{}, "identifier":{}, "confidence":{}}
    schemaList = []
    wrongDcid = []
    failed = []
    noUniprot = []
    for line in lines:
        if len(line) == 0:
            continue    
        term = line.split('\t') 
        # check if the record has the correct UniProt Protein Name
        c1, c2 = check_dcid(term[4]), check_dcid(term[5])
        if c1==0 or c2==0:
            wrongDcid.append(line)
            continue

        # check if the record has Uniprot Identifier
        u1, u2 = check_uniprot(term[0]), check_uniprot(term[1])
        if not u1 or not u2:
            noUniprot.append(line)
            continue

        # catch the record when an unusual format occurs
        try:
            schema, newSourceMap = get_schema_from_text(term, newSourceMap, psimi2dcid)
        except:
            failed.append(line)
            continue

        if schema:
            schemaList.append(schema)


    # the number of records we didn't import
    fCount = 0
    for alist in [wrongDcid,noUniprot,failed]:
        fCount += len(alist)

    if parts == 1:
        schemaEnumText = "\n\n".join(schemaList)
        with open('BioMINTDataSchema.mcf','w') as fp:
            fp.write(schemaEnumText)
        
    else:
         # the whole schema is too large to upload to dev browser at once. Split into parts.
        count = 1
        step = math.ceil(len(schemaList)/float(parts))
        for i in range(0,len(schemaList), step):
            schemaEnumText = "\n\n".join(schemaList[i:i+step])   
            with open('BioMINTDataSchema_part'+str(count)+'.mcf','w') as fp:
                fp.write(schemaEnumText)
            count += 1
        
    if wrongDcid:
        with open('BioMINTFailedDcid.txt','w') as fp:
            fp.write("\n".join(wrongDcid))
    if noUniprot:
        with open('BioMINTNoUniprot.txt','w') as fp:
            fp.write("\n".join(noUniprot))
    if failed:
        with open('BioMINTParseFailed.txt','w') as fp:
            fp.write("\n".join(failed))

    writeList = []
    for sourceType in newSourceMap:
        if not newSourceMap[sourceType]: continue
        writeList.append(sourceType)
        for source in newSourceMap[sourceType]:
            line = source + ": " + newSourceMap[sourceType][source]
            writeList.append(sourceType)
        writeList.append("\n")
    if writeList:
        with open('BioMINTNewSource.txt','w') as fp:
            fp.write("\n".join(writeList)) 
    print(str(len(schemaList)) + " records have been successfully parsed to schema. " + str(fCount) + " records failed the parsing and have been saved to corresponding files.")


if __name__ == "__main__":
    main(sys.argv[1:])