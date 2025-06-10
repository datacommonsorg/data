# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities to sanity schema nodes.

It checks schema for:
  - spell errors in name, description and CamelCase dcids.
  - URLs to be active
The errors are reported in counters as well as an output file.

To check a list of MCF files, run the command:
  python schema_checker.py --schema_input_mcf=<input-mcf-file> \
      --schema_error_output=<output-file-with-errors-per-node>
"""

import os
import re
import requests
import sys

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))),
                 'util'))

# TODO: check if ',' needs to be allowed.
_URL_PATTERN = r'(?P<url>\bhttps?://[^ "\',]*)'
_URL_SEPERATORS = '/?&#,'

flags.DEFINE_string('schema_input_mcf', '',
                    'MCF file with nodes to generate schema for.')
flags.DEFINE_string('url_allowlist',
                    os.path.join(_SCRIPT_DIR, 'urls_allowlist.csv'),
                    'File with list of URLs allowed')
flags.DEFINE_string('schema_check_output', '', 'File with list of spell errors')
flags.DEFINE_string('url_regex', _URL_PATTERN, 'File with list of spell errors')
flags.DEFINE_string('schema_check_config', '', 'File with config parameters.')

_FLAGS = flags.FLAGS

import file_util
import process_http_server

from config_map import ConfigMap
from counters import Counters
from config_map import ConfigMap
from mcf_file_util import load_mcf_nodes, write_mcf_nodes, update_mcf_nodes
from mcf_file_util import add_namespace, strip_namespace, add_mcf_node
from schema_spell_checker import get_spell_checker, spell_check_nodes, get_default_spell_config

import config_flags


# Check the URL
# Copied from https://github.com/datacommonsorg/schema/blob/main/test/url_checker.py
def get_url_status(url: str, timeout: int = 30) -> (str, str):
    """Gets the status for url.

  Args:
    url: URL to download.
    timeout: timeout in seconds.

  Returns:
    a tuple of (status, message)
      status: Status code and reason.
      message: Optional message providing additional details about response.
      Example:
        ('200 OK', ''),
        ('403 Forbidden', 'Access denied'),
        ('301 Moved Permanently','Redirected to https://abc.com')
  """
    try:
        resp = requests.get(url, timeout=timeout)

        # Check for redirects
        if resp.history:
            initial_resp = resp.history[0]
            return (
                str(initial_resp.status_code) + " " + initial_resp.reason
                if initial_resp.reason else str(initial_resp.status_code),
                'Redirected to ' + resp.url,
            )

        # Return the response code with reason
        status = str(resp.status_code)
        if resp.reason:
            status += ' ' + resp.reason
        return (status, '')

    except Exception as e:
        return "ERROR", str(e)


def get_url_regex(config: ConfigMap = None) -> re.Pattern:
    """Returns the compiled regex pattern for URLs."""
    if config:
        url_pattern = config.get('url_regex', _URL_PATTERN)
        if url_pattern:
            return re.compile(url_pattern)
    return re.compile(_URL_PATTERN)


def get_urls_in_string(value: str, url_regex: re.Pattern = None) -> list[str]:
    """Returns a list of URLs in the value string.

    Args:
      value: string from which URLs are extracted using regex
      url_regex: regex pattern for URLs
        if None, the default URL regex is used.

    Returns:
      list of URLs found in the value.
    """
    urls = []
    if url_regex == None:
        url_regex = get_url_regex()
    for matches in url_regex.finditer(str(value).strip()):
        url = matches.groupdict().get('url')
        if url:
            urls.append(url)
    return urls


def get_node_urls(node: dict[str, str],
                  url_regex: re.Pattern = None) -> dict[str, str]:
    """Returns a dictionary keyed by URLs with value as the property.

    Args:
      node: dictionary of property:value
      url_regex: regex to extract URLs from value

    Returns:
      dictionary keyed by URLs in the node with property as value.
    """
    node_urls = {}
    if url_regex == None:
        url_regex = get_url_regex()
    for prop, value in node.items():
        if prop and prop.startswith('#'):
            # Ignore comments
            continue
        urls = get_urls_in_string(prop, url_regex)
        urls.extend(get_urls_in_string(value, url_regex))
        for url in urls:
            url_props = node_urls.get(url, '') + ',' + url
            node_urls[url] = url_props.strip(',')
    return node_urls


def load_url_allowlist(url_file: str, url_regex: re.Pattern = None) -> set[str]:
    """Load list of URLs allowed.

    Args:
      url_file: CSV file with urls to be allowed without download attempt.
      url_regex: regular expression to parse URL in the CSv file.

    Returns:
      set of urls as strings.
    """
    urls = set()
    if not url_regex:
        url_regex = get_url_regex()
    url_props = get_node_urls(file_util.file_load_csv_dict(url_file), url_regex)
    urls = set(url_props.keys())
    logging.info(f'Loaded {len(urls)} urls from {url_file}')
    return urls


def is_url_allowed(url: str, urls_allowlist: set[str]) -> bool:
    """Returns True if URL is in the allowlist

    Args:
      url: URL to be checked.
        Also check all the URL prefixes broken seperators like '/#&'
      urls_allowlist: set of URLs allowed.
    """
    if url in urls_allowlist:
        # URL directly present in allowlist.
        return True

    # Check if URL prefix is in allowlist.
    url_prefix = url
    while url_prefix:
        # Get the url prefix
        pos = -1
        for c in _URL_SEPERATORS:
            pos = url_prefix.rfind(c)
            if pos > 0:
                break
        if pos > 0 and pos < len(url_prefix):
            url_prefix = url_prefix[:pos]
            if url_prefix in urls_allowlist:
                return True
        else:
            break
    return False


def check_mcf_urls(nodes: dict[str, dict],
                   urls_allowed: set[str] = None,
                   config: ConfigMap = None,
                   counters: Counters = None,
                   url_status_cache: dict = {}) -> list[dict]:
    """Returns the URLs that don't load for each MCF node.

    Args:
      nodes: dictionary of node with property: values per node.
      config: configMap with configuration parameters.
      counters: counters to be updated.
      url_status_cache: Caches status of URLs.
    """
    if not config:
        config = ConfigMap()
    if counters is None:
        counters = Counters(prefix='url_checker')
    if url_status_cache is None:
        url_status_cache = dict()
    url_errors = []
    url_regex = get_url_regex(config)
    if urls_allowed is None:
        urls_allowed = load_url_allowlist(config.get('url_allowlist', ''),
                                          url_regex)
        counters.add_counter('urls-allowlist', len(urls_allowed))

    counters.add_counter('total', len(nodes))
    logging.level_debug() and logging.debug(f'Checking URLs in {len(nodes)}')
    # Extract any URL in each property:value across all nodes.
    # Check if the URL can be downloaded.
    for dcid, node in nodes.items():
        counters.add_counter('processed', 1)
        url_props = get_node_urls(node, url_regex)
        for url, props in url_props.items():
            if is_url_allowed(url, urls_allowed):
                counters.add_counter('url-allowed', 1)
                continue
            cached_url = url_status_cache.get(url)
            if cached_url:
                url_status = cached_url.get('status', '')
                msg = cached_url.get('message', '')
                counters.add_counter(f'url-cache-hits-{url_status}', 1)
            else:
                counters.add_counter(f'url-lookups', 1)
                url_status, msg = get_url_status(url)
                url_status_cache[url] = {'status': url_status, 'message': msg}
                counters.add_counter(f'url-status-{url_status}', 1)
            if url_status.startswith('200'):
                logging.level_debug() and logging.debug(
                    f'URL: {url} in {dcid} {url_status}')
            else:
                # URL had an error. Log it
                logging.error(
                    f'URL Error: {url}, dcid: {dcid}, props: {props}, status: {url_status}, msg: {msg}'
                )
                err_node = dict()
                err_node.update({
                    'dcid': dcid,
                    'property': props,
                    'url': url,
                    'url_status': url_status,
                    'url_error_message': msg,
                })
                url_errors.append(err_node)
                counters.add_counter('error-url-status', 1)
    return url_errors


def _get_nodes_from_file(filename: str, nodes: dict = None) -> dict:
    """Returns nodes from file."""
    if nodes is None:
        nodes = {}
    for file in file_util.file_get_matching(filename):
        if '.mcf' in file or '.csv' in file:
            load_mcf_nodes(file, nodes)
        else:
            # Load each line as node.
            with file_util.FileIO(file) as input_file:
                for line in input_file:
                    line = line.strip()
                    if ':' in line:
                        prop, value = line.split(':', 1)
                    else:
                        prop = line
                        value = ''
                    nodes[len(nodes)] = {prop: value}
    return nodes


def sanity_check_nodes(
    nodes: dict,
    context: dict = None,
    mcf_spell_checker=None,
    urls_allowed: set = None,
    config: ConfigMap = None,
    counters: Counters = None,
    url_cache: dict = None,
) -> dict:
    """Sanity check schema nodes for spell and URLs errors.

    Args:
      nodes: dictionary of schema node as dictionary of property:values
      context: context property:values to be added for each error, such as filename
      config: configuration for sanity checks.
      counters: Counters to be updated

    Returns:
      dictionary of nodes with errors:
        <file>: { 'dcid': <dcid>, 'property': <prop>, 'error': <error message> }
    """
    if not config:
        config = ConfigMap()
    if counters is None:
        counters = Counters()

    if mcf_spell_checker is None:
        mcf_spell_checker = get_spell_checker(config, counters)
    if urls_allowed is None:
        urls_allowed = load_url_allowlist(config.get('url_allowlist', ''))
        counters.add_counter('urls-allowlist', len(urls_allowed))

    # Sanity each node in all MCF files.
    if url_cache is None:
        url_cache = {}
    if context is None:
        context = {}

    # Spell check all nodes
    errors = {}
    spell_errors = []
    if config.get('spell_check', True):
        spell_errors = spell_check_nodes(nodes, config, counters,
                                         mcf_spell_checker)
        context['check'] = 'SPELL'
        _add_list_to_dict(spell_errors, context, errors)

    # Check URLs from all nodes in the file
    url_errors = []
    if config.get('check_url', True):
        url_errors = check_mcf_urls(nodes, urls_allowed, config, counters,
                                    url_cache)
        context['check'] = 'URL'
        _add_list_to_dict(url_errors, context, errors)

    logging.info(
        f'Sanity checked: nodes: {len(nodes)}, spell errors: {len(spell_errors)}, URL errors: {len(url_errors)}'
    )
    return errors


def sanity_check_mcf(input_mcf: str,
                     config: ConfigMap = None,
                     counters: Counters = None) -> dict:
    """Sanity check schema nodes in mcf files.

    Args:
      input_mcf: Files with MCF nodes to be checked.
      config: configuration parameters for schema checks
      counters: Counters to be updated

    Returns:
      dictionary of nodes with errors for specific properties-values.
    """
    if not config:
        config = ConfigMap()
    if counters is None:
        counters = Counters()

    logging.info(
        f'Schema sanity check: {input_mcf} with config: {config.get_configs()}')

    mcf_spell_checker = get_spell_checker(config, counters)
    urls_allowed = load_url_allowlist(config.get('url_allowlist', ''))
    counters.add_counter('urls-allowlist', len(urls_allowed))

    # Sanity each node in all MCF files.
    errors = {}
    url_cache = {}
    input_files = file_util.file_get_matching(input_mcf)
    for mcf_file in input_files:
        nodes = _get_nodes_from_file(mcf_file)
        counters.add_counter(f'sanity-input-mcf-file', 1, mcf_file)
        logging.info(
            f'Loaded {len(nodes)} nodes from file for sanity check: {mcf_file}')
        context = {'file': mcf_file}
        file_errors = sanity_check_nodes(nodes, context, mcf_spell_checker,
                                         urls_allowed, config, counters,
                                         url_cache)

        logging.info(
            f'Sanity check: {mcf_file}, nodes: {len(nodes)}, errors: {len(file_errors)}'
        )
        for err in file_errors.values():
            errors[len(errors)] = err

    # Save errors into output file.
    output_file = config.get('schema_check_output', '')
    if errors and output_file:
        # Save MCF errors into the output
        output_file = file_util.file_get_name(output_file, file_ext='')
        logging.info(
            f'Writing {len(errors)} sanity check error into: {output_file}')
        file_util.file_write_py_dict(errors, output_file)

    # Get error counters
    error_counts = {
        c: v for c, v in counters.get_counters().items() if 'error' in c
    }
    logging.info(f'Sanity check error counts: {error_counts}')

    return errors


def get_default_schema_check_config() -> dict:
    """Returns config parameters for schema checker."""
    config = {}
    config.update(get_default_spell_config())
    config.update({
        'url_allowlist': _FLAGS.url_allowlist,
        'schema_check_output': _FLAGS.schema_check_output,
        'url_regex': _FLAGS.url_regex,
    })
    return config


def _add_list_to_dict(items: list[dict], context: dict, output: dict) -> dict:
    """Add a set of items into output dictionary with key as index."""
    if isinstance(items, dict):
        # Flatten dict of errors pvs into a list of errors.
        items_list = []
        for dcid, pvs in items.items():
            for prop, error in pvs.items():
                entry = {'dcid': dcid, 'property': prop, 'error': error}
                items_list.append(entry)
        items = items_list
    for item in items:
        if item:
            entry = dict(context)
            entry.update(item)
            output[len(output)] = entry
    return output


def main(_):
    # Launch a web server with a form for commandline args
    # if the command line flag --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    counters = Counters()
    config = ConfigMap()
    config.add_configs(
        config_flags.init_config_from_flags(
            _FLAGS.schema_check_config).get_configs())
    config.add_configs(get_default_schema_check_config())
    sanity_check_mcf(_FLAGS.schema_input_mcf, config, counters)


if __name__ == '__main__':
    app.run(main)
