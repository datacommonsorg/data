# Template for converting UN DSD file with column metadata
# to PVMap for statvar processor.
# The pvmap will have columns to generate statvar constraint
# propoerties with names.
# The pvmap will also have columns to generate schema MCF with a tMCF.
{
    'key':
        '{CONCEPT}',
    'UnCodeProp':
        'UnConceptCode',
    'UnCode':
        '"{CONCEPT}"',
    'ConceptProp':
        'UnConceptProperty',
    'ConstraintProp':
        '{PROPERTY}',
    'ConstraintPropType':
        'Property',
    'ConstraintPropEnum':
        'str(ConstraintProp[0].upper() + ConstraintProp[1:]+"Enum")',
    'ConceptNameProp':
        'PropertyName_{CONCEPT}',
    'ConceptName':
        '"{NAME_EN}"',
    'DescriptionProp':
        'ValueDesc_{CONCEPT}',
    'ConceptDescription':
        'quote(anyascii(DESCRIPTION))',
    # Initialize ValueName for specific codes for a concept to empty string
    'CodeNameProp':
        'ValueName_{CONCEPT}',
    'DefaultName':
        '""',
    # End of line prop:value when description is empty.
    '#End':
        'End',
    'Dummy':
        '.',
}
