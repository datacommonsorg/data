import requests
import pandas as pd
from absl import app
from absl import flags
from util import statvar_dcid_generator


FLAGS = flags.FLAGS
flags.DEFINE_string("country", "USA", "Country codes")
#maximum the API Can display is 32767
flags.DEFINE_integer("per_page", 32, "rows per page")
flags.DEFINE_string("output_csv", "WorldBankHNP_Expenditure_Tests.csv", "Path of final csv")


def get_df(serieses):
    '''gets df from json webpage'''
    df2 = pd.DataFrame(columns = ['Series Name', 'Series Code', 'Country Code',
                                  'Country', 'Year', 'Value'])
    series = ['SH.XPD.KHEX.GD.ZS', 'SH.XPD.CHEX.GD.ZS', 'SH.XPD.CHEX.PC.CD',
	      'SH.XPD.CHEX.PP.CD', 'SH.XPD.GHED.CH.ZS', 'SH.XPD.GHED.GD.ZS',
              'SH.XPD.GHED.GE.ZS', 'SH.XPD.GHED.PC.CD', 'SH.XPD.EHEX.CH.ZS',
              'SH.XPD.EHEX.EH.ZS', 'SH.XPD.PVTD.PP.CD', 'SH.XPD.PVTD.CH.ZS',
              'SH.XPD.PVTD.PC.CD', 'SH.XPD.GHED.PP.CD']
    for current_series in list(serieses):
        url = "https://api.worldbank.org/v2/country/all/indicator/"
        url = url + f"{current_series}?format=JSON&per_page=17000"
        response = requests.get(url)
        response = response.json()
        print(response[1][0]['indicator']['value'])
        for i in range(len(response[1])):
            if response[1][i]['value']:
                row = {"Series Name" : response[1][i]['indicator']['value'],
                    "Series Code" : response[1][i]['indicator']['id'],
                    "Country Code" : response[1][i]['countryiso3code'],
                    "Country" : response[1][i]['country']['value'],
                    "Year" : response[1][i]['date'],
                    'Value' : response[1][i]['value']
                    }

                df2.loc[len(df2)] = row
    return df2


def from_mcf(mcf):
	node_list = mcf.split("\n\n")
	desc_var_dict = dict()
	for node in node_list:
		property_dict = dict()
		prop_list = node.strip().split("\n")
		for prop in prop_list:
			property_dict[prop.split(": ")[0]] = prop.split(': ')[-1]
		var = get_statvar_dcid(property_dict)
		try:
			desc_var_dict[property_dict['description']] = var
		except:
			print(end = '')
	return desc_var_dict

def get_csv(input_df):
    '''
    create csv according to tmcf
    '''
    df2 = pd.DataFrame(columns = ['observationAbout', 'observationDate', "variableMeasured", 'value'])
    row_count = len(df)
    for line in range(row_count):
        desc = input_df['Series Name'][line]
        unit = ''
        if input_df['Country Code'][line]:
            row = ({'observationAbout' : "country/" + input_df['Country Code'][line],
              'observationDate' : input_df['Year'][line],
              'variableMeasured' : var_desc_dict[f"'{desc}'"],
              'value' : input_df['Value'][line]})

            df2.loc[len(df2.index)]=list(row.values())
    print(df2.head(len(df2)))
    df2.to_csv("WorldBankHealthcareExpenditure.csv")

def main(argv):
    df = get_df(FLAGS.per_page, FLAGS.country)
    get_csv(df, FLAGS.output_csv)

if __name__ == '__main__':
    app.run(main)
