import csv
import io
import urllib.request

output_columns = ['Date',
                  'CumulativeCount_MedicalTest_COVID_19',
                  'CumulativeCount_MedicalTest_COVID_19_Positive',
                  'CumulativeCount_MedicalTest_COVID_19_Negative',
                  'Count_MedicalTest_COVID_19_Pending',
                  'CumulativeCount_MedicalConditionIncident_COVID_19_PatientRecovered',
                  'CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased',
                  'Count_MedicalConditionIncident_COVID_19_PatientHospitalized',
                  'CumulativeCount_MedicalConditionIncident_COVID_19_PatientHospitalized',
                  'Count_MedicalConditionIncident_COVID_19_PatientInICU',
                  'CumulativeCount_MedicalConditionIncident_COVID_19_PatientInICU',
                  'Count_MedicalConditionIncident_COVID_19_PatientOnVentilator',
                  'CumulativeCount_MedicalConditionIncident_COVID_19_PatientOnVentilator'
                 ]
with open('COVIDTracking_US.csv', 'w', newline='') as f_out:
  writer = csv.DictWriter(f_out, fieldnames=output_columns, lineterminator='\n')
  with urllib.request.urlopen('https://covidtracking.com/api/v1/us/daily.csv') as response:
    reader = csv.DictReader(io.TextIOWrapper(response))

    writer.writeheader()
    for row_dict in reader:
      processed_dict = {
          'Date': '%s-%s-%s' % (row_dict['date'][:4], row_dict['date'][4:6], row_dict['date'][6:]),
          'CumulativeCount_MedicalTest_COVID_19': row_dict['totalTestResults'],
          'CumulativeCount_MedicalTest_COVID_19_Positive': row_dict['positive'],
          'CumulativeCount_MedicalTest_COVID_19_Negative': row_dict['negative'],
          'Count_MedicalTest_COVID_19_Pending': row_dict['pending'],
          'CumulativeCount_MedicalConditionIncident_COVID_19_PatientRecovered': row_dict['recovered'],
          'CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased': row_dict['death'],
          'Count_MedicalConditionIncident_COVID_19_PatientHospitalized': row_dict['hospitalizedCurrently'],
          'CumulativeCount_MedicalConditionIncident_COVID_19_PatientHospitalized': row_dict['hospitalizedCumulative'],
          'Count_MedicalConditionIncident_COVID_19_PatientInICU': row_dict['inIcuCurrently'],
          'CumulativeCount_MedicalConditionIncident_COVID_19_PatientInICU': row_dict['inIcuCumulative'],
          'Count_MedicalConditionIncident_COVID_19_PatientOnVentilator': row_dict['onVentilatorCurrently'],
          'CumulativeCount_MedicalConditionIncident_COVID_19_PatientOnVentilator': row_dict['onVentilatorCumulative'],
      }   

      writer.writerow(processed_dict)

TEMPLATE_MCF_TEMPLATE = """
Node: E:COVIDTracking_US->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:CovidTrackingProject
observationAbout: dcid:country/USA
observationDate: C:COVIDTracking_US->Date
value: C:COVIDTracking_US->{stat_var}
"""

stat_vars = output_columns[1:]
with open('COVIDTracking_US.tmcf', 'w', newline='') as f_out:
  for i in range(len(stat_vars)):
    f_out.write(TEMPLATE_MCF_TEMPLATE.format_map({'index': i, 'stat_var': output_columns[1:][i]}))
