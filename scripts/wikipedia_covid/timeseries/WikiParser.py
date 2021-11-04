import datetime
from typing import Dict, List
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from Config import REPLACE_HEADERS, PLACES
from os import path
from io import StringIO


def _get_css_value(css: str, key: str) -> str:
    """
    Given a valid CSS, return the key if it exists.
    Otherwise, return "".
    @param css: the text of CSS code.
    @param key: the key of the value to get.

    Example:
    css = "background: green; font: 10;"
    key = "font"
    Returns str(10);
    """
    # CSS input has to be valid.
    # key input has to be valid.
    if not css or not key:
        return ""

    # Search for the key.
    styles: List[str] = css.lower().split(';')
    for style in styles:
        key, value = style.split(":")
        # key found in CSS. Return it.
        if key == key.strip():
            return value

    # key has not be found in CSS.
    return ""


def _is_valid_date(date_text: str) -> bool:
    """
    Returns True if the input date is a valid date
    in the ISO form of YYYY-MM-DD.
    @param date_text: ISO date.
    """
    # The date must be an string.
    if not isinstance(date_text, str):
        return False

    # Try to convert the string to a date datetime object.
    # If it throws a ValueError exception, it means that
    # it's not a valid formatted date.
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def get_place_name_from_url(url: str) -> str:
    """
    Given a Wikipedia Template Time Series Chart URL or HTML document,
    return the name of the place being observed.
    @param url: Wikipedia Template Time Series Chart URL or HTML document
    """

    # If no input url, return ""
    if not url:
        return ""

    # If the input is a path, instead of a URL.
    # Use name of document instead.
    if path.exists(url):
        place_name = url.split(".")[0]
        return place_name

    # Otherwise, it means it's a URL so strip out the name from the URL.
    place_name = url.split('_medical_cases_chart')[-2]
    place_name = place_name.split('pandemic_data/')[-1]
    place_name = place_name.split('/')[-1]
    return place_name


def get_wikidata_id(wiki_url: str) -> str:
    """
    Given any Wikipedia page, return the WikidataId for the place observed.
    For Example:
    https://en.wikipedia.org/wiki/Spain will return "Q29".
    """
    html = urlopen(wiki_url)
    soup = BeautifulSoup(html, 'html.parser')
    li_wikidata = soup.find("li", {"id": "t-wikibase"})
    a_wikidata = li_wikidata.find('a')
    entity_page = a_wikidata['href'].split(':')[-1]
    wikidata_id = entity_page.split('/')[-1]
    return wikidata_id


def parse_time_series_chart(wiki_url: str) -> Dict[str, Dict[str, int]]:
    """
    Given a Wikipedia Template Time Series Table URL or HTML document
    return a dictionary of the data in the page.
    @param wiki_url: Wikipedia Template Time Series Table URL or HTML document
    """
    html = ""
    try:
        # Query the HTML of the Wikipedia site.
        html = urlopen(wiki_url)
    except:
        # Query the HTML of an HTML file.
        with open(wiki_url, "r+") as f:
            html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # Find the first table element in the site.
    table = soup.findAll("table")

    # If no table is available, return nothing.
    if not table:
        return {}

    # Get the first table available
    table = table[0]

    # Get a map of color -> label
    # The table doesn't refer to items by label but rather by color.
    span_labels = table.findAll("span", {"style": "font-size:90%; margin:0px"})

    color_to_label = {}

    for span_label in span_labels:
        # There must be two contents inside the span.
        # content1: color
        # content2: label
        if len(span_label.contents) != 2:
            continue

        # Get the color span.
        color_span, label_text = span_label.contents[0:2]

        # Clean up the label text.
        # To lower-case and strip string.
        label = label_text.lower().strip("\xa0")

        # Rename any labels by Config.REPLACE_HEADERS file.
        if label in REPLACE_HEADERS:
            label = REPLACE_HEADERS[label]

        # Get the color of the label.
        css_style = color_span['style']
        color = _get_css_value(css_style, "color")

        # Store the color -> label in the dictionary.
        if color and label:
            color_to_label[color] = label

    # Get all the rows in the table.
    rows = table.findAll("tr")

    # Store all the data as label -> date -> int
    data = {}

    for row in rows:
        # Get all columns in that row.
        tds = row.findAll("td")

        # Single-column rows are tipically headers.
        if len(tds) <= 1:
            continue

        # Get the td containing color an date
        td_date, td_colors = tds[0:2]

        # Get the date for the row.
        date = td_date.contents[0]

        # Date must be valid ISO format.
        if not _is_valid_date(date):
            continue

        # Make room for this row.
        data[date] = {}

        # Find all colored labels.
        div_labels = td_colors.findAll("div")

        # Match the color to the label and
        # store the value for the specific date.
        for div_label in div_labels:
            color = _get_css_value(div_label["style"], "background")

            # If the color has a label, then store it.
            if color in color_to_label:
                label = color_to_label[color]
                with open('headers.txt', 'a+') as f:
                    f.write(label + "\n" + wiki_url + "\n")

                # Make sure to store an int.
                # Just in case we want to perform calculations.
                value = int(div_label["title"])

                # Store the value for the date and label.
                data[date][label] = value
    return data

def WikiParser(state_to_source, output):
    # Stores a list of all the tables, for each place.
    all_tables: List[pd.DataFrame] = []

    for wikidata_id, url in state_to_source.items():
        try:
            # Parse the Wikipedia Template time series page's table.
            data: Dict[str, int] = parse_time_series_chart(url)
        except ValueError:
            print("Skipping URL as it is invalid.")
            continue

        # If no data was found in the time series chart, continue.
        if not data:
            continue

        # Get the place name from the Wikipedia URL.
        place_name = get_place_name_from_url(url)

        # Store the current table to the all_tables.
        # Traspose the table, each column corresponds to a label.
        table = pd.DataFrame(data).T

        # Get the WikidataId of the place.
        table['wikidataId'] = wikidata_id

        all_tables.append(table)

    # If there is not a single table, throw an exeption.
    if not all_tables:
        raise Exception("No tables have been found!")

    # Create one big table from the list of tables.
    main_table = pd.concat(all_tables)

    # Rename the index column to "date".
    main_table.index.name = "date"

    # NOTE: This function is used to calculate total_cases and is passed
    # down to the Pandas.apply function.
    def all_cases(row: pd.Series):
        """
        @param row: a pd.Series
        Given a row with "cases" or "active_cases" and "recoveries".
        If "cases" exists, return the row itself.
        Otherwise, "cases" will be manually calculated
        to be "active_cases" + "recoveries".
        """

        if "cases" in row and row['cases'] > 0:
            return row

        # If we are not given the number of total cases, calculate it.
        deaths = row['deaths'] if 'deaths' in row else 0
        active_cases = row['active_cases'] if 'active_cases' in row else 0
        recoveries = row['recoveries'] if 'recoveries' in row else 0

        # Sum the values up to calculate the total cases for that given date.
        row["cases"] = deaths + active_cases + recoveries

        return row


    main_table = main_table.apply(all_cases, axis = 1)

    # Get rid of any unecessary columns.
    # We only care about the following columns.
    main_table = main_table[main_table.columns & \
        ['wikidataId', 'cases', 'active_cases', 'recoveries', 'deaths']]

    # If output is StringIO, return the CSV as a string.
    if isinstance(output, StringIO):
        csv = main_table.to_csv(index=True)
        output.write(csv)
    else:
        # Otherwise, it means it's a path. Export to path.
        main_table.to_csv(output, index=True)


if __name__ == "__main__":
    WikiParser(state_to_source=PLACES, output="output.csv")
