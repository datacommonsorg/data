
def generate_SV():
    """generate the mcf for StatisticalVariables"""
    MedicalIncident_TEMPLATE = 'Node: dcid:COVID19_Italy_{SVFullName}\n' +\
                   'typeOf: dcs:StatisticalVariable\n' +\
                   'populationType: dcs:MedicalConditionIncident\n' +\
                   'incidentType: dcs:COVID_19\n' +\
                   'measuredProperty: dcs:{countType}\n' +\
                   'statType: dcs:measuredValue\n' +\
                   'medicalStatus: dcs:{SVname}\n\n'

    medicalIncidents = ['HospitalizedsWithSymptoms', 'IntensiveCare', \
        'Hospitalized', 'PeopleInHomeIsolation', 'ActiveCase', \
        'IncrementalActiveCase', 'CumulativeRecovered', 'CumulativeDeath',\
        'CumulativePositiveCase', 'IncrementalPositiveCase']
    
    with open('./dpc-covid19-ita_StatisticalVariable.mcf', 'w') as f_out:
        for svFull in medicalIncidents:
            if "Cumulative" in svFull:
                countType = "cumulativeCount"
                sv = svFull.replace("Cumulative","")
            elif "Incremental" in svFull:
                countType = "incrementalCount"
                sv = svFull
            else:
                countType = "count"
                sv = svFull
            f_out.write(MedicalIncident_TEMPLATE.format_map({'SVFullName': svFull, \
                'countType': countType, 'SVname':sv}))
        
        testsPerformed = 'Node: dcid:COVID19_Italy_CumulativeTestsPerformed\n' +\
                        'typeOf: dcs:StatisticalVariable\n' +\
                        'populationType: dcs:MedicaltTest\n' +\
                        'incidentType: dcs:COVID_19\n' +\
                        'measuredProperty: dcs:cumulativeCount\n' +\
                        'statType: dcs:measuredValue\n\n'
        testedPeople = 'Node: dcid:COVID19_Italy_CumulativeTestedPeople\n' +\
                       'typeOf: dcs:StatisticalVariable\n' +\
                       'populationType: dcs:Person\n' +\
                       'incidentType: dcs:COVID_19\n' +\
                       'measuredProperty: dcs:cumulativeCount\n' +\
                       'medicalStatus: dcs:Tested\n' +\
                       'statType: dcs:measuredValue\n\n'
        f_out.write(testsPerformed)
        f_out.write(testedPeople)
        
        
if __name__ == "__main__":
  generate_SV()

