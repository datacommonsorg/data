"""This script parse GO information
from hmdb_p.xml file"""
from xml.etree import ElementTree
import sys
import pandas as pd


def get_protein_attribute(protein_element):
    """Get accession and gGO information
    from protein element in xml file"""
    attribute_dict = {
        "accession": '{http://www.hmdb.ca}accession',
        "go_classification": '{http://www.hmdb.ca}go_classifications'
    }
    protein_accession = protein_element.find(\
                            attribute_dict["accession"]).text
    go_classification = protein_element.find(
        attribute_dict["go_classification"])
    go_classes = list(go_classification)
    parsed_go_classes = []
    for go_class in go_classes:
        parsed_go_class = get_go_attribute(go_class)
        parsed_go_classes.append(parsed_go_class)
    df_go = pd.DataFrame(parsed_go_classes)
    df_go["accession"] = protein_accession
    return df_go


def get_go_attribute(go_class):
    """Get GO category, description, and id
    from GO classification"""
    go_class = list(go_class)
    return {
        "go_category": go_class[0].text,
        "go_description": go_class[1].text,
        "go_id": go_class[2].text
    }


def main():
    """Main function"""
    hmdb_xml = sys.argv[1]
    #Read disease ontology .wol file
    tree = ElementTree.parse(hmdb_xml)
    # Get file root
    root = tree.getroot()
    # Find owl classes elements
    all_proteins = root.findall('{http://www.hmdb.ca}protein')
    df_go_list = []
    for prot in all_proteins:
        df_go_list.append(get_protein_attribute(prot))
    df_go = pd.concat(df_go_list)
    df_go.to_csv("hmdb_go.csv", index=False)


if __name__ == "__main__":
    main()
