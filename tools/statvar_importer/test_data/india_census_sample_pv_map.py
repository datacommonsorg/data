# Property-Value map for India census data
{
    # File level Properties.
    "C-2  MARITAL STATUS BY AGE AND SEX": {
        "observationDate": "2011",
        "measurementMethod": "dcs:IndiaCensus2011",
    },
    # Values in Column:E
    "Rural": {
        "placeOfResidenceClassification": "dcs:Rural"
    },
    "Urban": {
        "placeOfResidenceClassification": "dcs:Urban"
    },
    "Rural/": {
        "placeOfResidenceClassification": ""
    },
    "Urban/": {
        "placeOfResidenceClassification": ""
    },

    # Values in Column:F: Age-group
    "Age-group": {
        # Parse age range, example: "10-14" into "age": "[10 14 Years]"
        "age": "[{@StartAge} {@EndAge} Years]",
        "#Regex": "(?P<StartAge>[0-9]+)-(?P<EndAge>[0-9]+)",
    },
    "All ages": {
        "age": ""
    },  # No age bracket required
    "Age not stated": {
        "age": "dcs:AgeNotStated"
    },
    "Less than 18": {
        "age": "[- 18 Years]"
    },
    "Less than 21": {
        "age": "[- 21 Years]"
    },
    "80+": {
        "age": "[80 - Years]"
    },

    # Column:G-V: Persons/Males/Females
    "Persons": {
        "populationType": "dcs:Person",
        "value": "@Number",
        "gender": "",
    },
    "Males": {
        "populationType": "dcs:Person",
        "gender": "dcs:Male",
        "value": "@Number",
    },
    "Females": {
        "populationType": "dcs:Person",
        "gender": "dcs:Female",
        "value": "@Number",
    },

    # Column headers for Marital status: columns:J-V
    # Columns:J-L
    "Never married": {
        "maritalStatus": "dcs:NeverMarried",
    },
    # Columns:M-O
    "Currently Married": {
        "maritalStatus": "dcs:NowMarried",
    },
    # Columns:P-R
    "Widowed": {
        "maritalStatus": "dcs:Widowed",
    },
    # Columns:S-U
    "Separated": {
        "maritalStatus": "dcs:Separated",
    },
    # Columns:V-X
    "Divorced": {
        "maritalStatus": "dcs:Divorced",
    },
    # Columns:V-X
    "Unspecified": {
        "maritalStatus": "dcs:CDC_MaritalStatusUnknownOrNotStated",
    },

    # Place: Country in Column:D
    # TODO: use lgdCode instead
    "INDIA": {
        "observationAbout": "dcid:country/IND"
    },
    "ANDAMAN & NICOBAR ISLANDS (35)": {
        "observationAbout": "dcid:wikidataId/Q40888"
    },
    "ANDHRA PRADESH (28)": {
        "observationAbout": "dcid:wikidataId/Q1159"
    },
    "ARUNACHAL PRADESH (12)": {
        "observationAbout": "dcid:wikidataId/Q1162"
    },
    "ASSAM (18)": {
        "observationAbout": "dcid:wikidataId/Q1164"
    },
    "BIHAR (10)": {
        "observationAbout": "dcid:wikidataId/Q1165"
    },
    "CHANDIGARH (04)": {
        "observationAbout": "dcid:wikidataId/Q43433"
    },
    "CHHATTISGARH (22)": {
        "observationAbout": "dcid:wikidataId/Q1168"
    },
    "DADRA & NAGAR HAVELI (26)": {
        "observationAbout": "dcid:wikidataId/Q46107"
    },
    "DAMAN & DIU (25)": {
        "observationAbout": "dcid:wikidataId/Q66710"
    },
    "GOA (30)": {
        "observationAbout": "dcid:wikidataId/Q1171"
    },
    "GUJARAT (24)": {
        "observationAbout": "dcid:wikidataId/Q1061"
    },
    "HARYANA (06)": {
        "observationAbout": "dcid:wikidataId/Q1174"
    },
    "HIMACHAL PRADESH (02)": {
        "observationAbout": "dcid:wikidataId/Q1177"
    },
    "JAMMU & KASHMIR (01)": {
        "observationAbout": "dcid:wikidataId/Q66278313"
    },
    "JHARKHAND (20)": {
        "observationAbout": "dcid:wikidataId/Q1184"
    },
    "KARNATAKA (29)": {
        "observationAbout": "dcid:wikidataId/Q1185"
    },
    "KERALA (32)": {
        "observationAbout": "dcid:wikidataId/Q1186"
    },
    "LAKSHADWEEP (31)": {
        "observationAbout": "dcid:wikidataId/Q26927"
    },
    "MADHYA PRADESH (23)": {
        "observationAbout": "dcid:wikidataId/Q1188"
    },
    "MAHARASHTRA (27)": {
        "observationAbout": "dcid:wikidataId/Q1191"
    },
    "MANIPUR (14)": {
        "observationAbout": "dcid:wikidataId/Q1193"
    },
    "MEGHALAYA (17)": {
        "observationAbout": "dcid:wikidataId/Q1195"
    },
    "MIZORAM (15)": {
        "observationAbout": "dcid:wikidataId/Q1502"
    },
    "NAGALAND (13)": {
        "observationAbout": "dcid:wikidataId/Q1599"
    },
    "NCT OF DELHI (07)": {
        "observationAbout": "dcid:wikidataId/Q1353"
    },
    "ODISHA (21)": {
        "observationAbout": "dcid:wikidataId/Q22048"
    },
    "PUDUCHERRY (34)": {
        "observationAbout": "dcid:wikidataId/Q66743"
    },
    "PUNJAB (03)": {
        "observationAbout": "dcid:wikidataId/Q22424"
    },
    "RAJASTHAN (08)": {
        "observationAbout": "dcid:wikidataId/Q1437"
    },
    "SIKKIM (11)": {
        "observationAbout": "dcid:wikidataId/Q1505"
    },
    "TAMIL NADU (33)": {
        "observationAbout": "dcid:wikidataId/Q1445"
    },
    "TRIPURA (16)": {
        "observationAbout": "dcid:wikidataId/Q1363"
    },
    "UTTARAKHAND (05)": {
        "observationAbout": "dcid:wikidataId/Q1499"
    },
    "UTTAR PRADESH (09)": {
        "observationAbout": "dcid:wikidataId/Q1498"
    },
    "WEST BENGAL (19)": {
        "observationAbout": "dcid:wikidataId/Q1356"
    },
}
