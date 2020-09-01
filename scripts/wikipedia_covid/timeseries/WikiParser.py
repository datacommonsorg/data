import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from urllib.request import urlopen
import datetime
from typing import Dict, List


def _get_css_value(css: str, key: str) -> str:
    # CSS input has to be valid.
    # key input has to be valid.
    if not css or not key:
        return ""

    # Search for the key
    styles: List[str] = css.split(';')
    for style in styles:
        key, value = style.split(":")
        # key found in CSS. Return it.
        if find == key.strip():
            return value
    
    # key has not be found in CSS.
    return ""

def _is_valid_date(date_text: str) -> bool:
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def get_wiki_id(url: str) -> str:
    html = urlopen(url)
    soup = BeautifulSoup(html, 'html.parser')
    li_wikidata = soup.find("li", {"id": "t-wikibase"})
    a_wikidata = li_wikidata.find('a')
    entity_page = a_wikidata['href'].split(':')[-1]
    wiki_id = entity_page.split('/')[-1]
    print(wiki_id)
    return wiki_id


def parse_time_series_chart(url: str) -> Dict[str, Dict[str, int]]:
    print(url)
    html = urlopen(url)
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.findAll("table")[0]

    span_labels = table.findAll("span", {"style": "font-size:90%; margin:0px"})

    color_to_label = {}

    for span_label in span_labels:
        if len(span_label.contents) < 2:
            continue

        span = span_label.contents[0]
        label = span_label.contents[1].lower()
        
        style = span['style']
        color = _get_css_value(style, "color")

        if color and label:
            color_to_label[color] = label.strip("\xa0")

    rows = table.findAll("tr", {"class": "mw-collapsible"})

    data = {}

    for row in rows:
        tds = row.findAll("td")

        if len(tds) < 2:
            continue

        td_date, td_colors = tds[0], tds[1]
        date = td_date.contents[0]

        if not _is_valid_date(date):
            continue

        data[date] = {}
        div_labels = td_colors.findAll("div")

        for div_label in div_labels:
            for color, label in color_to_label.items():
                if color in div_label["style"]:
                    value = div_label["title"]
                    data[date][label] = value
    return data
