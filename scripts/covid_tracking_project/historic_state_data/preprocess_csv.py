import csv
import io
import urllib.request

output_columns = ['Date', 'GeoId',
                  'COVID19CumulativeTestResults', 'COVID19NewTestResults',
                  'COVID19CumulativePositiveTestResults', 'COVID19NewPositiveTestResults',
                  'COVID19CumulativeNegativeTestResults', 'COVID19NewNegativeTestResults',
                  'COVID19PendingTests',
                  'COVID19CumulativeRecoveredCases', 'COVID19CumulativeDeaths', 'COVID19NewDeaths',
                  'COVID19CurrentHospitalizedCases', 'COVID19CumulativeHospitalizedCases', 'COVID19NewHospitalizedCases',
                  'COVID19CurrentICUCases', 'COVID19CumulativeICUCases',
                  'COVID19CurrentVentilatorCases', 'COVID19CumulativeVentilatorCases',
                 ]
with open('COVIDTracking_States.csv', 'w', newline='') as f_out:
  writer = csv.DictWriter(f_out, fieldnames=output_columns, lineterminator='\n')
  with urllib.request.urlopen('https://covidtracking.com/api/v1/states/daily.csv') as response:
    reader = csv.DictReader(io.TextIOWrapper(response))

    writer.writeheader()
    for row_dict in reader:
      processed_dict = {
          'Date': '%s-%s-%s' % (row_dict['date'][:4], row_dict['date'][4:6], row_dict['date'][6:]),
          'GeoId': 'geoId/%s' % row_dict['fips'],
          'COVID19CumulativeTestResults': row_dict['totalTestResults'],
          'COVID19NewTestResults': row_dict['totalTestResultsIncrease'],
          'COVID19CumulativePositiveTestResults': row_dict['positive'],
          'COVID19NewPositiveTestResults': row_dict['positiveIncrease'],
          'COVID19CumulativeNegativeTestResults': row_dict['negative'],
          'COVID19NewNegativeTestResults': row_dict['negativeIncrease'],
          'COVID19PendingTests': row_dict['pending'],
          'COVID19CumulativeRecoveredCases': row_dict['recovered'],
          'COVID19CumulativeDeaths': row_dict['death'],
          'COVID19NewDeaths': row_dict['deathIncrease'],
          'COVID19CurrentHospitalizedCases': row_dict['hospitalizedCurrently'],
          'COVID19CumulativeHospitalizedCases': row_dict['hospitalizedCumulative'],
          'COVID19NewHospitalizedCases': row_dict['hospitalizedIncrease'],
          'COVID19CurrentICUCases': row_dict['inIcuCurrently'],
          'COVID19CumulativeICUCases': row_dict['inIcuCumulative'],
          'COVID19CurrentVentilatorCases': row_dict['onVentilatorCurrently'],
          'COVID19CumulativeVentilatorCases': row_dict['onVentilatorCumulative'],
      }   

      writer.writerow(processed_dict)

# Automate Template MCF generation since there are 18 Statitical Variables.
TEMPLATE_MCF_GEO = """
Node: E:COVIDTracking_States->E0
typeOf: dcs:State
dcid: C:COVIDTracking_States->GeoId
"""

TEMPLATE_MCF_TEMPLATE = """
Node: E:COVIDTracking_States->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
observationAbout: E:COVIDTracking_States->E0
observationDate: C:COVIDTracking_States->Date
value: C:COVIDTracking_States->{stat_var}
"""

stat_vars = output_columns[2:]
with open('COVIDTracking_States.tmcf', 'w', newline='') as f_out:
  f_out.write(TEMPLATE_MCF_GEO)
  for i in range(len(stat_vars)):
    f_out.write(TEMPLATE_MCF_TEMPLATE.format_map({'index': i+1, 'stat_var': output_columns[2:][i]}))