"""generate the mcf for StatisticalVariables"""

def generate_sv():
    MedicalIncident_TEMPLATE = ('Node: dcid:{countType}_MedicalConditionIncident'
                                '_COVID_19_{SVname}\n'
                                'typeOf: dcs:StatisticalVariable\n'
                                'populationType: dcs:MedicalConditionIncident\n'
                                'incidentType: dcs:COVID_19\n'
                                'measuredProperty: dcs:{countType}\n'
                                'statType: dcs:measuredValue\n'
                                'medicalStatus: dcs:{SVname}\n\n')

    medical_incidents = ['HospitalizedsWithSymptoms', 'IntensiveCare', \
        'Hospitalized', 'PeopleInHomeIsolation', 'ActiveCase', \
        'IncrementalActiveCase', 'CumulativeRecovered', 'CumulativeDeath',\
        'CumulativePositiveCase', 'IncrementalPositiveCase']

    with open('./dpc-covid19-ita_StatisticalVariable.mcf', 'w') as f_out:
        for sv_full in medical_incidents:
            if "Cumulative" in sv_full:
                count_type = "cumulativeCount"
                statvar = sv_full.replace("Cumulative", "")
            elif "Incremental" in sv_full:
                count_type = "incrementalCount"
                statvar = sv_full
            else:
                count_type = "count"
                statvar = sv_full
            f_out.write(MedicalIncident_TEMPLATE.format_map({
                'countType':count_type, 'SVname':statvar}))

        tests_performed = ('Node: dcid:cumulativeCount_MedicalTest_COVID_19\n'
                           'typeOf: dcs:StatisticalVariable\n'
                           'populationType: dcs:MedicaltTest\n'
                           'incidentType: dcs:COVID_19\n'
                           'measuredProperty: dcs:cumulativeCount\n'
                           'statType: dcs:measuredValue\n\n')
        tested_people = ('Node: dcid:cumulativeCount_Person_COVID_19_Tested\n'
                         'typeOf: dcs:StatisticalVariable\n'
                         'populationType: dcs:Person\n'
                         'incidentType: dcs:COVID_19\n'
                         'measuredProperty: dcs:cumulativeCount\n'
                         'medicalStatus: dcs:Tested\n'
                         'statType: dcs:measuredValue\n\n')
        f_out.write(tests_performed)
        f_out.write(tested_people)


if __name__ == "__main__":
    generate_sv()
