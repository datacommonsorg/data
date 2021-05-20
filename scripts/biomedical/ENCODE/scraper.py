""" Downloads all files from a given search result json from the Encode project

Not meant to be run from g3 as it requires Python3 support as well as the
following external libraries.
- requests
"""

from multiprocessing import Pool

import argparse
import requests
import shutil
import json
import gzip
import os
import io

# URL Patterns
ROOT_URL = 'https://www.encodeproject.org{path}'
JSON_URL = 'https://www.encodeproject.org{path}?format=json&limit=all'

# Encode project id patterns
EXPERIMENT_PATTERN = '/experiments/{name}/'
FILE_PATTERN = '/files/{name}/'

# Json-ld key constants
GRAPH_KEY = '@graph'
ID_KEY = '@id'
CONTEXT_KEY = '@context'
STATUS_KEY = 'status'
DOWNLOAD_URL_KEY = 'href'
FILE_KEY = 'files'
FILE_TYPE_KEY = 'file_type'
ACCESSION_KEY = 'accession'
NAME_KEY = 'name'

# File extensions
GZIP_EXTENSION = '.gz'

# Allowed file formats
ALLOWED_FILE_TYPES = [
    'bed', 'bed narrowPeak', 'bed broadPeak', 'bed idr_peak', 'bed bed3',
    'bed bed3+', 'bed bed6+', 'bed bed9', 'bed bed12', 'bed bedMethyl'
]

# Fail file path
FAIL_FILE = 'failures.txt'

# Location of where the Encode ontology is defined
TERMS_URL = 'https://www.encodeproject.org/terms/?format=json'

# Maximum number of subprocesses
MAX_CPU = 8


def download_file(url, dest_path):
  """ Downloads the file at the given url and stores it at the given file

    path.
    """
  req = requests.get(url)
  if req.status_code == 200:
    with open(dest_path, 'wb') as f:
      f.write(req.content)
    return
  print('> WARNING: Failed to fetch {}'.format(url))
  with open(FAIL_FILE, 'a') as f:
    print('{}, {}'.format(url, dest_path), file=f)


def download_json(url, dest_path):
  """ Downloads the json file at the given url and stores it at the given

    file path.
    """
  req = requests.get(url)
  if req.status_code == 200:
    payload = replace_context(req.json())
    with open(dest_path, 'w') as f:
      json.dump(payload, f)
    return payload
  print('> WARNING: Failed to fetch {}'.format(url))
  with open(FAIL_FILE, 'a') as f:
    print('{}, {}'.format(url, dest_path), file=f)
  return None


def download_gzip(url, dest_path):
  """ Downloads the gzip file, decompresses it, and stores it at the given

    file path.
    """
  req = requests.get(url)
  if req.status_code == 200:
    with open(dest_path, 'wb') as f:
      in_ = io.BytesIO()
      in_.write(req.content)
      in_.seek(0)
      zip_file = gzip.GzipFile(fileobj=in_, mode='rb')
      shutil.copyfileobj(zip_file, f)
    return
  print('> WARNING: Failed to fetch {}'.format(url))
  with open(FAIL_FILE, 'a') as f:
    print('{}, {}, {}'.format(url, dest_path, 'COMPRESSED'), file=f)


def replace_context(encode_json):
  """ Replaces the context field with the correct vocabulary url. """
  if CONTEXT_KEY in encode_json:
    encode_json[CONTEXT_KEY] = TERMS_URL
  return encode_json


def mkdirs_if_dne(path):
  """ Creates the directory at path if it does not exist. """
  if not os.path.isdir(path):
    os.makedirs(path)


def get_experiment_id(experiment):
  """ Returns the experiment id of the given experiment. """
  return experiment[ACCESSION_KEY]


def get_experiment_files(experiment):
  """ Returns all file jsons in an experiment json. """
  return experiment[FILE_KEY]


def get_encode_file_id(encode_file):
  """ Returns the id of the encode file. """
  return encode_file[ACCESSION_KEY]


def get_file_type(encode_file):
  """ Returns the file type of the given encode file. """
  return encode_file[FILE_TYPE_KEY]


def get_data_file_name(encode_file_download):
  """ Returns the file name and if it is a gzip file for the given file

    pointed at by the download url.
    """
  file_name = encode_file_download.split('/')[-1]
  if file_name.endswith(GZIP_EXTENSION):
    return file_name.split(GZIP_EXTENSION)[0], True
  return file_name, False


def delete_disabled_entity(dest_root):
  """ Deletes any JSON files in the given dest_root that has status set to

    disabled in its contents.
    """
  json_files = [name for name in os.listdir(dest_root) if '.json' in name]
  for json_file in json_files:
    json_path = os.path.join(dest_root, json_file)
    with open(json_path, 'r') as f:
      json_contents = json.load(f)

    if STATUS_KEY in json_contents and (
        json_contents[STATUS_KEY] == 'disabled' or
        json_contents[STATUS_KEY] == 'archived'):
      print('> Removing disabled file {}'.format(json_path))
      os.remove(json_path)


# ------------------------------ SCRAPE FUNCTION ------------------------------


def scrape_auxiliary_files(aux_map, dest_root):
  """ Downloads all auxiliary files. """
  mkdirs_if_dne(dest_root)

  print('-' * 80)
  print('Downloading all auxiliary files...')
  for path in aux_map:
    formatted_name = path.replace('-', '_').replace('/', '')
    dest_filename = '{}.json'.format(formatted_name)
    dest_path = os.path.join(dest_root, dest_filename)
    url = JSON_URL.format(path=path)
    print('> Downloading file: {} -> {}'.format(path, dest_path))
    aux_json = download_json(url, dest_path)

    # Call an additional scrape function if specified
    if aux_map[path] is not None:
      aux_root = os.path.join(dest_root, formatted_name)
      aux_map[path](aux_json, aux_root)

  print('Done scraping auxiliary files!\n')


def scrape_users(users, dest_root):
  """ Downloads all user JSONs and stores it in the directory given by

    dest_root.
    """
  mkdirs_if_dne(dest_root)

  print('> Downloading all user JSONs...')
  for user in users[GRAPH_KEY]:
    encode_user_path = user[ID_KEY]
    user_url = JSON_URL.format(path=encode_user_path)
    user_file_name = '{}.json'.format(encode_user_path.split('/')[-2])
    user_path = os.path.join(dest_root, user_file_name)
    download_json(user_url, user_path)
    print('\r> Finished scraping {}'.format(encode_user_path))

  delete_disabled_entity(dest_root)
  print('\n> Finished scraping all user JSONs!\n')


def scrape_awards(awards, dest_root):
  """ Downloads all awards JSONs and stores it in the directory given by

    dest_root.
    """
  mkdirs_if_dne(dest_root)

  print('> Downloading all award JSONs...')
  for award in awards[GRAPH_KEY]:
    encode_award_path = award[ID_KEY]
    award_url = JSON_URL.format(path=encode_award_path)
    award_file_name = '{}.json'.format(award[NAME_KEY])
    award_path = os.path.join(dest_root, award_file_name)
    download_json(award_url, award_path)
    print('\r> Finished scraping {}'.format(encode_award_path))

  delete_disabled_entity(dest_root)
  print('\n> Finished scraping all award JSONs!\n')


def scrape_labs(labs, dest_root):
  """ Downloads all labs JSONs and stores it in the directory given by

    dest_root.
    """
  mkdirs_if_dne(dest_root)

  print('> Downloading all lab JSONs...')
  for lab in labs[GRAPH_KEY]:
    encode_lab_path = lab[ID_KEY]
    lab_url = JSON_URL.format(path=encode_lab_path)
    lab_file_name = '{}.json'.format(lab[NAME_KEY])
    lab_path = os.path.join(dest_root, lab_file_name)
    download_json(lab_url, lab_path)
    print('\r> Finished scraping {}'.format(encode_lab_path))

  delete_disabled_entity(dest_root)
  print('\n> Finished scraping all lab JSONs!\n')


def scrape_biosamples(biosamples, dest_root):
  """ Downloads all biosamples JSONs and stores it in the directory given by

    dest_root.
    """
  mkdirs_if_dne(dest_root)

  print('> Downloading all biosample JSONs...')
  for biosample in biosamples[GRAPH_KEY]:
    encode_biosample_path = biosample[ID_KEY]
    biosample_url = JSON_URL.format(path=encode_biosample_path)
    biosample_file_name = '{}.json'.format(biosample[ACCESSION_KEY])
    biosample_path = os.path.join(dest_root, biosample_file_name)
    download_json(biosample_url, biosample_path)
    print('\r> Finished scraping {}'.format(encode_biosample_path))

  delete_disabled_entity(dest_root)
  print('\n> Finished scraping all biosample JSONs!\n')


def scrape_biosample_types(biosample_types, dest_root):
  """ Downloads all biosample types JSONs and stores it in the directory given

    by dest_root.
    """
  mkdirs_if_dne(dest_root)

  print('> Downloading all biosample type JSONs...')
  for biosample_type in biosample_types[GRAPH_KEY]:
    encode_biosample_type_path = biosample_type[ID_KEY]
    biosample_type_url = JSON_URL.format(path=encode_biosample_type_path)
    biosample_type_file_name = '{}.json'.format(
        encode_biosample_type_path.split('/')[-2])
    biosample_type_path = os.path.join(dest_root, biosample_type_file_name)
    download_json(biosample_type_url, biosample_type_path)
    print('\r> Finished scraping {}'.format(encode_biosample_type_path))

  delete_disabled_entity(dest_root)
  print('\n> Finished scraping all biosample type JSONs!\n')


def scrape_libraries(libraries, dest_root):
  """ Downloads all libraries JSONs and stores it in the directory given by

    dest_root.
    """
  mkdirs_if_dne(dest_root)

  print('> Downloading all library JSONs...')
  for library in libraries[GRAPH_KEY]:
    encode_library_path = library[ID_KEY]
    library_url = JSON_URL.format(path=encode_library_path)
    library_file_name = '{}.json'.format(library[ACCESSION_KEY])
    library_path = os.path.join(dest_root, library_file_name)
    download_json(library_url, library_path)
    print('\r> Finished scraping {}'.format(encode_library_path))

  delete_disabled_entity(dest_root)
  print('\n> Finished scraping all library JSONs!\n')


# --------------------------- SCRAPE SEARCH RESULTS ---------------------------


def scrape_search_result(search_path, dest_root, num_processes=-1):
  """ Gets all the search results contained in the json stored at the given

    search_path and stores the result into dest_root.
    """
  mkdirs_if_dne(dest_root)

  print('-' * 80)
  print('Scraping search results at {}'.format(search_path))
  with open(search_path, 'r') as f:
    search_results = json.load(f)

  # If parallel is specified, scrape each experiment in the search result in
  # parallel. Otherwise iterate through all experiments.
  print('> Now scraping {} experiments.'.format(len(search_results[GRAPH_KEY])))
  if num_processes > 1:
    args = []
    for idx, experiment in enumerate(search_results[GRAPH_KEY]):
      exp_id = get_experiment_id(experiment)
      exp_dest_root = os.path.join(dest_root, exp_id)
      args.append((idx, exp_id, exp_dest_root))

    # Create a multiprocessing pool and execute the scraper in parallel
    pool = Pool(num_processes)
    pool.starmap(scrape_experiment, args)
  else:
    for idx, experiment in enumerate(search_results[GRAPH_KEY]):
      exp_id = get_experiment_id(experiment)
      exp_dest_root = os.path.join(dest_root, exp_id)
      scrape_experiment(idx, exp_id, exp_dest_root)
  print('\n> Done!')


def scrape_experiment(scrape_num, exp_id, dest_root):
  """ Scrapes the given experiment and stores the information in the

    directory given by dest_root.
    """
  mkdirs_if_dne(dest_root)

  # Scrape the summary
  encode_exp_path = EXPERIMENT_PATTERN.format(name=exp_id)
  summary_url = JSON_URL.format(path=encode_exp_path)
  summary_file_name = '{}.json'.format(exp_id)
  summary_path = os.path.join(dest_root, summary_file_name)
  exp_json = download_json(summary_url, summary_path)

  # Iterate through all files and call scrape file
  allowed_files = filter(
      lambda encode_file: get_file_type(encode_file) in ALLOWED_FILE_TYPES,
      get_experiment_files(exp_json),
  )
  for encode_file in allowed_files:
    encode_file_id = get_encode_file_id(encode_file)
    encode_file_root = os.path.join(dest_root, encode_file_id)
    scrape_encode_file(encode_file_id, encode_file_root)

  print('\r> Done scraping experiment {}\t'.format(scrape_num), end='')


def scrape_encode_file(encode_file_id, dest_root):
  """ Scrapes the given encode file summary and raw data and stores the

    information in the directory given by dest_root.
    """
  mkdirs_if_dne(dest_root)

  # Scrape the summary
  encode_file_path = FILE_PATTERN.format(name=encode_file_id)
  summary_url = JSON_URL.format(path=encode_file_path)
  summary_file_name = '{}.json'.format(encode_file_id)
  summary_path = os.path.join(dest_root, summary_file_name)
  encode_file_json = download_json(summary_url, summary_path)

  # Scrape the raw data file
  download_path = encode_file_json[DOWNLOAD_URL_KEY]
  data_file_url = ROOT_URL.format(path=download_path)
  data_file_name, compressed = get_data_file_name(download_path)
  data_file_path = os.path.join(dest_root, data_file_name)

  # Download and decompress if the file is compressed, else download the
  # file as normal
  if compressed:
    download_gzip(data_file_url, data_file_path)
  else:
    download_file(data_file_url, data_file_path)


# ------------------------------- FIX FUNCTION --------------------------------


def fix_context(dest_root, num_processes=8):
  """ Reassigns the context for each JSON stored in the dest_root. """
  targets = []

  # Collect all files to fix
  for root, subdirs, files in os.walk(dest_root):
    json_files = [f for f in files if '.json' in f]
    for json_file in json_files:
      # Construct the path and append
      json_path = os.path.join(root, json_file)
      targets.append(json_path)

  # Run the fix in parallel
  pool = Pool(num_processes)
  pool.starmap(fix_context_json, targets)


def fix_context_json(path):
  """ Reassigns the context for the JSON at the given path. """
  with open(path, 'r') as f:
    json_contents = json.load(f)

  # Change the context if required and write the changes
  json_contents = replace_context(json_contents)
  with open(path, 'w') as f:
    json.dump(json_contents, f)

  print('\r> Finished fixing: {}'.format(path))


# ------------------------------- MAIN FUNCTION -------------------------------

INPUT_PATH = 'input/batch_2/search_results.json'
OUTPUT_ROOT = 'output/data'

# Auxiliary file paths
AUXILIARY_FILE_MAP = {
    '/terms/': None,
    '/users/': scrape_users,
    '/labs/': scrape_labs,
    '/awards/': scrape_awards,
    '/biosamples/': scrape_biosamples,
    '/biosample-types/': scrape_biosample_types,
    '/libraries/': scrape_libraries,
}

# Create the argument parser.
parser = argparse.ArgumentParser(description='Scrape the Encode Project.')
parser.add_argument(
    '--input_path',
    type=str,
    help='Path of the search results JSON file.',
    default=INPUT_PATH)
parser.add_argument(
    '--output_root',
    type=str,
    help='The root folder of where to save all scraped files.',
    default=OUTPUT_ROOT)
parser.add_argument(
    '--fix',
    action='store_true',
    help='Set this flag if the files are downloaded in the output_root but the context needs to be fixed.'
)

if __name__ == '__main__':
  args = parser.parse_args()
  if args.fix:
    fix_context(args.output_root)
  else:
    scrape_auxiliary_files(AUXILIARY_FILE_MAP, args.output_root)
    scrape_search_result(
        args.input_path, args.output_root, num_processes=MAX_CPU)
    
