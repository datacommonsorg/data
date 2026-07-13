# Template for converting UN codelist files to PVMap for statvar processor.
# The pvmap will have columns to generate statvar constraint property:values
# and names.
# The pvmap will also have columns to generate schema MCF with a tMCF.
{
    'key': '{CONCEPT}:{CODE}',
    'UnConceptProp': 'Property',
    'UnConcept': '"{CONCEPT}"',
    'UnCodeProp': 'UnCode',
    'UnCode': '"{CODE}"',
    'ConstraintProp': '{PROPERTY}',
    'ConstraintPropValue': 'to_dcid(NAMESPACE+"_"+CONCEPT+"-"+CODE)',
    'ConstraintPropType': 'TypeOf',
    'ConstraintPropEnum': (
        'str(ConstraintProp[0].upper() + ConstraintProp[1:]+"Enum")'
    ),
    'NameProp': 'ValueName_{CONCEPT}',
    'ConstraintValueName': '"{NAME_EN}"',
    'DescriptionProp': 'ValueDesc_{CONCEPT}',
    'ConstraintValueDescription': '{DESCRIPTION}',
    'End': 'End',
    'Dummy': '.',
}
