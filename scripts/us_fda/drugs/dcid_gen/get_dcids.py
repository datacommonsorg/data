def get_id_from_chembl_file(line):
    """Helper method to extract chembl id from line of chembl_ids.out file.
    """
    molec = line.split(' ')[0]
    chembl_id = molec.replace('chembl_molecule:', '').strip()
    return chembl_id


def get_label_from_chembl_file(line):
    """Helper method to extract label from line of chembl_ids.out file.
    """
    label = re.findall(r'(?<=").*?(?=")', line)
    if len(label) != 1:
        print('Unexpected number of labels in ChemblFile: ' + str(label))
    return label[0]


def get_chembl_dict_from_file():
    """Loads a dictionary of drug names to chembl ids from the chembl_ids.out
    file using helper functions. Returns the dictionary.
    """
    # load chembl_ids from chembl file
    chembl_file_drugs = {}
    with open('raw_data/chembl_ids.out') as chembl_id_out:
        for line in chembl_id_out:
            if 'rdfs:label "CHEMBL' not in line:
                label = get_label_from_chembl_file(line)
                chembl_id = get_id_from_chembl_file(line)

                if label in chembl_file_drugs and chembl_id not in chembl_file_drugs[
                        label]:
                    chembl_file_drugs[label].append(chembl_id)
                else:
                    chembl_file_drugs[label] = [chembl_id]
    return chembl_file_drugs


# FUNCTIONS: match drugName to chembl_id
def get_chembl_id_through_api(search):
    """Uses the chembl python api to search for a chembl ID based on the
    drug name.
    """
    search = search.strip()
    chembl_id = None
    for molec in molecule.search(search):
        #print(molec)
        for molec_synonym in molec['molecule_synonyms']:
            if molec_synonym['molecule_synonym'].lower() == search.lower():
                chembl_id = molec['molecule_chembl_id']
                #print('found: ' + search)
                return chembl_id
    return chembl_id


def get_ref_name(synonyms):
    """Returns a suitable reference name for a drug when the chembl ID cannot
    be found. This reference name is used in dcids and therefore must not contain
    special characters.
    """
    ref_name = synonyms.replace(' , ', '_')
    ref_name = ref_name.replace(', ', '_')
    ref_name = ref_name.replace(',', '_')
    ref_name = ref_name.replace('/ ', '_')
    ref_name = ref_name.replace('/', '-')
    ref_name = ref_name.replace('- ', '-')
    ref_name = ref_name.replace(' IN PLASTIC CONTAINER', '').strip()
    ref_name = ref_name.replace(' IN WATER', '').strip()

    ref_name = ref_name.replace(' ', '_')
    ref_name = ref_name.replace('%', 'PRCT')

    ref_name = re.sub("[^0-9a-zA-Z_-]+", "", ref_name).title()

    if len(ref_name) > 136:
        print('WARNING ref_name too long: ' + ref_name)
    #print(ref_name)

    return ref_name


def get_drug_ref_name(synonyms, active_ingred, chembl_file_drugs):
    """Returns list of chembl IDs or drug references that will be used in the
    drug node's dcid.
    """
    check_list = [' AND ', ';', ' IN ']
    if any(check in synonyms for check in check_list):
        return get_ref_name(synonyms)

    synonyms = synonyms.replace('\'', '')
    synonyms = synonyms.replace('.', '')
    search_name = re.split(r'[^a-zA-Z\s-]', synonyms)[0]

    chembl_id = None
    if not search_name:
        return get_ref_name(active_ingred)
    if search_name in chembl_file_drugs:
        chembl_id = chembl_file_drugs[search_name]
    else:
        try:
            chembl_id = func_timeout(10,
                                     get_chembl_id_through_api,
                                     args=(search_name,))
        except FunctionTimedOut:
            chembl_id = None
        except:
            chembl_id = None

    if not chembl_id:
        return get_ref_name(synonyms)

    return chembl_id
