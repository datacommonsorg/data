# Lint as: python3
"""
This script preprocesses the covid19 data from Italy Department of Civil Protection for importing into Data Commons.
"""

import sys
import pandas as pd


class pcm_dpc:

  def _translate(self):
    # translate coloumn names from italian to english
    it2en = {'data': 'Date', 'stato': 'State', 'codice_regione': 'RegionCode', 'denominazione_regione': 'RegionName', \
      'codice_provincia': 'ProvinceCode', 'denominazione_provincia': 'ProvinceName', 'sigla_provincia':'ProvinceAbbreviation',\
      'lat': 'Latitude', 'long': 'Longitude',\
      'ricoverati_con_sintomi': 'HospitalizedsWithSymptoms', 'terapia_intensiva': 'IntensiveCare', \
      'totale_ospedalizzati': 'Hospitalized', 'isolamento_domiciliare': 'PeopleInHomeIsolation', \
      'totale_positivi': 'ActiveCase', 'variazione_totale_positivi': 'IncrementalPositiveCase', \
      'nuovi_positivi': 'IncrementalActiveCase', 'dimessi_guariti':'CumulativeRecovered', 'deceduti': 'CumulativeDeath', \
      'totale_casi':'CumulativePositiveCase', 'tamponi': 'CumulativeTestsPerformed', 'casi_testati': 'CumulativeTestedPeople'}
    self.data = self.data.rename(columns = it2en)
    
  def preprocess(self):
    # clean and save the CSV file for importing into DataCommons
    self.data = pd.read_csv(self.csvpath).drop(columns = ['note_it', 'note_en'])
    self._translate()
    self.data['Date'] = self.data['Date'].str[0:10]
    self.setLocation()
    self.data.to_csv(self.name + '.csv')
    
  def setLocation(self):
    pass
    
  def generate_tmcf(self):
    #generate the template mcf
    self.geoTemplate()
    TEMPLATE = 'Node: E:pcm-dpc->E{index}\n' +\
               'typeOf: dcs:StatVarObservation\n' +\
               'variableMeasured: dcs:COVID19_{SVname}\n' +\
               'observationAbout: E:pcm-dpc->E0\n' +\
               'observationDate: C:pcm-dpc->Date\n' +\
               'value: C:pcm-dpc->{SVname}\n\n'
    idx = 1
    with open(self.name + '.mcf', 'a') as f_out:
      for sv in self.StatVar:
        f_out.write(TEMPLATE.format_map({'index': idx, 'SVname': sv}))
        idx += 1

  def generate_SV(self):
    # generate the mcf for StatisticalVariables
    StatVar_TEMPLATE = 'Node: dcid:COVID19_{SVFullName}\n' +\
                       'typeOf: dcs:StatisticalVariable\n' +\
                       'populationType: dcs:{population}\n' +\
                       'incidentType: dcs:COVID_19\n' +\
                       'measuredProperty: dcs:{countType}\n' +\
                       'statType: dcs:measuredValue\n' +\
                       'medicalStatus: dcs:{SVname}\n\n'
    
    with open(self.name + '_StatisticalVariable.mcf', 'w') as f_out:
      for svFull in self.StatVar:
      
        if "Cumulative" in svFull:
          countType = "cumulativeCount"
          sv = svFull[10:]
        elif "Incremental" in svFull:
          countType = "incrementalCount"
          sv = svFull[11:]
        else:
          countType = "count"
          sv = svFull
        
        if "Test" in svFull:
          populationType = "MedicalTest"
        else:
          populationType = "MedicalConditionIncident"
        
        f_out.write(StatVar_TEMPLATE.format_map({'SVFullName': svFull, 'population': populationType, \
            'countType': countType, 'SVname':sv}))
  
  
class pcm_dpc_national(pcm_dpc):
  def __init__(self):
    self.csvpath = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv"
    self.name = "dpc-covid19-ita-national-trend"
    self.StatVar = ['HospitalizedsWithSymptoms', 'IntensiveCare', 'Hospitalized', \
    'PeopleInHomeIsolation', 'ActiveCase',  'IncrementalPositiveCase', 'IncrementalActiveCase', \
    'CumulativeRecovered', 'CumulativeDeath', 'CumulativePositiveCase', 'CumulativeTestsPerformed', 'CumulativeTestedPeople']
    
  def setLocation(self):
    assert (self.data['State'] == 'ITA').all()
    self.data['Location'] = 'country/ITA'
    self.data = self.data.drop(columns = ['State'])
    
  def geoTemplate(self):
    Geo_TEMPLATE = 'Node: E:pcm-dpc->E0\n' +\
                   'typeOf: dcs:Country\n' +\
                   'dcid: C:pcm-dpc->Location\n\n'
    with open(self.name + '.mcf', 'w') as f_out:
      f_out.write(Geo_TEMPLATE)
  
class pcm_dpc_regions(pcm_dpc):
  def __init__(self):
    self.csvpath = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv"
    self.name = "dpc-covid19-ita-regional"
    self.StatVar = ['HospitalizedsWithSymptoms', 'IntensiveCare', 'Hospitalized', \
    'PeopleInHomeIsolation', 'ActiveCase',  'IncrementalPositiveCase', 'IncrementalActiveCase', \
    'CumulativeRecovered', 'CumulativeDeath', 'CumulativePositiveCase', 'CumulativeTestsPerformed', 'CumulativeTestedPeople']
    
  def setLocation(self):
    self.data['Location'] = self.data['State'] + '/' + self.data['RegionCode'].astype(str)
    #self.data['ContainedIn'] = 'country'+ '/' + self.data['State']
    #self.data = self.data.drop(columns = ['State', 'RegionCode'])
    #self.data = self.data.drop(columns = ['RegionName', 'Latitude', 'Longitude'])
    
  def geoTemplate(self):
     Geo_TEMPLATE = 'Node: E:pcm-dpc->E0\n' +\
                    'typeOf: dcs:State\n' +\
                    'dcid: C:pcm-dpc->Location\n' +\
                    'name: C:pcm-dpc->RegionName\n' +\
                    'latitude: C:pcm-dpc->Latitude\n' +\
                    'longitude: C:pcm-dpc->Longitude\n\n'
                    #'ContainedIn: C:pdm-dpc->ContainedIn\n\n'
                    
     with open(self.name + '.mcf', 'w') as f_out:
       f_out.write(Geo_TEMPLATE)
    
class pcm_dpc_provinces(pcm_dpc):
  
  def __init__(self):
    self.csvpath = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-province/dpc-covid19-ita-province.csv"
    self.name = "dpc-covid19-ita-province"
    self.StatVar = ['CumulativePositiveCase']
    
  def setLocation(self):
    self.data['Location'] = self.data['State'] + '/' + self.data['RegionCode'].astype(str) + '/' + self.data['ProvinceCode'].astype(str)
    #self.data['ContainedIn'] = self.data['State'] + '/' + self.data['RegionCode'].astype(str)
    #self.data = self.data.drop(columns  = ['State', 'RegionCode', 'ProvinceCode'])
    #self.data = self.data.drop(columns = ['ProvinceCode', 'ProvinceName' 'Latitude', 'Longitude'])

  def geoTemplate(self):
    Geo_TEMPLATE = 'Node: E:pcm-dpc->E0\n' +\
                   'typeOf: dcs:County\n' +\
                   'dcid: C:pcm-dpc->Location\n' +\
                   'name: C:pcm-dpc->ProvinceName\n' +\
                   'latitude: C:pcm-dpc->Latitude\n' +\
                   'longitude: C:pcm-dpc->Longitude\n\n'
                   #'containedIn: C:pdm-dpc->ContainedIn\n\n'

    with open(self.name + '.mcf', 'w') as f_out:
      f_out.write(Geo_TEMPLATE)

def main(argv):

  HELPINFO = "\tspecify the dataset type and function:\n" +\
    "\tdataset type: National, Regions, Provinces\n" +\
    "\tfunctions: preprocess, generate_tmcf, generate_SV\n\n"
    
  if len(argv) < 2:
    print(HELPINFO)
    return
  
  if argv[0] == "National":
    data = pcm_dpc_national()
  elif argv[0] == "Regions":
    data = pcm_dpc_regions()
  elif argv[0] == "Provinces":
    data = pcm_dpc_provinces()
  else:
    print(HELPINFO)
    return
    
  if argv[1] == "preprocess":
    data.preprocess()
  elif argv[1] == "generate_tmcf":
    data.generate_tmcf()
  elif argv[1] == "generate_SV":
    data.generate_SV()
  else:
    print(HELPINFO)

if __name__ == "__main__":
  main(sys.argv[1:])
  
