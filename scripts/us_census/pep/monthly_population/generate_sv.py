from statvar_dcid_generator import get_statvar_dcid



sv_list = [
    {
    "populationType" : "Person",
    "residentStatus": "InArmedForcesOverseas",
    #"armedForcesStatus": "InArmedForces",
    "statType": "measuredValue",
    "measuredProperty": "count"
    },
    {
    "populationType" : "Person",
    "residentStatus": "USResident",
    "statType": "measuredValue",
    "measuredProperty": "count"
    },
    {
    "populationType" : "Person",
    "residentStatus": "USResident__InArmedForcesOverseas",
    "statType": "measuredValue",
    "measuredProperty": "count"
    },
    {
    "populationType" : "Person",
    "armedForcesStatus": "Civilian",
    "statType": "measuredValue",
    "measuredProperty": "count"
    },
    {
    "populationType": "Person",
    "institutionalization": "USC_NonInstitutionalized",
    "armedForcesStatus" : "Civilian",
    "statType": "measuredValue",
    "measuredProperty": "count"
    },
    {
    "populationType": "Person",
    "residenceType": "Household",
    "statType": "measuredValue",
    "measuredProperty": "count"
    }
    ]
print("-----")
for property in sv_list:
    print(get_statvar_dcid(property))
print("-----")