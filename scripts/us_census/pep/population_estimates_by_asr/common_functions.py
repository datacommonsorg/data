"""
Contains the recurring functions of other files
"""
import json
import os
import pandas as pd


def input_url(file_name: str, key_name: str):
    """
    Take the File Name and Key as input
    and provide the URLs of the specified year/geo as output.
    """
    _URLS_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   file_name)
    _URLS_JSON = None
    with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
        _URLS_JSON = json.load(file)
    _url = _URLS_JSON[key_name]
    return _url


def replace_age(df: pd.DataFrame):
    """
    Replaces the columns of DF as per metadata
    """
    df.rename(columns={
        0: '0To4Years',
        1: '5To9Years',
        2: '10To14Years',
        3: '15To19Years',
        4: '20To24Years',
        5: '25To29Years',
        6: '30To34Years',
        7: '35To39Years',
        8: '40To44Years',
        9: '45To49Years',
        10: '50To54Years',
        11: '55To59Years',
        12: '60To64Years',
        13: '65To69Years',
        14: '70To74Years',
        15: '75To79Years',
        16: '80To84Years',
        17: '85OrMoreYears'
    },
              inplace=True)
    return df


def replace_agegrp(df: pd.DataFrame, inp_flag: int):
    if inp_flag == 1:
        df = df.replace({"AGEGRP": {'1': '0To4Years'}})
    else:
        df = df.replace({"AGEGRP": {
            '0': '0Years',
            '1': '1To4Years',
        }})
    df = df.replace({
        "AGEGRP": {
            '2': '5To9Years',
            '3': '10To14Years',
            '4': '15To19Years',
            '5': '20To24Years',
            '6': '25To29Years',
            '7': '30To34Years',
            '8': '35To39Years',
            '9': '40To44Years',
            '10': '45To49Years',
            '11': '50To54Years',
            '12': '55To59Years',
            '13': '60To64Years',
            '14': '65To69Years',
            '15': '70To74Years',
            '16': '75To79Years',
            '17': '80To84Years',
            '18': '85OrMoreYears'
        }
    })
    return df


def gender_based_grouping(df: pd.DataFrame):
    """
    Aggregates the columns based on gender by removing race from SV
    """
    df['SVs'] = df['SVs'].str.replace('_WhiteAlone', '')
    df['SVs'] = df['SVs'].str.replace('_BlackOrAfricanAmericanAlone', '')
    df['SVs'] = df['SVs'].str.replace('_OtherRaces', '')
    df['SVs'] = df['SVs'].str.replace('_AmericanIndianAndAlaskaNativeAlone', '')
    df['SVs'] = df['SVs'].str.replace('_AsianOrPacificIslander', '')
    df['SVs'] = df['SVs'].str.replace('_AsianAlone', '')
    df['SVs'] = df['SVs'].str.replace\
        ('_NativeHawaiianAndOtherPacificIslanderAlone', '')
    df['SVs'] = df['SVs'].str.replace('_TwoOrMoreRaces', '')
    df = df.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    return df


def race_based_grouping(df: pd.DataFrame):
    """
    Aggregates the columns based on race by removing gender from SV
    """
    df['SVs'] = df['SVs'].str.replace('_Male', '')
    df['SVs'] = df['SVs'].str.replace('_Female', '')
    df = df.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    return df
