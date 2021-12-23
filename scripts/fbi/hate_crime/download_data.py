import requests
import os
from bs4 import BeautifulSoup
import time
import json
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_integer('start_year',
                     2005,
                     'Start year(Min. 2005)',
                     lower_bound=2005)
flags.DEFINE_integer('end_year', 2020, 'End year(Min. 2005)', lower_bound=2005)
flags.DEFINE_boolean('force_fetch', True,
                     'forces api query and not return cached result')
flags.DEFINE_string('store_path', './source_data', 'Path to store the output')
flags.DEFINE_string('cache_path', './source_data/.cache_html/',
                    'Path to store the cached html files')
flags.DEFINE_string('base_url', 'https://ucr.fbi.gov/hate-crime',
                    'The base url containing list of URLs for each year')

# TODO respect original file extension
# TODO 2005 table 13, 14
# TODO 2004 tables
# TODO store http errors
# TODO handle list of multiple access urls found
# TODO log no access URL found

# Headers to make request
headers = {
    'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36'
}
"""
The file names of excel files changes across the years.
The URLs to access table appear in sequence of table number,
hence code uses enumerate to assign the table number.
years_with_no_table0 list help make this correction.
"""
years_with_no_table0 = ['2004', '2005', '2006', '2007']

# dictionary to access status across method calls
status_dict = {
    'year_list': [str(x) for x in range(2005, 2020)],
    'output_dir': './source_data',
    'cache_dir': './source_data/.cache_html/',
    'force_fetch': True,
    'base_url': 'https://ucr.fbi.gov/hate-crime',
    'session': None,
    'cur_year': '',
    'cur_year_url': '',
    'cur_access_url': '',
    'table_html_url_list': [],
    'download_urls': {}
}


def get_abs_url(base_url: str, cur_url: str) -> str:
    """Convert relative URL to absolute URL.
  """
    ret_url = cur_url
    if not cur_url.startswith('http'):
        if cur_url.startswith('/'):
            ret_url = requests.compat.urljoin(base_url, cur_url)
        else:
            ret_url = base_url + '/' + cur_url
    return ret_url


def request_html_soup(cur_session, url: str):
    """Get html text and bs4 object of the html from URL.
  """
    req = cur_session.get(url)
    if req.status_code == requests.codes.ok:
        resp_html = req.text
        resp_soup = BeautifulSoup(resp_html, features="html.parser")
    else:
        resp_html = None
        resp_soup = None

        print('HTTP status code: ' + str(req.status_code))
    return resp_html, resp_soup


def find_year_url(html_soup, year_str: str) -> str:
    """Find the URL for a given year from the base HTML list of URL for all years.
  """
    year_url = None
    base_a_list = html_soup.find(id='content-core').find_all('a')
    for cur_a in base_a_list:
        cur_year = cur_a.string
        if cur_year == year_str:
            print(cur_year)
            year_url = cur_a.get('href')
    return year_url


def find_access_tables_url() -> str:
    """Find the URL to 'Access Tables' in the given HTML for the year.
  
  The method uses status variables set in the status_dict for context.
  """
    global status_dict
    # fetch or return from cache
    if status_dict['force_fetch'] or not os.path.isfile(
            os.path.join(status_dict['cache_dir'],
                         f"{status_dict['cur_year']}.html")):
        year_html, year_soup = request_html_soup(status_dict['session'],
                                                 status_dict['cur_year_url'])
        with open(
                os.path.join(status_dict['cache_dir'],
                             f"{status_dict['cur_year']}.html"), 'w') as fp:
            fp.write(year_html)
    else:
        with open(
                os.path.join(status_dict['cache_dir'],
                             f"{status_dict['cur_year']}.html"), 'r') as fp:
            year_html = fp.read()
            year_soup = BeautifulSoup(year_html, features="html.parser")

    # some year pages contain and iframe which has the actual html content, 1st iframe is used if multiple are found
    year_iframe_list = year_soup.find_all('iframe')
    if len(year_iframe_list) > 0:
        status_dict['cur_year_url'] = year_iframe_list[0]['src']
        print('iframe', status_dict['cur_year_url'])
        year_html, year_soup = request_html_soup(status_dict['session'],
                                                 status_dict['cur_year_url'])
        with open(
                os.path.join(status_dict['cache_dir'],
                             f"{status_dict['cur_year']}.html"), 'w') as fp:
            fp.write(year_html)
    # convert for use of base URL in the next step
    status_dict['cur_year_url'] = status_dict[
        'cur_year_url'][:status_dict['cur_year_url'].rfind('/')]
    year_subitem_list = year_soup.find_all('div', class_='subitem')
    access_tables_found = False
    access_url = None
    if len(year_subitem_list) > 0:
        for year_subitem in year_subitem_list:
            if not access_tables_found:
                all_a = year_subitem.find_all('a')
                for cur2_a in all_a:
                    access_url = cur2_a.get('href')
                    if not access_tables_found:
                        if cur2_a.string and 'access' in cur2_a.string.lower():
                            access_tables_found = True
                            access_url = get_abs_url(
                                status_dict['cur_year_url'], access_url)
                        else:
                            all_b = cur2_a.find_all('b')
                            for cur_b in all_b:
                                if not access_tables_found:
                                    if 'access' in cur_b.string.lower():
                                        access_tables_found = True
                                        access_url = get_abs_url(
                                            status_dict['cur_year_url'],
                                            access_url)
    status_dict['cur_access_url'] = access_url
    return access_url


def find_table_html_url():
    """Find the URL list of HTML version of all the tables.
  
  The method uses status variables set in the status_dict for context.
  """
    global status_dict
    # fetch or return from cache
    if status_dict['force_fetch'] or not os.path.isfile(
            os.path.join(status_dict['cache_dir'],
                         f"{status_dict['cur_year']}_access.html")):
        access_html, access_soup = request_html_soup(
            status_dict['session'], status_dict['cur_access_url'])
        with open(
                os.path.join(status_dict['cache_dir'],
                             f"{status_dict['cur_year']}_access.html"),
                'w') as fp:
            fp.write(access_html)
    else:
        with open(
                os.path.join(status_dict['cache_dir'],
                             f"{status_dict['cur_year']}_access.html"),
                'r') as fp:
            access_html = fp.read()
            access_soup = BeautifulSoup(access_html, features="html.parser")
    # convert for use of base URL in the next step
    status_dict['cur_access_url'] = status_dict[
        'cur_access_url'][:status_dict['cur_access_url'].rfind('/')]

    tables_div_all = access_soup.find(id='col_b')
    if not tables_div_all:
        tables_div_all = access_soup.find(id='col_2')
    tables_a_all = tables_div_all.find_all('a')
    if status_dict['cur_year'] in years_with_no_table0:
        status_dict['table_html_url_list'] = ['']
    else:
        status_dict['table_html_url_list'] = []
    for i, cur_table_a in enumerate(tables_a_all):
        table_html_url = cur_table_a.get('href')
        table_html_url = get_abs_url(status_dict['cur_access_url'],
                                     table_html_url)
        status_dict['table_html_url_list'].append(table_html_url)
    return status_dict['table_html_url_list']


def find_table_xls_url():
    global status_dict
    for table_i, table_html_url in enumerate(
            status_dict['table_html_url_list']):
        if table_html_url:
            print(table_html_url)
            if status_dict['force_fetch'] or not os.path.isfile(
                    os.path.join(
                        status_dict['cache_dir'],
                        f"{status_dict['cur_year']}_table_{table_i}.html")):
                table_html, table_soup = request_html_soup(
                    status_dict['session'], table_html_url)
                with open(
                        os.path.join(
                            status_dict['cache_dir'],
                            f"{status_dict['cur_year']}_table_{table_i}.html"),
                        'w') as fp:
                    fp.write(table_html)
            else:
                with open(
                        os.path.join(
                            status_dict['cache_dir'],
                            f"{status_dict['cur_year']}_table_{table_i}.html"),
                        'r') as fp:
                    table_html = fp.read()
                    table_soup = BeautifulSoup(table_html,
                                               features="html.parser")

            table_html_url = table_html_url[:table_html_url.rfind('/')]

            table_html_a_all = table_soup.find_all('a')
            for cur_table_html_a in table_html_a_all:
                if cur_table_html_a.string and 'excel' in cur_table_html_a.string.lower(
                ):
                    table_xls_url = cur_table_html_a.get('href')
                    table_xls_url = get_abs_url(table_html_url, table_xls_url)

                    print(table_xls_url)
                    # store list of urls
                    status_dict['download_urls'][
                        status_dict['cur_year']].append(table_xls_url)
                    with open(
                            os.path.join(status_dict['output_dir'],
                                         'url_list.json'), 'w') as fp:
                        json.dump(status_dict['download_urls'], fp, indent=2)
                    # fetch and store urls
                    r = requests.get(table_xls_url)
                    output_path = os.path.join(status_dict['output_dir'],
                                               f"{status_dict['cur_year']}")
                    with open(os.path.join(output_path, f'table_{table_i}.xls'),
                              'wb') as fp:
                        fp.write(r.content)

            time.sleep(0.5)


def scrape_yearwise():
    global status_dict

    session = requests.Session()
    session.headers.update(headers)

    status_dict['session'] = session

    status_dict['output_dir'] = os.path.expanduser(status_dict['output_dir'])
    if not os.path.exists(status_dict['output_dir']):
        os.makedirs(status_dict['output_dir'], exist_ok=True)

    status_dict['cache_dir'] = os.path.expanduser(status_dict['cache_dir'])
    if not os.path.exists(status_dict['cache_dir']):
        os.makedirs(status_dict['cache_dir'], exist_ok=True)
    if status_dict['force_fetch'] or not os.path.isfile(
            os.path.join(status_dict['cache_dir'], 'base.html')):
        base_html, base_soup = request_html_soup(session,
                                                 status_dict['base_url'])
        with open(os.path.join(status_dict['cache_dir'], 'base.html'),
                  'w') as fp:
            fp.write(base_html)
    else:
        with open(os.path.join(status_dict['cache_dir'], 'base.html'),
                  'r') as fp:
            base_html = fp.read()
            base_soup = BeautifulSoup(base_html, features="html.parser")

    for cur_year in status_dict['year_list']:
        status_dict['cur_year'] = cur_year
        year_url = find_year_url(base_soup, cur_year)
        if year_url:
            print(year_url)
            status_dict['cur_year_url'] = year_url
            output_path = os.path.join(status_dict['output_dir'], f"{cur_year}")
            if not os.path.exists(output_path):
                os.makedirs(output_path, exist_ok=True)
            status_dict['download_urls'][cur_year] = []

            access_url = find_access_tables_url()

            if access_url:
                print(access_url)
                find_table_html_url()
                find_table_xls_url()
            else:
                print('No access tables url')

            time.sleep(2)


def main(argv):
    global status_dict
    status_dict['year_list'] = [
        str(x) for x in range(FLAGS.start_year, FLAGS.end_year)
    ]
    status_dict['force_fetch'] = FLAGS.force_fetch
    status_dict['output_dir'] = FLAGS.store_path
    status_dict['cache_dir'] = FLAGS.cache_path
    status_dict['base_url'] = FLAGS.base_url

    scrape_yearwise()


if __name__ == '__main__':
    app.run(main)
