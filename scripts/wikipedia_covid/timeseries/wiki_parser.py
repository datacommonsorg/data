import datetime
from typing import Dict, List
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import Config


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
    Given a Wikipedia Template Time Series Chart URL,
    return the name of the place being observed.
    @param url: Wikipedia Template Time Series Chart URL
    """
    place_name = url.split('_medical_cases_chart')[-2]
    place_name = place_name.split('pandemic_data/')[-1]
    place_name = place_name.split('/')[-1]
    return place_name


def get_wiki_id(wiki_url: str) -> str:
    """
    Given any Wikipedia page, return the Wikidata Id
    for the place being observed.
    For Example:
    https://en.wikipedia.org/wiki/Spain will return "Q29".
    """
    html = urlopen(wiki_url)
    soup = BeautifulSoup(html, 'html.parser')
    li_wikidata = soup.find("li", {"id": "t-wikibase"})
    a_wikidata = li_wikidata.find('a')
    entity_page = a_wikidata['href'].split(':')[-1]
    wiki_id = entity_page.split('/')[-1]
    return wiki_id


def parse_time_series_chart(wiki_url: str) -> Dict[str, Dict[str, int]]:
    """
    Given a Wikipedia Template Time Series Table URL,
    return a dicionary of the data in the page.
    @param wiki_url: Wikipedia Template Time Series Table URL
    """
    # Query the HTML of the Wikipedia site.
    html = urlopen(wiki_url)
    soup = BeautifulSoup(html, 'html.parser')

    # Find the first table element in the site.
    table = soup.findAll("table")[0]

    # Get a map of color -> label
    # The table doesn't refer to items by label but rather by color.
    span_labels = table.findAll("span", {"style": "font-size:90%; margin:0px"})

    color_to_label = {}

    for span_label in span_labels:
        # There must be two contents inside the span.
        # conten1: color
        # contenn2: label
        if len(span_label.contents) != 2:
            continue

        # Get the color span.
        color_span, label_text = span_label.contents[0:2]

        # Clean up the label text.
        # To lower-case and strip string.
        label = label_text.lower().strip("\xa0")

        # Rename any labels by Config.replace_headers file.
        if label in Config.replace_headers:
            label = Config.replace_headers[label]

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

                # Make sure to store an int.
                # Just in case we want to perform calculations.
                value = int(div_label["title"])

                # Store the value for the date and label.
                data[date][label] = value
    return data


if __name__ == "__main__":
    # Stores a list of all the tables, for each Wiki place.
    all_tables: List[pd.DataFrame] = []

    f_in = open('./input.txt', 'r+')
    for url in f_in.readlines():
        # Parse the Wikipedia Page's table.
        data: Dict[str, int] = parse_time_series_chart(url)

        # If no data was found in the time series chart, continue.
        if not data:
            continue

        # Get the place name from the Wikipedia URL.
        place_name = get_place_name_from_url(url)

        # Store the current table to the all_tables.
        # Traspose the table, each column corresponds to a label.
        table = pd.DataFrame(data).T

        # Get the Wiki Data Id of the place.
        table['wikiId'] = get_wiki_id('https://en.wikipedia.org/wiki/' +
                                      place_name)
        
        all_tables.append(table)

    # Create one big table from the list of tables.
    main_table = pd.concat(all_tables)

    # Rename the index column to "date".
    main_table.index.name = "date"

    # Cases = Active Cases + Recoveries OR Confirmed Cases
    if "active_cases" in main_table and "recoveries" in main_table:
        main_table['cases'] = main_table['active_cases'] \
            + main_table['recoveries']

    # Get rid of any unecessary columns.
    main_table = main_table[main_table.columns & \
        ['wikiId', 'cases','active_cases', 'recoveries', 'deaths']]

    # Export table to CSV.
    main_table.to_csv('output.csv', mode="w+")
