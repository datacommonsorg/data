import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from urllib.request import urlopen
import datetime
from typing import Dict

def _get_css_value(css: str, find: str) -> str:
    if not css or not find:
        return ""

    styles = css.split(';')
    for style in styles:
        key, value = style.split(":")
        if find == key.strip():
            return value

def _is_valid_date(date_text: str) -> bool:
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def parse_time_series_chart(url: str) -> Dict[str, Dict[str, int]]:
    html = urlopen(url)
    soup = BeautifulSoup(html, 'html.parser')

    # heading = soup.find("h1", {"id": "firstHeading"})

    table = soup.findAll("table")[0]

    span_labels = table.findAll("span", {"style": "font-size:90%; margin:0px"})

    color_to_label = {}

    for span_label in span_labels:
        span, label = span_label.contents
        style = span['style']
        color = _get_css_value(style, "color")
        if color and label:
            color_to_label[color] = label.strip("\xa0")

    rows = table.findAll("tr", {"class": "mw-collapsible"})

    data = {}

    for row in rows:
        date = row.find("td", {"class": "bb-04em"}).contents[0]
        if not _is_valid_date(date):
            continue
        data[date] = {}

        td_colors = row.find("td", {"class": "bb-lr"})
        div_labels = td_colors.findAll("div")

        for div_label in div_labels:
            for color, label in color_to_label.items():
                if color in div_label["style"]:
                    value = div_label["title"]
                    data[date][label] = value
    return data
