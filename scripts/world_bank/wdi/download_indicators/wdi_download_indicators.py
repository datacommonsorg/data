"""Download World Bank WDI via API and write cleaned csv to out_path."""

import io
import urllib.request
import zipfile

from absl import app
from absl import flags
import numpy as np
import pandas as pd

# The output path should have a default filename.
_OUT_DEFAULT_NAME = 'cleaned_wdi.csv'
_OUT_PATH = flags.DEFINE_string('out_path', _OUT_DEFAULT_NAME,
                                'CNS path to write output.')

indicators = [
    'SP.POP.TOTL',
    'SP.POP.TOTL.FE.IN',
    'SP.POP.TOTL.MA.IN',
    'SP.POP.0014.TO.ZS',
    'SP.POP.1564.TO.ZS',
    'SP.POP.65UP.TO.ZS',
    'SP.DYN.LE00.IN',
    'SP.URB.TOTL.IN.ZS',
    'SP.URB.TOTL',
    'SP.POP.0014.FE.ZS',
    'SP.POP.1519.FE.5Y',
    'SP.POP.2024.FE.5Y',
    'SP.POP.2529.FE.5Y',
    'SP.POP.3034.FE.5Y',
    'SP.POP.3539.FE.5Y',
    'SP.POP.4044.FE.5Y',
    'SP.POP.4549.FE.5Y',
    'SP.POP.5054.FE.5Y',
    'SP.POP.5559.FE.5Y',
    'SP.POP.6064.FE.5Y',
    'SP.POP.65UP.FE.ZS',
    'SP.POP.0014.MA.ZS',
    'SP.POP.1519.MA.5Y',
    'SP.POP.2024.MA.5Y',
    'SP.POP.2529.MA.5Y',
    'SP.POP.3034.MA.5Y',
    'SP.POP.3539.MA.5Y',
    'SP.POP.4044.MA.5Y',
    'SP.POP.4549.MA.5Y',
    'SP.POP.5054.MA.5Y',
    'SP.POP.5559.MA.5Y',
    'SP.POP.6064.MA.5Y',
    'SP.POP.65UP.MA.ZS',
    'SE.ADT.LITR.ZS',
    'SE.ADT.LITR.FE.ZS',
    'SE.ADT.LITR.MA.ZS',
    'SE.ADT.1524.LT.ZS',
    'SE.ADT.1524.LT.FE.ZS',
    'SE.ADT.1524.LT.MA.ZS',
    'NY.GDP.MKTP.CD',
    'NY.GDP.MKTP.KD.ZG',
    'NV.AGR.TOTL.ZS',
    'NV.AGR.TOTL.CD',
    'NV.SRV.TOTL.ZS',
    'NV.SRV.TOTL.CD',
    'NV.IND.TOTL.ZS',
    'NV.IND.TOTL.CD',
    'NY.GNP.PCAP.PP.CD',
    'SI.POV.GINI',
    'IT.NET.USER.ZS',
]


def DownloadAndParseCsvs() -> None:
    """Loops through all indicators and downloads the data for all countries/dates.

  This data is then added to the output which is written to _OUT_PATH
  """
    dat = []
    for indicator in indicators:
        print(f'DOWNLOADING: {indicator}....')
        resp = urllib.request.urlopen(
            f'http://api.worldbank.org/v2/country/all/indicator/{indicator}?source=2&downloadformat=csv'
        )
        myzip = zipfile.ZipFile(io.BytesIO(resp.read()))
        csv_data = pd.DataFrame()
        start_index = 0
        found = False
        for filename in myzip.namelist():
            if filename.startswith('API_'):
                with myzip.open(filename) as f:
                    for line in f:
                        if line.decode('utf-8').startswith('"Country'):
                            break
                        start_index += 1
                with myzip.open(filename) as f:
                    csv_data = pd.read_csv(f, skiprows=start_index)
                    found = True
        if found:
            for _, row in csv_data.iterrows():
                if True in pd.isna(row):
                    continue
                for year in range(1960, 2022):
                    if pd.isna(row['Country Code']):
                        continue
                    country_str = 'dcid:country/' + row['Country Code']
                    sv_string = 'worldBank/' + row['Indicator Code'].replace(
                        '.', '_')
                    dat.append([
                        row['Indicator Code'],
                        sv_string,
                        'WorldBank_WDI_CSV',
                        country_str,
                        year,
                        row[str(year)],
                        '',
                    ])

    out_df = pd.DataFrame(
        np.array(dat),
        columns=[
            'indicatorcode',
            'statvar',
            'measurementmethod',
            'observationabout',
            'observationdate',
            'observationvalue',
            'unit',
        ],
    )
    # Write to the _OUT_PATH which defaults to the output filename
    # if no path is provided.
    with open(_OUT_PATH.value, 'w+') as f_out:
        out_df.to_csv(f_out, index=False)


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    DownloadAndParseCsvs()


if __name__ == '__main__':
    app.run(main)
