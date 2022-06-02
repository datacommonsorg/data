"""
Contains the recurring functions of other files
"""
import json
import os
import pandas as pd


def _input_url(file_name: str, key_name: str):
    """
    Take the File Name and Key as input
    and provide the URLs of the specified year/geo as output.
    """
    _URLS_JSON_PATH = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + file_name
    _URLS_JSON = None
    with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
        _URLS_JSON = json.load(file)
    _url = _URLS_JSON[key_name]
    return _url

def _replace_age(df: pd.DataFrame):
    """
    Replaces the columns of DF as per metadata
    """
    _age = {
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
    }
    df.rename(columns=_age, inplace=True)
    return df
