# Lint as: python3
"""
This script preprocesses the covid19 data from Italy Department of Civil
Protection for importing into Data Commons.
"""

import pandas as pd

class PcmDpc:
    """download the csv files and preprocess it for importing into
    DataCommons"""
    def preprocess(self):
        """clean and save the CSV file"""
        self.data = pd.read_csv(self.csvpath).drop(
            columns=['note'])
        self._translate()
        self.data['Date'] = self.data['Date'].str[0:10]
        self.set_location() # prepocess the geo ids
        self.data.to_csv(self.name + '.csv', index=False)

    def generate_tmcf(self):
        """ generate the template mcf"""
        self.geo_template() # write the geo node to template mcf
        TEMPLATE = ('Node: E:pcm-dpc->E{index}\n'
                    'typeOf: dcs:StatVarObservation\n'
                    'variableMeasured: dcs:COVID19_Italy_{SVname}\n'
                    'observationAbout: E:pcm-dpc->E0\n'
                    'observationDate: C:pcm-dpc->Date\n'
                    'value: C:pcm-dpc->{SVname}\n\n')
        idx = 1
        with open(self.name + '.tmcf', 'a') as f_out:
            for statvar in self.stat_vars:
                f_out.write(TEMPLATE.format_map({'index': idx, 'SVname': statvar}))
                idx += 1

    def _translate(self):
        """translate coloumn names from italian to english"""
        it2en = {'data': 'Date', 'stato': 'State',
                 'codice_regione':'RegionCode',
                 'denominazione_regione': 'RegionName',
                 'codice_provincia': 'ProvinceCode',
                 'denominazione_provincia': 'ProvinceName',
                 'sigla_provincia': 'ProvinceAbbreviation',
                 'lat': 'Latitude', 'long': 'Longitude',
                 'ricoverati_con_sintomi': 'HospitalizedsWithSymptoms',
                 'terapia_intensiva': 'IntensiveCare',
                 'totale_ospedalizzati': 'Hospitalized',
                 'isolamento_domiciliare': 'PeopleInHomeIsolation',
                 'totale_positivi': 'ActiveCase',
                 'variazione_totale_positivi': 'IncrementalPositiveCase',
                 'nuovi_positivi': 'IncrementalActiveCase',
                 'dimessi_guariti': 'CumulativeRecovered',
                 'deceduti': 'CumulativeDeath',
                 'totale_casi':'CumulativePositiveCase',
                 'tamponi': 'CumulativeTestsPerformed',
                 'casi_testati': 'CumulativeTestedPeople'}
        self.data = self.data.rename(columns=it2en)

    def set_location(self):
        pass

    def geo_template(self):
        pass

class PcmDpcNational(PcmDpc):
    """subclass processing national data"""
    def __init__(self):
        self.csvpath = ('https://raw.githubusercontent.com/pcm-dpc/COVID-19/'
                        'master/dati-andamento-nazionale/dpc-covid19-ita-and'
                        'amento-nazionale.csv')
        self.name = "dpc-covid19-ita-national-trend"
        self.stat_vars = ['HospitalizedsWithSymptoms', 'IntensiveCare',
                          'Hospitalized', 'PeopleInHomeIsolation', 'ActiveCase',
                          'IncrementalPositiveCase', 'IncrementalActiveCase',
                          'CumulativeRecovered', 'CumulativeDeath',
                          'CumulativePositiveCase', 'CumulativeTestsPerformed',
                          'CumulativeTestedPeople']

    def set_location(self):
        assert (self.data['State'] == 'ITA').all()
        self.data['Location'] = 'country/ITA'
        self.data = self.data.drop(columns=['State'])

    def geo_template(self):
        GEO_TEMPLATE = ('Node: E:pcm-dpc->E0\n'
                        'typeOf: dcs:Country\n'
                        'dcid: C:pcm-dpc->Location\n\n')
        with open(self.name + '.tmcf', 'w') as f_out:
            f_out.write(GEO_TEMPLATE)


class PcmDpcRegions(PcmDpc):
    """subclass processing regional data"""
    def __init__(self):
        self.csvpath = ('https://raw.githubusercontent.com/pcm-dpc/COVID-19/'
                        'master/dati-regioni/dpc-covid19-ita-regioni.csv')
        self.name = "dpc-covid19-ita-regional"
        self.stat_vars = ['HospitalizedsWithSymptoms', 'IntensiveCare',
                          'Hospitalized', 'PeopleInHomeIsolation', 'ActiveCase',
                          'IncrementalPositiveCase', 'IncrementalActiveCase',
                          'CumulativeRecovered', 'CumulativeDeath',
                          'CumulativePositiveCase', 'CumulativeTestsPerformed',
                          'CumulativeTestedPeople']

    def set_location(self):
        region_code_path = ('https://raw.githubusercontent.com/qlj-lijuan/data/'
                            'master/scripts/istat/geos/cleaned/ISTAT_region.csv')
        region_code = pd.read_csv(region_code_path)[['Region Code', 'NUTS2']]
        code_dict = region_code.set_index('Region Code').to_dict()['NUTS2']
        # region code 21 and 22 is missing from the dict above, add manually here.
        code_dict[21] = 'nuts/ITH1'
        code_dict[22] = 'nuts/ITH2'
        self.data['Location'] = self.data['RegionCode'].map(code_dict)
        self.data = self.data.drop(columns=['State', 'RegionCode', 'RegionName',
                                            'Latitude', 'Longitude'])

    def geo_template(self):
        GEO_TEMPLATE = 'Node: E:pcm-dpc->E0\n' +\
                    'typeOf: dcs:EurostatNUTS2\n' +\
                    'dcid: C:pcm-dpc->Location\n\n'
        with open(self.name + '.tmcf', 'w') as f_out:
            f_out.write(GEO_TEMPLATE)


class PcmDpcProvinces(PcmDpc):
    """subclass of provinces data"""
    def __init__(self):
        self.csvpath = ('https://raw.githubusercontent.com/pcm-dpc/COVID-19/'
                        'master/dati-province/dpc-covid19-ita-province.csv')
        self.name = "dpc-covid19-ita-province"
        self.stat_vars = ['CumulativePositiveCase']

    def set_location(self):
        province_code_path = ('https://raw.githubusercontent.com/qlj-lijuan/data'
                              '/master/scripts/istat/geos/cleaned/ISTAT_province'
                              '.csv')
        province_code = pd.read_csv(province_code_path)[['Province Abbreviation',
                                                       'NUTS3']]
        province_dict = (province_code.set_index('Province Abbreviation')
                         .to_dict()['NUTS3'])
        # drop the data whose location is "being defined/updated",
        # i.e. ProvinceCode > 111.
        # location Sud Sardegna (Province Code = 111) is not defined as a
        # unique area in DataCommons, skip for now.
        self.data = self.data[self.data['ProvinceCode'] < 111].reset_index()
        self.data['Location'] = self.data['ProvinceAbbreviation'].map(
            province_dict)
        self.data = self.data[['Date', 'Location', 'CumulativePositiveCase']]

    def geo_template(self):
        GEO_TEMPLATE = ('Node: E:pcm-dpc->E0\n'
                        'typeOf: dcs:EurostatNUTS3\n'
                        'dcid: C:pcm-dpc->Location\n\n')
        with open(self.name + '.tmcf', 'w') as f_out:
            f_out.write(GEO_TEMPLATE)

def main():
    """process the national, regional, provinces data and generate
    correponding template mcfs"""
    data_obj = [PcmDpcNational(), PcmDpcRegions(), PcmDpcProvinces()]
    for data in data_obj:
        data.preprocess()
        data.generate_tmcf()

if __name__ == "__main__":
    main()
